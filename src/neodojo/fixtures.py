from __future__ import annotations

import math
from typing import Any

BONES = [
    ["pelvis", "spine"],
    ["spine", "neck"],
    ["neck", "head"],
    ["spine", "left_hip"],
    ["left_hip", "left_knee"],
    ["left_knee", "left_ankle"],
    ["spine", "right_hip"],
    ["right_hip", "right_knee"],
    ["right_knee", "right_ankle"],
    ["neck", "left_shoulder"],
    ["left_shoulder", "left_elbow"],
    ["left_elbow", "left_wrist"],
    ["neck", "right_shoulder"],
    ["right_shoulder", "right_elbow"],
    ["right_elbow", "right_wrist"],
]

TRAJECTORY_JOINTS = [
    "left_wrist",
    "right_wrist",
    "left_elbow",
    "right_elbow",
    "left_knee",
    "right_knee",
]

FIXTURE_ROUTINE = "Baduanjin"
FIXTURE_FORM = "opening-form fixture"
FIXTURE_FPS = 24
FIXTURE_JOINT_SET = "neodojo_fixture_v1"


def _point(x: float, y: float, z: float) -> list[float]:
    return [round(x, 4), round(y, 4), round(z, 4)]


def _smplx_frame(progress: float) -> dict[str, list[float]]:
    lift = 0.5 - 0.5 * math.cos(math.pi * progress)
    settle = math.sin(math.pi * progress)
    sway = 0.035 * math.sin(2 * math.pi * progress)
    knee_bend = 0.055 * settle

    pelvis_y = 1.0 - 0.035 * settle
    spine_y = 1.38 - 0.02 * settle
    neck_y = 1.73 - 0.005 * settle
    shoulder_y = 1.6 + 0.02 * lift

    left_elbow = _point(-0.49 + 0.2 * lift, 1.31 + 0.67 * lift, 0.05 + sway)
    right_elbow = _point(0.49 - 0.2 * lift, 1.31 + 0.67 * lift, 0.05 - sway)
    left_wrist = _point(-0.62 + 0.46 * lift, 1.12 + 1.18 * lift, 0.1 + sway)
    right_wrist = _point(0.62 - 0.46 * lift, 1.12 + 1.18 * lift, 0.1 - sway)

    return {
        "pelvis": _point(0.0, pelvis_y, 0.0),
        "spine": _point(0.0, spine_y, 0.02 * settle),
        "neck": _point(0.0, neck_y, 0.0),
        "head": _point(0.0, 1.93, 0.0),
        "left_hip": _point(-0.19, pelvis_y - 0.04, 0.0),
        "left_knee": _point(-0.22, 0.56 - knee_bend, 0.06),
        "left_ankle": _point(-0.22, 0.08, -0.03),
        "right_hip": _point(0.19, pelvis_y - 0.04, 0.0),
        "right_knee": _point(0.22, 0.56 - knee_bend, 0.06),
        "right_ankle": _point(0.22, 0.08, -0.03),
        "left_shoulder": _point(-0.32, shoulder_y, 0.0),
        "left_elbow": left_elbow,
        "left_wrist": left_wrist,
        "right_shoulder": _point(0.32, shoulder_y, 0.0),
        "right_elbow": right_elbow,
        "right_wrist": right_wrist,
    }


def build_smplx_fixture_frames(frame_count: int = 96) -> list[dict[str, list[float]]]:
    if frame_count < 8:
        raise ValueError("frame_count must be at least 8")

    frames = []
    for index in range(frame_count):
        progress = index / (frame_count - 1)
        frames.append(_smplx_frame(progress))
    return frames


def derive_g1_like_frame(frame: dict[str, list[float]]) -> dict[str, list[float]]:
    """Create a derived visual track with constrained torso and arm motion."""
    derived: dict[str, list[float]] = {}
    for joint, point in frame.items():
        x, y, z = point
        if joint in {"left_wrist", "right_wrist"}:
            y -= 0.12
            x *= 1.08
        elif joint in {"left_elbow", "right_elbow"}:
            y -= 0.06
            z *= 0.65
        elif joint in {"spine", "neck"}:
            z *= 0.25
        elif joint == "head":
            y -= 0.03
        derived[joint] = _point(x * 0.94, y, z * 0.7)
    return derived


def compute_feedback(frame: dict[str, list[float]]) -> dict[str, Any]:
    neck_y = frame["neck"][1]
    shoulder_y = (frame["left_shoulder"][1] + frame["right_shoulder"][1]) / 2
    elbow_y = (frame["left_elbow"][1] + frame["right_elbow"][1]) / 2
    wrist_y = (frame["left_wrist"][1] + frame["right_wrist"][1]) / 2
    wrist_symmetry = abs(abs(frame["left_wrist"][0]) - abs(frame["right_wrist"][0]))

    shoulder_clearance = neck_y - shoulder_y
    elbow_drop = wrist_y - elbow_y

    checks = {
        "shoulders_below_neck": shoulder_clearance >= 0.08,
        "wrists_above_elbows": elbow_drop >= 0.18,
        "wrists_symmetric": wrist_symmetry <= 0.03,
    }

    return {
        "source": "smplx",
        "name": "manual key-frame geometry check",
        "shoulder_clearance_m": round(shoulder_clearance, 4),
        "elbow_drop_m": round(elbow_drop, 4),
        "wrist_symmetry_m": round(wrist_symmetry, 4),
        "checks": checks,
        "passed": all(checks.values()),
    }


def build_fixture_from_smplx_frames(frames: list[dict[str, list[float]]]) -> dict[str, Any]:
    if len(frames) < 8:
        raise ValueError("fixture must include at least 8 frames")

    g1_frames = [derive_g1_like_frame(frame) for frame in frames]
    key_frame = len(frames) - 1
    feedback = compute_feedback(frames[key_frame])

    return {
        "fixture_only": True,
        "routine": f"{FIXTURE_ROUTINE} {FIXTURE_FORM}",
        "fps": FIXTURE_FPS,
        "frame_count": len(frames),
        "key_frame": key_frame,
        "scoring_source": "smplx",
        "tracks": {
            "smplx": {
                "label": "SMPL-X teacher",
                "role": "teaching accuracy source",
                "frames": frames,
            },
            "g1": {
                "label": "Unitree G1 visual",
                "role": "derived visual companion",
                "frames": g1_frames,
            },
        },
        "bones": BONES,
        "trajectory_joints": TRAJECTORY_JOINTS,
        "feedback": feedback,
    }


def build_fixture(frame_count: int = 96) -> dict[str, Any]:
    return build_fixture_from_smplx_frames(build_smplx_fixture_frames(frame_count))
