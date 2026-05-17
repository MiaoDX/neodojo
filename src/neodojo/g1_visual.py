from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import require_schema
from .fixtures import FIXTURE_FPS, FIXTURE_JOINT_SET, TEACHING_JOINTS, derive_g1_like_frame
from .motion_contract import (
    TRACK_SCHEMA,
    _normalize_point,
    _normalization_metadata,
    _timing_metadata,
    _write_json,
    load_motion_record_frames,
    resolve_motion_record_manifest,
    validate_output_dir,
    validate_scoring_source,
)

ROBOT_MODEL_SCHEMA = "neodojo.robot_model.v1"
COMPARISON_REPORT_SCHEMA = "neodojo.track_comparison.v1"
GMR_TRACK_EXPORT_SCHEMA = "neodojo.gmr_unitree_g1_track.v1"
SUPPORTED_ROBOT = "unitree_g1"


@dataclass(frozen=True)
class RobotModelWriteResult:
    descriptor_path: Path


@dataclass(frozen=True)
class G1TrackWriteResult:
    track_manifest_path: Path
    track_data_path: Path
    comparison_report_path: Path


def _as_posix(path: Path) -> str:
    return str(path).replace(os.sep, "/")


def _relative_path(path: Path, start: Path) -> str:
    return os.path.relpath(path, start).replace(os.sep, "/")


def _resolve_existing(path: Path) -> Path:
    if not path.exists():
        raise ValueError(f"file does not exist: {path}")
    return path.resolve()


def _infer_model_format(model_path: Path, root: ET.Element) -> str:
    suffix = model_path.suffix.lower()
    if suffix == ".urdf" or root.tag == "robot":
        return "urdf"
    if suffix == ".xml" or root.tag == "mujoco":
        return "mjcf"
    raise ValueError("supported G1 model formats are URDF and MJCF/XML")


def _mesh_references(root: ET.Element, model_format: str) -> list[str]:
    if model_format == "urdf":
        return [mesh.attrib["filename"] for mesh in root.findall(".//mesh") if mesh.attrib.get("filename")]
    return [mesh.attrib["file"] for mesh in root.findall(".//mesh") if mesh.attrib.get("file")]


def _joint_names(root: ET.Element) -> list[str]:
    return [joint.attrib.get("name", "") for joint in root.findall(".//joint") if joint.attrib.get("name")]


def _root_name(root: ET.Element, model_format: str) -> str | None:
    if model_format == "urdf":
        link = root.find(".//link")
        return link.attrib.get("name") if link is not None else None

    body = root.find(".//body")
    return body.attrib.get("name") if body is not None else None


def _resolve_mesh_reference(reference: str, model_path: Path, mesh_roots: list[Path]) -> Path | None:
    candidates = []
    ref_path = Path(reference)
    if ref_path.is_absolute():
        candidates.append(ref_path)
    else:
        candidates.append(model_path.parent / ref_path)
        for mesh_root in mesh_roots:
            candidates.append(mesh_root / ref_path)

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return None


def write_fixture_g1_model_descriptor(out_dir: Path) -> RobotModelWriteResult:
    validate_output_dir(out_dir)
    descriptor_path = out_dir / "robot-models" / SUPPORTED_ROBOT / "manifest.json"
    descriptor = {
        "schema": ROBOT_MODEL_SCHEMA,
        "robot": SUPPORTED_ROBOT,
        "fixture_only": True,
        "model_format": "fixture_descriptor",
        "model_path": None,
        "mesh_roots": [],
        "source_url": None,
        "source_revision": None,
        "license": None,
        "variant": "g1-like fixture skeleton",
        "joint_count": 16,
        "joints": [],
        "root_name": "pelvis",
        "provenance": {
            "generator": "neodojo.fixtures.derive_g1_like_frame",
            "accuracy_role": "visual plumbing fixture only; not a real Unitree G1 asset",
        },
        "validation": {
            "loadable": True,
            "missing_assets": [],
        },
    }
    _write_json(descriptor_path, descriptor)
    return RobotModelWriteResult(descriptor_path=descriptor_path)


def register_g1_model(
    out_dir: Path,
    model_path: Path,
    mesh_roots: list[Path] | None = None,
    source_url: str | None = None,
    source_revision: str | None = None,
    license_name: str | None = None,
    variant: str | None = None,
) -> RobotModelWriteResult:
    validate_output_dir(out_dir)
    resolved_model = _resolve_existing(model_path)
    resolved_mesh_roots = [_resolve_existing(path) for path in mesh_roots or []]

    try:
        root = ET.parse(resolved_model).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"failed to parse robot model XML: {exc}") from exc

    model_format = _infer_model_format(resolved_model, root)
    missing_assets = []
    for reference in _mesh_references(root, model_format):
        if _resolve_mesh_reference(reference, resolved_model, resolved_mesh_roots) is None:
            missing_assets.append(reference)

    if missing_assets:
        missing = ", ".join(missing_assets)
        raise ValueError(f"robot model references missing mesh assets: {missing}")

    joints = _joint_names(root)
    descriptor_path = out_dir / "robot-models" / SUPPORTED_ROBOT / "manifest.json"
    descriptor = {
        "schema": ROBOT_MODEL_SCHEMA,
        "robot": SUPPORTED_ROBOT,
        "fixture_only": False,
        "model_format": model_format,
        "model_path": _as_posix(model_path),
        "resolved_model_path": _as_posix(resolved_model),
        "mesh_roots": [_as_posix(path) for path in mesh_roots or []],
        "source_url": source_url,
        "source_revision": source_revision,
        "license": license_name,
        "variant": variant,
        "joint_count": len(joints),
        "joints": joints,
        "root_name": _root_name(root, model_format),
        "provenance": {
            "registered_by": "neodojo.robot-model register",
        },
        "validation": {
            "loadable": True,
            "missing_assets": [],
        },
    }
    _write_json(descriptor_path, descriptor)
    return RobotModelWriteResult(descriptor_path=descriptor_path)


def build_g1_visual_track(
    motion_record: Path,
    out_dir: Path,
    model_descriptor_path: Path | None = None,
) -> G1TrackWriteResult:
    validate_output_dir(out_dir)
    motion_manifest_path = resolve_motion_record_manifest(motion_record)
    motion_manifest, smplx_frames = load_motion_record_frames(motion_manifest_path)

    if model_descriptor_path is not None and not model_descriptor_path.exists():
        raise ValueError(f"G1 model descriptor does not exist: {model_descriptor_path}")

    g1_frames = [derive_g1_like_frame(frame) for frame in smplx_frames]
    track_dir = out_dir / "tracks" / "g1"
    track_data_path = track_dir / "joints.json"
    track_manifest_path = track_dir / "manifest.json"
    report_path = out_dir / "comparison-report.json"

    track_data = {
        "frames": g1_frames,
        "joint_set": FIXTURE_JOINT_SET,
        "track_id": "g1",
    }
    track_manifest = {
        "schema": TRACK_SCHEMA,
        "track_id": "g1",
        "robot": SUPPORTED_ROBOT,
        "fixture_only": True,
        "source_motion_record": _relative_path(motion_manifest_path, track_manifest_path.parent),
        "role": "derived visual companion",
        "derived_from": "smplx",
        "derivation": "fixture_g1_like_from_smplx",
        "model_descriptor": (
            _relative_path(model_descriptor_path, track_manifest_path.parent) if model_descriptor_path else None
        ),
        "scoring_allowed": False,
        "fps": motion_manifest.get("fps", FIXTURE_FPS),
        "frame_count": len(g1_frames),
        "timing": motion_manifest.get("timing"),
        "coordinates": motion_manifest.get("coordinates"),
        "contact": motion_manifest.get("contact"),
        "joint_set": FIXTURE_JOINT_SET,
        "data_files": {
            "frames": _relative_path(track_data_path, track_manifest_path.parent),
        },
    }
    smplx_manifest = {
        "track_id": "smplx",
        "scoring_allowed": True,
    }
    validate_scoring_source({"smplx": smplx_manifest, "g1": track_manifest})

    report = {
        "schema": COMPARISON_REPORT_SCHEMA,
        "fixture_only": True,
        "canonical_track": "smplx",
        "derived_tracks": ["g1"],
        "scoring_source": "smplx",
        "g1_scoring_allowed": False,
        "frame_count": len(g1_frames),
        "fps": track_manifest["fps"],
        "frame_count_match": len(g1_frames) == int(motion_manifest["frame_count"]),
        "known_loss_points": [
            "torso DOF mismatch",
            "hand/gripper simplification",
            "foot/contact drift not evaluated in fixture mode",
        ],
        "provenance": {
            "source_motion_record": _relative_path(motion_manifest_path, report_path.parent),
            "model_descriptor": _relative_path(model_descriptor_path, report_path.parent)
            if model_descriptor_path
            else None,
        },
    }

    _write_json(track_data_path, track_data)
    _write_json(track_manifest_path, track_manifest)
    _write_json(report_path, report)

    return G1TrackWriteResult(
        track_manifest_path=track_manifest_path,
        track_data_path=track_data_path,
        comparison_report_path=report_path,
    )


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"{label} does not exist: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"failed to parse {label} JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def _require_gmr_fps(payload: dict[str, Any]) -> int | float:
    fps = payload.get("fps", FIXTURE_FPS)
    if isinstance(fps, bool) or not isinstance(fps, (int, float)) or fps <= 0:
        raise ValueError("GMR track export must contain positive numeric fps")
    return fps


def _normalize_joint_angles(raw_angles: Any, frame_index: int) -> dict[str, float]:
    if not isinstance(raw_angles, dict) or not raw_angles:
        raise ValueError(f"frame {frame_index} must contain non-empty joint_angles")

    angles: dict[str, float] = {}
    for joint, value in raw_angles.items():
        if not isinstance(joint, str) or not joint:
            raise ValueError(f"frame {frame_index} joint_angles keys must be non-empty strings")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"frame {frame_index} joint angle {joint} must be numeric")
        angles[joint] = round(float(value), 6)
    return angles


def _normalize_gmr_export_frames(raw_frames: Any) -> tuple[list[dict[str, list[float]]], list[dict[str, float]], list[str]]:
    if not isinstance(raw_frames, list) or len(raw_frames) < 8:
        raise ValueError("GMR track export must contain at least 8 frames")

    visual_frames: list[dict[str, list[float]]] = []
    joint_angle_frames: list[dict[str, float]] = []
    joint_angle_names: list[str] | None = None
    for frame_index, raw_frame in enumerate(raw_frames):
        if not isinstance(raw_frame, dict):
            raise ValueError(f"frame {frame_index} must be an object")
        visual_joints = raw_frame.get("visual_joints")
        if not isinstance(visual_joints, dict):
            raise ValueError(f"frame {frame_index} must contain visual_joints")
        missing = [joint for joint in TEACHING_JOINTS if joint not in visual_joints]
        if missing:
            raise ValueError(f"frame {frame_index} is missing visual joints: {', '.join(missing)}")

        normalized_visual = {
            joint: _normalize_point(visual_joints[joint], frame_index, joint)
            for joint in TEACHING_JOINTS
        }
        normalized_angles = _normalize_joint_angles(raw_frame.get("joint_angles"), frame_index)
        current_joint_names = sorted(normalized_angles)
        if joint_angle_names is None:
            joint_angle_names = current_joint_names
        elif current_joint_names != joint_angle_names:
            raise ValueError(f"frame {frame_index} joint_angles keys do not match the first frame")

        visual_frames.append(normalized_visual)
        joint_angle_frames.append(normalized_angles)

    return visual_frames, joint_angle_frames, joint_angle_names or []


def import_gmr_json_track(
    out_dir: Path,
    source_path: Path,
    *,
    motion_record: Path | None = None,
    model_descriptor_path: Path | None = None,
) -> G1TrackWriteResult:
    validate_output_dir(out_dir)
    payload = _load_json_object(source_path, "GMR track export")
    require_schema(payload, GMR_TRACK_EXPORT_SCHEMA, "GMR track export")
    if payload.get("robot") != SUPPORTED_ROBOT:
        raise ValueError("GMR track export must target unitree_g1")
    if model_descriptor_path is not None and not model_descriptor_path.exists():
        raise ValueError(f"G1 model descriptor does not exist: {model_descriptor_path}")

    visual_frames, joint_angle_frames, joint_angle_names = _normalize_gmr_export_frames(payload.get("frames"))
    fps = _require_gmr_fps(payload)
    timing = payload.get("timing") or _timing_metadata(fps, len(visual_frames))
    coordinates = payload.get("coordinates")
    contact = payload.get("contact")
    motion_manifest_path: Path | None = None
    motion_manifest: dict[str, Any] | None = None
    frame_count_match: bool | None = None
    fps_match: bool | None = None

    if motion_record is not None:
        motion_manifest_path = resolve_motion_record_manifest(motion_record)
        motion_manifest, smplx_frames = load_motion_record_frames(motion_manifest_path)
        frame_count_match = len(visual_frames) == len(smplx_frames)
        if not frame_count_match:
            raise ValueError("GMR track frame count must match the source motion record")
        fps_match = float(motion_manifest.get("fps", fps)) == float(fps)
        timing = motion_manifest.get("timing") or timing
        coordinates = motion_manifest.get("coordinates") or coordinates
        contact = motion_manifest.get("contact") or contact

    if coordinates is None or contact is None:
        derived_coordinates, derived_contact = _normalization_metadata(visual_frames)
        coordinates = coordinates or derived_coordinates
        contact = contact or derived_contact

    track_dir = out_dir / "tracks" / "g1"
    track_data_path = track_dir / "joints.json"
    track_manifest_path = track_dir / "manifest.json"
    report_path = out_dir / "comparison-report.json"
    provenance = payload.get("provenance", {})
    if not isinstance(provenance, dict):
        raise ValueError("GMR track export provenance must be an object when provided")

    fixture_only = bool(payload.get("fixture_only", False))
    track_data = {
        "frames": visual_frames,
        "joint_angles": joint_angle_frames,
        "joint_angle_names": joint_angle_names,
        "joint_set": FIXTURE_JOINT_SET,
        "track_id": "g1",
    }
    track_manifest = {
        "schema": TRACK_SCHEMA,
        "track_id": "g1",
        "robot": SUPPORTED_ROBOT,
        "fixture_only": fixture_only,
        "source_motion_record": _relative_path(motion_manifest_path, track_manifest_path.parent)
        if motion_manifest_path
        else None,
        "role": "imported GMR visual companion",
        "derived_from": "gmr_unitree_g1",
        "derivation": "imported_gmr_unitree_g1",
        "model_descriptor": (
            _relative_path(model_descriptor_path, track_manifest_path.parent) if model_descriptor_path else None
        ),
        "scoring_allowed": False,
        "fps": fps,
        "frame_count": len(visual_frames),
        "timing": timing,
        "coordinates": coordinates,
        "contact": contact,
        "joint_set": FIXTURE_JOINT_SET,
        "pose_stream": {
            "kind": "unitree_g1_joint_angles",
            "source_schema": GMR_TRACK_EXPORT_SCHEMA,
            "joint_angle_count": len(joint_angle_names),
            "joint_angle_names": joint_angle_names,
        },
        "data_files": {
            "frames": _relative_path(track_data_path, track_manifest_path.parent),
        },
        "provenance": {
            **provenance,
            "source_artifact": _as_posix(source_path),
            "source_artifact_resolved": _as_posix(source_path.resolve()),
        },
    }
    validate_scoring_source(
        {"smplx": {"track_id": "smplx", "scoring_allowed": True}, "g1": track_manifest}
    )

    report = {
        "schema": COMPARISON_REPORT_SCHEMA,
        "fixture_only": fixture_only,
        "canonical_track": "smplx",
        "derived_tracks": ["g1"],
        "scoring_source": "smplx",
        "g1_scoring_allowed": False,
        "frame_count": len(visual_frames),
        "fps": fps,
        "frame_count_match": frame_count_match,
        "fps_match": fps_match,
        "joint_angle_count": len(joint_angle_names),
        "joint_angle_names": joint_angle_names,
        "known_loss_points": [
            "imported GMR pose remains a visual companion",
            "G1 torso and hand DOF still differ from SMPL-X",
            "teaching feedback must continue to read SMPL-X",
        ],
        "provenance": {
            "source_gmr_export": _as_posix(source_path),
            "source_motion_record": _relative_path(motion_manifest_path, report_path.parent)
            if motion_manifest_path
            else None,
            "model_descriptor": _relative_path(model_descriptor_path, report_path.parent)
            if model_descriptor_path
            else None,
            "source_motion_record_fixture_only": motion_manifest.get("fixture_only") if motion_manifest else None,
        },
    }

    _write_json(track_data_path, track_data)
    _write_json(track_manifest_path, track_manifest)
    _write_json(report_path, report)

    return G1TrackWriteResult(
        track_manifest_path=track_manifest_path,
        track_data_path=track_data_path,
        comparison_report_path=report_path,
    )


def resolve_g1_track_manifest(path: Path) -> Path:
    if path.is_file():
        return path

    candidates = [
        path / "tracks" / "g1" / "manifest.json",
        path / "manifest.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise ValueError(f"could not find a G1 track manifest under {path}")


def load_g1_track_frames(track_manifest_path: Path) -> tuple[dict[str, Any], list[dict[str, list[float]]]]:
    manifest = json.loads(track_manifest_path.read_text(encoding="utf-8"))
    require_schema(manifest, TRACK_SCHEMA, "G1 visual-track manifest")
    if manifest.get("track_id") != "g1":
        raise ValueError("expected a G1 visual-track manifest")
    if manifest.get("scoring_allowed"):
        raise ValueError("G1 visual tracks cannot allow scoring")

    data_file = manifest.get("data_files", {}).get("frames")
    if not data_file:
        raise ValueError("G1 track manifest is missing data_files.frames")

    data_path = track_manifest_path.parent / data_file
    data = json.loads(data_path.read_text(encoding="utf-8"))
    frames = data.get("frames")
    if not isinstance(frames, list) or len(frames) < 8:
        raise ValueError("G1 track data must contain at least 8 frames")
    return manifest, frames
