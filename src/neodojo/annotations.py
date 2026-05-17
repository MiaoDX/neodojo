from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import ANNOTATION_SCHEMA
from .fixtures import compute_feedback
from .motion_contract import (
    _relative_path,
    _write_json,
    load_motion_record_frames,
    resolve_motion_record_manifest,
    validate_output_dir,
)


@dataclass(frozen=True)
class AnnotationDetectResult:
    manifest_path: Path


def _wrist_height_score(frame: dict[str, list[float]]) -> tuple[float, float, float]:
    left_wrist = frame["left_wrist"]
    right_wrist = frame["right_wrist"]
    left_elbow = frame["left_elbow"]
    right_elbow = frame["right_elbow"]
    average_wrist_y = (left_wrist[1] + right_wrist[1]) / 2
    average_elbow_y = (left_elbow[1] + right_elbow[1]) / 2
    wrist_symmetry = abs(abs(left_wrist[0]) - abs(right_wrist[0]))
    elbow_drop = average_wrist_y - average_elbow_y
    return average_wrist_y, elbow_drop, -wrist_symmetry


def detect_opening_form_keyframe(frames: list[dict[str, list[float]]]) -> int:
    if len(frames) < 8:
        raise ValueError("key-frame detection requires at least 8 frames")
    return max(range(len(frames)), key=lambda index: _wrist_height_score(frames[index]))


def _constraint_results(feedback: dict[str, Any]) -> list[dict[str, Any]]:
    checks = feedback.get("checks", {})
    return [
        {
            "source": "smplx",
            "kind": "shoulders_below_neck",
            "metric": "shoulder_clearance_m",
            "threshold_m": 0.08,
            "actual_m": feedback.get("shoulder_clearance_m"),
            "passed": bool(checks.get("shoulders_below_neck")),
        },
        {
            "source": "smplx",
            "kind": "wrists_above_elbows",
            "metric": "elbow_drop_m",
            "threshold_m": 0.18,
            "actual_m": feedback.get("elbow_drop_m"),
            "passed": bool(checks.get("wrists_above_elbows")),
        },
        {
            "source": "smplx",
            "kind": "wrists_symmetric",
            "metric": "wrist_symmetry_m",
            "threshold_m": 0.03,
            "actual_m": feedback.get("wrist_symmetry_m"),
            "passed": bool(checks.get("wrists_symmetric")),
        },
    ]


def write_detected_annotations(out_dir: Path, motion_record: Path) -> AnnotationDetectResult:
    validate_output_dir(out_dir)
    motion_manifest_path = resolve_motion_record_manifest(motion_record)
    motion_manifest, frames = load_motion_record_frames(motion_manifest_path)
    frame_index = detect_opening_form_keyframe(frames)
    feedback = compute_feedback(frames[frame_index])
    frame_range = {
        "start_frame": max(0, frame_index - 2),
        "end_frame": min(len(frames) - 1, frame_index + 2),
    }
    manifest_path = out_dir / "manifest.json"
    manifest = {
        "schema": ANNOTATION_SCHEMA,
        "fixture_only": bool(motion_manifest.get("fixture_only")),
        "source_motion_record": _relative_path(motion_manifest_path, manifest_path.parent),
        "detector": {
            "name": "opening_form_raise_hands_apex",
            "version": "neodojo.detector.opening_form_apex.v1",
            "method": "select frame with highest average SMPL-X wrist height, elbow drop, and wrist symmetry",
            "advisory": True,
        },
        "routine": motion_manifest.get("routine"),
        "form": motion_manifest.get("form"),
        "frame_count": len(frames),
        "keyframes": [
            {
                "name": "raise hands apex",
                "frame": frame_index,
                "frame_range": frame_range,
                "terms": ["sink shoulders", "drop elbows", "wrists above elbows", "wrists symmetric"],
                "selected_joints": [
                    "neck",
                    "left_shoulder",
                    "right_shoulder",
                    "left_elbow",
                    "right_elbow",
                    "left_wrist",
                    "right_wrist",
                ],
                "constraints": _constraint_results(feedback),
                "feedback": feedback,
            }
        ],
    }
    _write_json(manifest_path, manifest)
    return AnnotationDetectResult(manifest_path=manifest_path)
