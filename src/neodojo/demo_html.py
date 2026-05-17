from __future__ import annotations

import json
import math
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
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

TRAJECTORY_JOINTS = ["left_wrist", "right_wrist", "left_elbow", "right_elbow", "left_knee", "right_knee"]


@dataclass(frozen=True)
class DemoWriteResult:
    html_path: Path
    manifest_path: Path


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


def _g1_from_smplx(frame: dict[str, list[float]]) -> dict[str, list[float]]:
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


def build_fixture(frame_count: int = 96) -> dict[str, Any]:
    if frame_count < 8:
        raise ValueError("frame_count must be at least 8")

    smplx_frames = []
    g1_frames = []
    for index in range(frame_count):
        progress = index / (frame_count - 1)
        smplx = _smplx_frame(progress)
        smplx_frames.append(smplx)
        g1_frames.append(_g1_from_smplx(smplx))

    key_frame = frame_count - 1
    feedback = compute_feedback(smplx_frames[key_frame])

    return {
        "fixture_only": True,
        "routine": "Baduanjin opening-form fixture",
        "fps": 24,
        "frame_count": frame_count,
        "key_frame": key_frame,
        "scoring_source": "smplx",
        "tracks": {
            "smplx": {
                "label": "SMPL-X teacher",
                "role": "teaching accuracy source",
                "frames": smplx_frames,
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


def render_demo_html(fixture: dict[str, Any] | None = None) -> str:
    data = fixture if fixture is not None else build_fixture()
    template = resources.files("neodojo.templates").joinpath("teaching_demo.html").read_text(encoding="utf-8")
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return template.replace("__NEODOJO_DEMO_DATA__", payload)


def write_demo(out_dir: Path, frame_count: int = 96) -> DemoWriteResult:
    fixture = build_fixture(frame_count=frame_count)
    out_dir.mkdir(parents=True, exist_ok=True)

    html_path = out_dir / "index.html"
    manifest_path = out_dir / "manifest.json"
    html_path.write_text(render_demo_html(fixture), encoding="utf-8")
    manifest_path.write_text(
        json.dumps(
            {
                "fixture_only": True,
                "html": "index.html",
                "frame_count": fixture["frame_count"],
                "scoring_source": fixture["scoring_source"],
                "tracks": {
                    "smplx": fixture["tracks"]["smplx"]["role"],
                    "g1": fixture["tracks"]["g1"]["role"],
                },
                "feedback": fixture["feedback"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return DemoWriteResult(html_path=html_path, manifest_path=manifest_path)
