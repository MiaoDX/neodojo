from __future__ import annotations

import os
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import sha256_file
from .fixtures import derive_g1_like_frame
from .g1_visual import GMR_TRACK_EXPORT_SCHEMA, SUPPORTED_ROBOT
from .motion_contract import (
    _timing_metadata,
    _write_json,
    load_motion_record_frames,
    resolve_motion_record_manifest,
    validate_output_dir,
)

GMR_NATIVE_ADAPTER_REPORT_SCHEMA = "neodojo.gmr_native_adapter_report.v1"

UNITREE_G1_29DOF_JOINT_NAMES = [
    "left_hip_pitch_joint",
    "left_hip_roll_joint",
    "left_hip_yaw_joint",
    "left_knee_joint",
    "left_ankle_pitch_joint",
    "left_ankle_roll_joint",
    "right_hip_pitch_joint",
    "right_hip_roll_joint",
    "right_hip_yaw_joint",
    "right_knee_joint",
    "right_ankle_pitch_joint",
    "right_ankle_roll_joint",
    "waist_yaw_joint",
    "waist_roll_joint",
    "waist_pitch_joint",
    "left_shoulder_pitch_joint",
    "left_shoulder_roll_joint",
    "left_shoulder_yaw_joint",
    "left_elbow_joint",
    "left_wrist_roll_joint",
    "left_wrist_pitch_joint",
    "left_wrist_yaw_joint",
    "right_shoulder_pitch_joint",
    "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint",
    "right_elbow_joint",
    "right_wrist_roll_joint",
    "right_wrist_pitch_joint",
    "right_wrist_yaw_joint",
]


@dataclass(frozen=True)
class GMRNativeNormalizeResult:
    normalized_export_path: Path
    report_path: Path


def _as_posix(path: Path) -> str:
    return str(path).replace(os.sep, "/")


def _relative_path(path: Path, start: Path) -> str:
    return os.path.relpath(path, start).replace(os.sep, "/")


def _load_pickle_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"GMR native pickle does not exist: {path}")
    try:
        with path.open("rb") as file:
            payload = pickle.load(file)
    except ModuleNotFoundError as exc:
        raise ValueError(
            "failed to load GMR native pickle; install the package that wrote it, "
            f"or export a dependency-free normalized JSON first: {exc}"
        ) from exc
    except pickle.UnpicklingError as exc:
        raise ValueError(f"failed to unpickle GMR native output: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("GMR native pickle must contain a dictionary")
    return payload


def _tolist(value: Any, label: str) -> Any:
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, tuple):
        return [_tolist(item, label) for item in value]
    if isinstance(value, list):
        return [_tolist(item, label) for item in value]
    return value


def _numeric_row(row: Any, label: str, frame_index: int, *, width: int | None = None) -> list[float]:
    row = _tolist(row, label)
    if not isinstance(row, list) or not row:
        raise ValueError(f"{label} frame {frame_index} must be a non-empty numeric row")
    if width is not None and len(row) != width:
        raise ValueError(f"{label} frame {frame_index} must contain {width} values")

    normalized = []
    for value_index, value in enumerate(row):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{label} frame {frame_index} value {value_index} must be numeric")
        normalized.append(round(float(value), 6))
    return normalized


def _numeric_rows(value: Any, label: str, *, width: int | None = None) -> list[list[float]]:
    rows = _tolist(value, label)
    if not isinstance(rows, list) or len(rows) < 8:
        raise ValueError(f"GMR native pickle field {label} must contain at least 8 frames")
    return [_numeric_row(row, label, frame_index, width=width) for frame_index, row in enumerate(rows)]


def _positive_fps(value: Any) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ValueError("GMR native pickle must contain positive numeric fps")
    return value


def _embedded_joint_names(payload: dict[str, Any]) -> list[str] | None:
    for key in ("joint_names", "dof_names", "robot_dof_names", "robot_motor_names"):
        value = payload.get(key)
        if value is None:
            continue
        value = _tolist(value, key)
        if not isinstance(value, list) or not all(isinstance(name, str) and name for name in value):
            raise ValueError(f"GMR native pickle field {key} must be a list of joint-name strings")
        return value
    return None


def _resolve_joint_names(
    payload: dict[str, Any],
    joint_angle_width: int,
    *,
    robot: str,
    joint_names: list[str] | None = None,
) -> tuple[list[str], str]:
    if joint_names is not None:
        names = joint_names
        source = "cli"
    else:
        names = _embedded_joint_names(payload)
        source = "native_payload"
        if names is None and robot == SUPPORTED_ROBOT and joint_angle_width == len(UNITREE_G1_29DOF_JOINT_NAMES):
            names = UNITREE_G1_29DOF_JOINT_NAMES
            source = "unitree_g1_29dof_default"

    if names is None:
        raise ValueError(
            "GMR native pickle does not include joint names; pass --joint-names for this robot/DOF layout"
        )
    if len(names) != joint_angle_width:
        raise ValueError(
            f"GMR native joint name count ({len(names)}) must match dof_pos width ({joint_angle_width})"
        )
    if len(set(names)) != len(names):
        raise ValueError("GMR native joint names must be unique")
    return names, source


def _joint_angle_frames(joint_names: list[str], dof_rows: list[list[float]]) -> list[dict[str, float]]:
    return [dict(zip(joint_names, row)) for row in dof_rows]


def normalize_gmr_pickle(
    out_dir: Path,
    source_path: Path,
    *,
    motion_record: Path,
    robot: str = SUPPORTED_ROBOT,
    joint_names: list[str] | None = None,
) -> GMRNativeNormalizeResult:
    validate_output_dir(out_dir)
    if robot != SUPPORTED_ROBOT:
        raise ValueError("only unitree_g1 native GMR output is supported in this adapter")

    payload = _load_pickle_object(source_path)
    fps = _positive_fps(payload.get("fps"))
    dof_rows = _numeric_rows(payload.get("dof_pos"), "dof_pos")
    root_pos_rows = _numeric_rows(payload.get("root_pos"), "root_pos", width=3)
    root_rot_rows = _numeric_rows(payload.get("root_rot"), "root_rot", width=4)
    if len(root_pos_rows) != len(dof_rows) or len(root_rot_rows) != len(dof_rows):
        raise ValueError("GMR native root_pos, root_rot, and dof_pos frame counts must match")

    joint_angle_width = len(dof_rows[0])
    if any(len(row) != joint_angle_width for row in dof_rows):
        raise ValueError("GMR native dof_pos width must be stable across frames")
    resolved_joint_names, joint_name_source = _resolve_joint_names(
        payload,
        joint_angle_width,
        robot=robot,
        joint_names=joint_names,
    )

    motion_manifest_path = resolve_motion_record_manifest(motion_record)
    motion_manifest, smplx_frames = load_motion_record_frames(motion_manifest_path)
    if len(smplx_frames) != len(dof_rows):
        raise ValueError("GMR native frame count must match the source motion record")
    fps_match = float(motion_manifest.get("fps", fps)) == float(fps)

    normalized_path = out_dir / "gmr-unitree-g1.normalized.json"
    report_path = out_dir / "gmr-native-adapter-report.json"
    timing = motion_manifest.get("timing") or _timing_metadata(fps, len(dof_rows))
    visual_frames = [derive_g1_like_frame(frame) for frame in smplx_frames]
    joint_angle_frames = _joint_angle_frames(resolved_joint_names, dof_rows)

    normalized_export = {
        "schema": GMR_TRACK_EXPORT_SCHEMA,
        "robot": SUPPORTED_ROBOT,
        "fixture_only": bool(motion_manifest.get("fixture_only", False)),
        "fps": fps,
        "timing": timing,
        "coordinates": motion_manifest.get("coordinates"),
        "contact": motion_manifest.get("contact"),
        "frames": [
            {
                "visual_joints": visual_frame,
                "joint_angles": joint_angles,
            }
            for visual_frame, joint_angles in zip(visual_frames, joint_angle_frames)
        ],
        "provenance": {
            "adapter": "neodojo.tracks normalize-gmr-pkl",
            "native_format": "YanjieZe/GMR robot motion pickle",
            "source_artifact": _as_posix(source_path),
            "source_artifact_resolved": _as_posix(source_path.resolve()),
            "source_artifact_sha256": sha256_file(source_path),
            "source_motion_record": _relative_path(motion_manifest_path, normalized_path.parent),
            "robot": SUPPORTED_ROBOT,
            "joint_name_source": joint_name_source,
            "visual_joints_source": "source_motion_record_smplx_derived",
            "root_streams_preserved_in_report": True,
        },
    }

    report = {
        "schema": GMR_NATIVE_ADAPTER_REPORT_SCHEMA,
        "source": _as_posix(source_path),
        "normalized_export": _relative_path(normalized_path, report_path.parent),
        "robot": SUPPORTED_ROBOT,
        "frame_count": len(dof_rows),
        "fps": fps,
        "fps_match": fps_match,
        "source_motion_record": _relative_path(motion_manifest_path, report_path.parent),
        "source_motion_record_fixture_only": motion_manifest.get("fixture_only"),
        "scoring_source": "smplx",
        "g1_scoring_allowed": False,
        "joint_angle_count": len(resolved_joint_names),
        "joint_angle_names": resolved_joint_names,
        "joint_name_source": joint_name_source,
        "root_pos_sample": root_pos_rows[0],
        "root_rot_sample_xyzw": root_rot_rows[0],
        "visual_joints_source": "source_motion_record_smplx_derived",
        "warnings": [
            "GMR pickles store root pose and robot joint angles, not the viewer joint positions used by the fixture HTML path.",
            "The normalized export keeps native Unitree G1 joint angles and derives display joints from the source SMPL-X motion record.",
            "Teaching feedback must continue to read SMPL-X, not the imported G1 pose stream.",
        ],
    }

    _write_json(normalized_path, normalized_export)
    _write_json(report_path, report)

    return GMRNativeNormalizeResult(
        normalized_export_path=normalized_path,
        report_path=report_path,
    )

