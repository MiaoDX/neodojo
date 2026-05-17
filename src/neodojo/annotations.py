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
    feedback_report_path: Path


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


def _average_y(frame: dict[str, list[float]], *joints: str) -> float:
    return sum(frame[joint][1] for joint in joints) / len(joints)


def _mid_support_frame(frames: list[dict[str, list[float]]], apex_frame: int) -> int:
    if apex_frame <= 1:
        return max(0, len(frames) // 2)
    search_end = max(1, apex_frame)
    return min(
        range(search_end),
        key=lambda index: _average_y(frames[index], "left_knee", "right_knee"),
    )


def _frame_range(frame_index: int, frame_count: int, radius: int = 2) -> dict[str, int]:
    return {
        "start_frame": max(0, frame_index - radius),
        "end_frame": min(frame_count - 1, frame_index + radius),
    }


def _term_result(
    *,
    term_id: str,
    label: str,
    frame_index: int,
    metric: str,
    actual: float,
    comparator: str,
    threshold: float,
    unit: str = "m",
) -> dict[str, Any]:
    if comparator == ">=":
        passed = actual >= threshold
        margin = actual - threshold
    elif comparator == "<=":
        passed = actual <= threshold
        margin = threshold - actual
    else:
        raise ValueError(f"unsupported comparator: {comparator}")
    status = "pass" if passed else "warn"
    if not passed:
        confidence = "needs_review"
    elif margin >= threshold * 0.25:
        confidence = "high"
    else:
        confidence = "medium"
    return {
        "id": term_id,
        "label": label,
        "source": "smplx",
        "frame": frame_index,
        "metric": metric,
        "actual": round(actual, 4),
        "threshold": threshold,
        "comparator": comparator,
        "unit": unit,
        "margin": round(margin, 4),
        "confidence": confidence,
        "status": status,
        "passed": passed,
    }


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


def _opening_stance_terms(frames: list[dict[str, list[float]]], frame_index: int) -> list[dict[str, Any]]:
    frame = frames[frame_index]
    ankle_width = abs(frame["right_ankle"][0] - frame["left_ankle"][0])
    ankle_height_delta = abs(frame["right_ankle"][1] - frame["left_ankle"][1])
    pelvis_center_offset = abs(frame["pelvis"][0] - ((frame["left_ankle"][0] + frame["right_ankle"][0]) / 2))
    return [
        _term_result(
            term_id="stance_width",
            label="stable stance width",
            frame_index=frame_index,
            metric="ankle_width_m",
            actual=ankle_width,
            comparator=">=",
            threshold=0.35,
        ),
        _term_result(
            term_id="level_feet",
            label="feet level on floor",
            frame_index=frame_index,
            metric="ankle_height_delta_m",
            actual=ankle_height_delta,
            comparator="<=",
            threshold=0.03,
        ),
        _term_result(
            term_id="centered_pelvis",
            label="pelvis centered over stance",
            frame_index=frame_index,
            metric="pelvis_center_offset_m",
            actual=pelvis_center_offset,
            comparator="<=",
            threshold=0.04,
        ),
    ]


def _support_terms(frames: list[dict[str, list[float]]], frame_index: int) -> list[dict[str, Any]]:
    frame = frames[frame_index]
    start = frames[0]
    pelvis_settle = start["pelvis"][1] - frame["pelvis"][1]
    knee_softness = _average_y(start, "left_knee", "right_knee") - _average_y(frame, "left_knee", "right_knee")
    root_sway = abs(frame["pelvis"][0] - start["pelvis"][0])
    return [
        _term_result(
            term_id="root_settle",
            label="root settles before lifting",
            frame_index=frame_index,
            metric="pelvis_settle_m",
            actual=pelvis_settle,
            comparator=">=",
            threshold=0.02,
        ),
        _term_result(
            term_id="soft_knees",
            label="knees soften evenly",
            frame_index=frame_index,
            metric="average_knee_drop_m",
            actual=knee_softness,
            comparator=">=",
            threshold=0.03,
        ),
        _term_result(
            term_id="root_center_stable",
            label="root stays centered",
            frame_index=frame_index,
            metric="pelvis_sway_m",
            actual=root_sway,
            comparator="<=",
            threshold=0.03,
        ),
    ]


def _apex_terms(frames: list[dict[str, list[float]]], frame_index: int, feedback: dict[str, Any]) -> list[dict[str, Any]]:
    frame = frames[frame_index]
    head_y = frame["head"][1]
    wrist_y = _average_y(frame, "left_wrist", "right_wrist")
    vertical_reach = wrist_y - head_y
    return [
        _term_result(
            term_id="sink_shoulders",
            label="sink shoulders",
            frame_index=frame_index,
            metric="shoulder_clearance_m",
            actual=float(feedback["shoulder_clearance_m"]),
            comparator=">=",
            threshold=0.08,
        ),
        _term_result(
            term_id="drop_elbows",
            label="drop elbows",
            frame_index=frame_index,
            metric="elbow_drop_m",
            actual=float(feedback["elbow_drop_m"]),
            comparator=">=",
            threshold=0.18,
        ),
        _term_result(
            term_id="wrist_symmetry",
            label="wrists symmetric",
            frame_index=frame_index,
            metric="wrist_symmetry_m",
            actual=float(feedback["wrist_symmetry_m"]),
            comparator="<=",
            threshold=0.03,
        ),
        _term_result(
            term_id="vertical_reach",
            label="vertical reach over head",
            frame_index=frame_index,
            metric="wrist_above_head_m",
            actual=vertical_reach,
            comparator=">=",
            threshold=0.2,
        ),
    ]


def _keyframe(
    *,
    name: str,
    frame_index: int,
    frame_count: int,
    terms: list[str],
    selected_joints: list[str],
    term_results: list[dict[str, Any]],
    primary: bool = False,
    feedback: dict[str, Any] | None = None,
    constraints: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    keyframe = {
        "name": name,
        "frame": frame_index,
        "primary": primary,
        "frame_range": _frame_range(frame_index, frame_count),
        "terms": terms,
        "selected_joints": selected_joints,
        "term_results": term_results,
        "constraints": constraints or [],
        "passed": all(result["passed"] for result in term_results),
    }
    if feedback is not None:
        keyframe["feedback"] = feedback
    return keyframe


def _routine_review(keyframes: list[dict[str, Any]]) -> dict[str, Any]:
    term_results = []
    for keyframe in keyframes:
        for result in keyframe.get("term_results", []):
            term_results.append(
                {
                    **result,
                    "keyframe": keyframe["name"],
                }
            )
    passed_terms = sum(1 for result in term_results if result["passed"])
    return {
        "schema": "neodojo.routine_feedback_report.v1",
        "source": "smplx",
        "scoring_source": "smplx",
        "advisory": True,
        "summary": {
            "keyframe_count": len(keyframes),
            "term_count": len(term_results),
            "passed_terms": passed_terms,
            "status": "pass" if passed_terms == len(term_results) else "review",
        },
        "keyframes": [
            {
                "name": keyframe["name"],
                "frame": keyframe["frame"],
                "primary": keyframe["primary"],
                "passed": keyframe["passed"],
                "terms": keyframe["terms"],
            }
            for keyframe in keyframes
        ],
        "term_results": term_results,
        "notes": [
            "Fixture/import review only; this is not proof of real qigong correctness.",
            "All feedback evidence is computed from SMPL-X teaching joints.",
        ],
    }


def write_detected_annotations(out_dir: Path, motion_record: Path) -> AnnotationDetectResult:
    validate_output_dir(out_dir)
    motion_manifest_path = resolve_motion_record_manifest(motion_record)
    motion_manifest, frames = load_motion_record_frames(motion_manifest_path)
    apex_frame = detect_opening_form_keyframe(frames)
    support_frame = _mid_support_frame(frames, apex_frame)
    apex_feedback = compute_feedback(frames[apex_frame])
    frame_count = len(frames)
    keyframes = [
        _keyframe(
            name="opening stance",
            frame_index=0,
            frame_count=frame_count,
            terms=["stable stance width", "feet level on floor", "pelvis centered over stance"],
            selected_joints=["pelvis", "left_ankle", "right_ankle"],
            term_results=_opening_stance_terms(frames, 0),
        ),
        _keyframe(
            name="settled support",
            frame_index=support_frame,
            frame_count=frame_count,
            terms=["root settles before lifting", "knees soften evenly", "root stays centered"],
            selected_joints=["pelvis", "left_knee", "right_knee"],
            term_results=_support_terms(frames, support_frame),
        ),
        _keyframe(
            name="raise hands apex",
            frame_index=apex_frame,
            frame_count=frame_count,
            terms=["sink shoulders", "drop elbows", "wrists above elbows", "wrists symmetric", "vertical reach"],
            selected_joints=[
                "head",
                "neck",
                "left_shoulder",
                "right_shoulder",
                "left_elbow",
                "right_elbow",
                "left_wrist",
                "right_wrist",
            ],
            term_results=_apex_terms(frames, apex_frame, apex_feedback),
            primary=True,
            constraints=_constraint_results(apex_feedback),
            feedback=apex_feedback,
        ),
    ]
    routine_review = _routine_review(keyframes)
    manifest_path = out_dir / "manifest.json"
    feedback_report_path = out_dir / "routine-feedback.json"
    manifest = {
        "schema": ANNOTATION_SCHEMA,
        "fixture_only": bool(motion_manifest.get("fixture_only")),
        "source_motion_record": _relative_path(motion_manifest_path, manifest_path.parent),
        "detector": {
            "name": "opening_form_routine_review",
            "version": "neodojo.detector.opening_form_routine_review.v1",
            "method": (
                "select opening stance, settled support, and apex frames from SMPL-X teaching joints; "
                "score posture terms from deterministic geometry"
            ),
            "advisory": True,
        },
        "routine": motion_manifest.get("routine"),
        "form": motion_manifest.get("form"),
        "frame_count": frame_count,
        "primary_keyframe": "raise hands apex",
        "feedback_report": _relative_path(feedback_report_path, manifest_path.parent),
        "routine_review": routine_review,
        "keyframes": keyframes,
    }
    report = {
        **routine_review,
        "source_annotation_manifest": _relative_path(manifest_path, feedback_report_path.parent),
        "routine": motion_manifest.get("routine"),
        "form": motion_manifest.get("form"),
        "frame_count": frame_count,
        "fixture_only": bool(motion_manifest.get("fixture_only")),
    }
    _write_json(manifest_path, manifest)
    _write_json(feedback_report_path, report)
    return AnnotationDetectResult(manifest_path=manifest_path, feedback_report_path=feedback_report_path)
