from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import require_schema
from .fixtures import (
    FIXTURE_FORM,
    FIXTURE_FPS,
    FIXTURE_JOINT_SET,
    FIXTURE_ROUTINE,
    TEACHING_JOINTS,
    build_smplx_fixture_frames,
)

MOTION_RECORD_SCHEMA = "neodojo.motion_record.v1"
TRACK_SCHEMA = "neodojo.track.v1"
GVHMR_JOINT_EXPORT_SCHEMA = "neodojo.gvhmr_smplx_joints.v1"
SMPLX_PARAMETER_SCHEMA = "neodojo.smplx_parameters.v1"

_SMPLX_REQUIRED_PARAMETER_FIELDS = ("global_orient", "body_pose", "betas")
_SMPLX_FRAME_PARAMETER_FIELDS = {
    "global_orient",
    "body_pose",
    "transl",
    "left_hand_pose",
    "right_hand_pose",
    "jaw_pose",
    "leye_pose",
    "reye_pose",
    "expression",
}


@dataclass(frozen=True)
class MotionContractWriteResult:
    out_dir: Path
    motion_record_manifest_path: Path
    motion_record_data_path: Path
    smplx_track_manifest_path: Path
    smplx_track_data_path: Path
    smplx_parameters_data_path: Path | None = None


def _write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _relative_path(path: Path, start: Path) -> str:
    return os.path.relpath(path, start).replace(os.sep, "/")


def validate_output_dir(out_dir: Path, repo_root: Path | None = None) -> None:
    repo = (repo_root or Path.cwd()).resolve()
    resolved = out_dir.resolve(strict=False)
    if not _is_relative_to(resolved, repo):
        return

    relative = resolved.relative_to(repo)
    if relative.parts and relative.parts[0] == "outputs":
        return

    raise ValueError("output path inside this repo must be under outputs/")


def validate_scoring_source(track_manifests: dict[str, dict[str, Any]], scoring_source: str = "smplx") -> None:
    if scoring_source != "smplx":
        raise ValueError("SMPL-X is the only allowed scoring source")

    scoring_track = track_manifests.get(scoring_source)
    if not scoring_track:
        raise ValueError("missing SMPL-X scoring track")
    if not scoring_track.get("scoring_allowed"):
        raise ValueError("SMPL-X track must allow scoring")

    for track_id, manifest in track_manifests.items():
        if track_id != "smplx" and manifest.get("scoring_allowed"):
            raise ValueError("derived visual tracks cannot allow scoring")


def _as_posix(path: Path) -> str:
    return str(path).replace(os.sep, "/")


def _timing_metadata(fps: int | float, frame_count: int) -> dict[str, Any]:
    return {
        "fps": fps,
        "frame_count": frame_count,
        "duration_seconds": round(frame_count / float(fps), 6),
        "start_frame": 0,
        "end_frame": frame_count - 1,
    }


def _contact_windows(contact_flags: list[bool]) -> list[dict[str, int]]:
    windows: list[dict[str, int]] = []
    start: int | None = None
    for index, contact in enumerate(contact_flags):
        if contact and start is None:
            start = index
        elif not contact and start is not None:
            windows.append({"start_frame": start, "end_frame": index - 1})
            start = None
    if start is not None:
        windows.append({"start_frame": start, "end_frame": len(contact_flags) - 1})
    return windows


def _normalization_metadata(frames: list[dict[str, list[float]]]) -> tuple[dict[str, Any], dict[str, Any]]:
    left_ankles = [frame["left_ankle"][1] for frame in frames if "left_ankle" in frame]
    right_ankles = [frame["right_ankle"][1] for frame in frames if "right_ankle" in frame]
    floor_height = round(min(left_ankles + right_ankles), 4)
    tolerance = 0.02
    left_contacts = [abs(frame["left_ankle"][1] - floor_height) <= tolerance for frame in frames]
    right_contacts = [abs(frame["right_ankle"][1] - floor_height) <= tolerance for frame in frames]
    coordinates = {
        "schema": "neodojo.coordinates.v1",
        "units": "meters",
        "world_up_axis": "y",
        "facing_axis": "z+",
        "root_joint": "pelvis",
        "floor_height_m": floor_height,
        "normalization": "fixture/imported joints normalized into neodojo local y-up coordinates",
    }
    contact = {
        "schema": "neodojo.contact.v1",
        "source": "derived_from_ankle_height",
        "floor_height_m": floor_height,
        "contact_tolerance_m": tolerance,
        "feet": {
            "left": {
                "contact_ratio": round(sum(left_contacts) / len(frames), 4),
                "contact_windows": _contact_windows(left_contacts),
            },
            "right": {
                "contact_ratio": round(sum(right_contacts) / len(frames), 4),
                "contact_windows": _contact_windows(right_contacts),
            },
        },
        "diagnostics": {
            "advisory": True,
            "notes": "contact is derived from normalized joint height and is not a physics contact solve",
        },
    }
    return coordinates, contact


def _require_text(payload: dict[str, Any], key: str, fallback: str) -> str:
    value = payload.get(key, fallback)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"GVHMR joint export must contain string {key}")
    return value


def _require_fps(payload: dict[str, Any]) -> int | float:
    fps = payload.get("fps", FIXTURE_FPS)
    if isinstance(fps, bool) or not isinstance(fps, (int, float)) or fps <= 0:
        raise ValueError("GVHMR joint export must contain positive numeric fps")
    return fps


def _normalize_point(value: Any, frame_index: int, joint: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"frame {frame_index} joint {joint} must be a 3D point")

    point = []
    for component in value:
        if isinstance(component, bool) or not isinstance(component, (int, float)):
            raise ValueError(f"frame {frame_index} joint {joint} must contain numeric coordinates")
        point.append(round(float(component), 4))
    return point


def _normalize_teaching_frames(raw_frames: Any) -> list[dict[str, list[float]]]:
    if not isinstance(raw_frames, list) or len(raw_frames) < 8:
        raise ValueError("GVHMR joint export must contain at least 8 frames")

    frames = []
    for frame_index, raw_frame in enumerate(raw_frames):
        if not isinstance(raw_frame, dict):
            raise ValueError(f"frame {frame_index} must be an object")
        missing = [joint for joint in TEACHING_JOINTS if joint not in raw_frame]
        if missing:
            raise ValueError(f"frame {frame_index} is missing teaching joints: {', '.join(missing)}")
        frames.append({joint: _normalize_point(raw_frame[joint], frame_index, joint) for joint in TEACHING_JOINTS})
    return frames


def _numeric_array_shape(value: Any, label: str) -> list[int]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty numeric array")

    def shape(node: Any, path: str) -> list[int]:
        if isinstance(node, list):
            if not node:
                raise ValueError(f"{path} must not contain empty arrays")
            child_shapes = [shape(child, f"{path}[]") for child in node]
            first_shape = child_shapes[0]
            if any(child_shape != first_shape for child_shape in child_shapes):
                raise ValueError(f"{path} must be rectangular")
            return [len(node), *first_shape]
        if isinstance(node, bool) or not isinstance(node, (int, float)):
            raise ValueError(f"{path} must contain only numeric values")
        return []

    return shape(value, label)


def _normalize_smplx_parameters(raw_parameters: Any, frame_count: int) -> tuple[dict[str, Any], dict[str, Any]] | None:
    if raw_parameters is None:
        return None
    if not isinstance(raw_parameters, dict):
        raise ValueError("GVHMR joint export smplx_parameters must be an object when provided")

    parameterization = raw_parameters.get("parameterization", "smplx")
    if not isinstance(parameterization, str) or not parameterization.strip():
        raise ValueError("smplx_parameters.parameterization must be a non-empty string")

    fields: dict[str, dict[str, Any]] = {}
    parameter_values: dict[str, Any] = {}
    metadata_keys = {"schema", "parameterization", "source", "provenance", "notes"}
    for field_name, value in sorted(raw_parameters.items()):
        if field_name in metadata_keys:
            continue
        if not isinstance(field_name, str) or not field_name:
            raise ValueError("SMPL-X parameter field names must be non-empty strings")
        shape = _numeric_array_shape(value, f"smplx_parameters.{field_name}")
        if field_name in _SMPLX_FRAME_PARAMETER_FIELDS and shape[0] != frame_count:
            raise ValueError(
                f"smplx_parameters.{field_name} frame count {shape[0]} "
                f"does not match teaching frame count {frame_count}"
            )
        fields[field_name] = {"shape": shape}
        parameter_values[field_name] = value

    if not fields:
        raise ValueError("GVHMR joint export smplx_parameters must contain at least one numeric field")

    missing = [field for field in _SMPLX_REQUIRED_PARAMETER_FIELDS if field not in fields]
    summary = {
        "schema": SMPLX_PARAMETER_SCHEMA,
        "parameterization": parameterization,
        "frame_count": frame_count,
        "fields": fields,
        "required_fields": list(_SMPLX_REQUIRED_PARAMETER_FIELDS),
        "missing_required_fields": missing,
        "mesh_ready": not missing,
    }
    data = {
        "schema": SMPLX_PARAMETER_SCHEMA,
        "parameterization": parameterization,
        "frame_count": frame_count,
        "fields": parameter_values,
    }
    return summary, data


def _write_motion_contract(
    out_dir: Path,
    frames: list[dict[str, list[float]]],
    *,
    fixture_only: bool,
    source_type: str,
    routine: str,
    form: str,
    fps: int | float,
    provenance: dict[str, Any],
    smplx_parameters: dict[str, Any] | None = None,
) -> MotionContractWriteResult:
    validate_output_dir(out_dir)
    timing = _timing_metadata(fps, len(frames))
    coordinates, contact = _normalization_metadata(frames)

    motion_dir = out_dir / "motion-record"
    track_dir = out_dir / "tracks" / "smplx"
    motion_data_path = motion_dir / "smplx-joints.json"
    smplx_parameters_data_path = motion_dir / "smplx-parameters.json"
    motion_manifest_path = motion_dir / "manifest.json"
    track_data_path = track_dir / "joints.json"
    track_manifest_path = track_dir / "manifest.json"

    motion_data = {
        "frames": frames,
        "joint_set": FIXTURE_JOINT_SET,
        "track_id": "smplx",
    }
    track_data = {
        "frames": frames,
        "joint_set": FIXTURE_JOINT_SET,
        "track_id": "smplx",
    }

    motion_manifest = {
        "schema": MOTION_RECORD_SCHEMA,
        "fixture_only": fixture_only,
        "source_type": source_type,
        "routine": routine,
        "form": form,
        "fps": fps,
        "frame_count": len(frames),
        "timing": timing,
        "coordinates": coordinates,
        "contact": contact,
        "joint_set": FIXTURE_JOINT_SET,
        "scoring_source": "smplx",
        "provenance": provenance,
        "data_files": {
            "smplx_frames": _relative_path(motion_data_path, motion_manifest_path.parent),
        },
    }
    normalized_parameters = _normalize_smplx_parameters(smplx_parameters, len(frames))
    if normalized_parameters is not None:
        parameter_summary, parameter_data = normalized_parameters
        parameter_data_file = _relative_path(smplx_parameters_data_path, motion_manifest_path.parent)
        motion_manifest["smplx_parameters"] = {
            **parameter_summary,
            "data_file": parameter_data_file,
        }
        motion_manifest["data_files"]["smplx_parameters"] = parameter_data_file
    track_manifest = {
        "schema": TRACK_SCHEMA,
        "track_id": "smplx",
        "fixture_only": fixture_only,
        "source_motion_record": _relative_path(motion_manifest_path, track_manifest_path.parent),
        "role": "teaching accuracy source",
        "scoring_allowed": True,
        "fps": fps,
        "frame_count": len(frames),
        "timing": timing,
        "coordinates": coordinates,
        "contact": contact,
        "joint_set": FIXTURE_JOINT_SET,
        "data_files": {
            "frames": _relative_path(track_data_path, track_manifest_path.parent),
        },
    }

    validate_scoring_source({"smplx": track_manifest}, scoring_source=motion_manifest["scoring_source"])

    _write_json(motion_data_path, motion_data)
    if normalized_parameters is not None:
        _write_json(smplx_parameters_data_path, parameter_data)
    _write_json(motion_manifest_path, motion_manifest)
    _write_json(track_data_path, track_data)
    _write_json(track_manifest_path, track_manifest)

    return MotionContractWriteResult(
        out_dir=out_dir,
        motion_record_manifest_path=motion_manifest_path,
        motion_record_data_path=motion_data_path,
        smplx_track_manifest_path=track_manifest_path,
        smplx_track_data_path=track_data_path,
        smplx_parameters_data_path=smplx_parameters_data_path if normalized_parameters is not None else None,
    )


def write_fixture_motion_contract(out_dir: Path, frame_count: int = 96) -> MotionContractWriteResult:
    frames = build_smplx_fixture_frames(frame_count)
    return _write_motion_contract(
        out_dir,
        frames,
        fixture_only=True,
        source_type="synthetic_fixture",
        routine=FIXTURE_ROUTINE,
        form=FIXTURE_FORM,
        fps=FIXTURE_FPS,
        provenance={
            "generator": "neodojo.fixtures.build_smplx_fixture_frames",
            "accuracy_role": "plumbing fixture only; not qigong teaching evidence",
        },
    )


def write_gvhmr_json_motion_contract(out_dir: Path, source_path: Path) -> MotionContractWriteResult:
    if not source_path.exists():
        raise ValueError(f"GVHMR joint export does not exist: {source_path}")
    try:
        payload = json.loads(source_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"failed to parse GVHMR joint export JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("GVHMR joint export must be a JSON object")
    require_schema(payload, GVHMR_JOINT_EXPORT_SCHEMA, "GVHMR joint export")

    raw_frames = payload.get("frames", payload.get("smplx_joints"))
    frames = _normalize_teaching_frames(raw_frames)
    routine = _require_text(payload, "routine", FIXTURE_ROUTINE)
    form = _require_text(payload, "form", "imported GVHMR segment")
    fps = _require_fps(payload)
    provenance = payload.get("provenance", {})
    if not isinstance(provenance, dict):
        raise ValueError("GVHMR joint export provenance must be an object when provided")
    provenance = {
        **provenance,
        "source_schema": payload.get("schema", GVHMR_JOINT_EXPORT_SCHEMA),
        "source_artifact": _as_posix(source_path),
        "source_artifact_resolved": _as_posix(source_path.resolve()),
        "accuracy_role": "imported SMPL-X teaching joints; not a fixture",
    }
    source_validation = payload.get("source_validation")
    if source_validation is not None:
        if not isinstance(source_validation, dict):
            raise ValueError("GVHMR joint export source_validation must be an object when provided")
        provenance["source_validation"] = source_validation

    return _write_motion_contract(
        out_dir,
        frames,
        fixture_only=False,
        source_type="gvhmr_smplx_joints_json",
        routine=routine,
        form=form,
        fps=fps,
        provenance=provenance,
        smplx_parameters=payload.get("smplx_parameters"),
    )


def resolve_motion_record_manifest(motion_record: Path) -> Path:
    if motion_record.is_file():
        return motion_record

    candidates = [
        motion_record / "motion-record" / "manifest.json",
        motion_record / "manifest.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise ValueError(f"could not find a motion-record manifest under {motion_record}")


def load_motion_record_frames(motion_manifest_path: Path) -> tuple[dict[str, Any], list[dict[str, list[float]]]]:
    manifest = json.loads(motion_manifest_path.read_text(encoding="utf-8"))
    require_schema(manifest, MOTION_RECORD_SCHEMA, "motion-record manifest")
    if manifest.get("scoring_source") != "smplx":
        raise ValueError("motion record must keep SMPL-X as scoring_source")

    data_file = manifest.get("data_files", {}).get("smplx_frames")
    if not data_file:
        raise ValueError("motion-record manifest is missing data_files.smplx_frames")

    data_path = motion_manifest_path.parent / data_file
    data = json.loads(data_path.read_text(encoding="utf-8"))
    frames = data.get("frames")
    if not isinstance(frames, list) or len(frames) < 8:
        raise ValueError("motion-record data must contain at least 8 SMPL-X frames")
    return manifest, frames


def load_track_frames(track_manifest_path: Path) -> list[dict[str, list[float]]]:
    manifest = json.loads(track_manifest_path.read_text(encoding="utf-8"))
    require_schema(manifest, TRACK_SCHEMA, "track manifest")
    if manifest.get("track_id") != "smplx":
        raise ValueError("only SMPL-X teaching tracks are supported in the local motion contract")
    if not manifest.get("scoring_allowed"):
        raise ValueError("SMPL-X teaching track must allow scoring")

    data_file = manifest.get("data_files", {}).get("frames")
    if not data_file:
        raise ValueError("track manifest is missing data_files.frames")

    data_path = track_manifest_path.parent / data_file
    data = json.loads(data_path.read_text(encoding="utf-8"))
    frames = data.get("frames")
    if not isinstance(frames, list) or len(frames) < 8:
        raise ValueError("track data must contain at least 8 frames")
    return frames
