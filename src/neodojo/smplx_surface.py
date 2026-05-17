from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import require_schema
from .fixtures import BONES
from .motion_contract import (
    _relative_path,
    _write_json,
    load_motion_record_frames,
    resolve_motion_record_manifest,
    validate_output_dir,
)

SMPLX_SURFACE_PROXY_SCHEMA = "neodojo.smplx_surface_proxy.v1"

_SURFACE_RADII_M = {
    ("pelvis", "spine"): 0.105,
    ("spine", "neck"): 0.095,
    ("neck", "head"): 0.07,
    ("spine", "left_hip"): 0.085,
    ("spine", "right_hip"): 0.085,
    ("left_hip", "left_knee"): 0.06,
    ("right_hip", "right_knee"): 0.06,
    ("left_knee", "left_ankle"): 0.045,
    ("right_knee", "right_ankle"): 0.045,
    ("neck", "left_shoulder"): 0.055,
    ("neck", "right_shoulder"): 0.055,
    ("left_shoulder", "left_elbow"): 0.045,
    ("right_shoulder", "right_elbow"): 0.045,
    ("left_elbow", "left_wrist"): 0.035,
    ("right_elbow", "right_wrist"): 0.035,
}


@dataclass(frozen=True)
class SMPLXSurfaceProxyWriteResult:
    manifest_path: Path
    data_path: Path


def _radius_for_bone(start: str, end: str) -> float:
    return _SURFACE_RADII_M.get((start, end), _SURFACE_RADII_M.get((end, start), 0.04))


def _surface_frame(frame: dict[str, list[float]]) -> dict[str, Any]:
    capsules = []
    for start, end in BONES:
        if start not in frame or end not in frame:
            continue
        capsules.append(
            {
                "kind": "capsule",
                "start_joint": start,
                "end_joint": end,
                "start": frame[start],
                "end": frame[end],
                "radius_m": _radius_for_bone(start, end),
            }
        )
    return {"capsules": capsules}


def write_smplx_surface_proxy(out_dir: Path, motion_record: Path) -> SMPLXSurfaceProxyWriteResult:
    validate_output_dir(out_dir)
    motion_manifest_path = resolve_motion_record_manifest(motion_record)
    motion_manifest, smplx_frames = load_motion_record_frames(motion_manifest_path)

    surface_dir = out_dir / "surfaces" / "smplx"
    data_path = surface_dir / "surface-proxy.json"
    manifest_path = surface_dir / "manifest.json"
    frames = [_surface_frame(frame) for frame in smplx_frames]

    data = {
        "schema": SMPLX_SURFACE_PROXY_SCHEMA,
        "track_id": "smplx",
        "surface_kind": "joint_capsule_proxy",
        "frames": frames,
    }
    manifest = {
        "schema": SMPLX_SURFACE_PROXY_SCHEMA,
        "track_id": "smplx",
        "fixture_only": bool(motion_manifest.get("fixture_only", False)),
        "source_motion_record": _relative_path(motion_manifest_path, manifest_path.parent),
        "role": "SMPL-X body surface proxy for visual inspection",
        "derived_from": "smplx_joints",
        "surface_kind": "joint_capsule_proxy",
        "licensed_smplx_mesh": False,
        "scoring_allowed": False,
        "scoring_source": "smplx_joints",
        "fps": motion_manifest.get("fps"),
        "frame_count": len(frames),
        "timing": motion_manifest.get("timing"),
        "coordinates": motion_manifest.get("coordinates"),
        "contact": motion_manifest.get("contact"),
        "data_files": {
            "surface": _relative_path(data_path, manifest_path.parent),
        },
        "provenance": {
            "generator": "neodojo.smplx_surface.write_smplx_surface_proxy",
            "notes": (
                "Dependency-light capsule proxy derived from teaching joints. "
                "This is not a licensed SMPL-X mesh or body-model evaluation."
            ),
        },
    }
    _write_json(data_path, data)
    _write_json(manifest_path, manifest)
    return SMPLXSurfaceProxyWriteResult(manifest_path=manifest_path, data_path=data_path)


def resolve_smplx_surface_manifest(path: Path) -> Path:
    if path.is_file():
        return path

    candidates = [
        path / "surfaces" / "smplx" / "manifest.json",
        path / "manifest.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise ValueError(f"could not find an SMPL-X surface manifest under {path}")


def load_smplx_surface_proxy(surface_manifest_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = json.loads(surface_manifest_path.read_text(encoding="utf-8"))
    require_schema(manifest, SMPLX_SURFACE_PROXY_SCHEMA, "SMPL-X surface proxy manifest")
    if manifest.get("track_id") != "smplx":
        raise ValueError("expected an SMPL-X surface proxy manifest")
    if manifest.get("scoring_allowed"):
        raise ValueError("SMPL-X surface proxy cannot be a scoring source")

    data_file = manifest.get("data_files", {}).get("surface")
    if not data_file:
        raise ValueError("SMPL-X surface proxy manifest is missing data_files.surface")

    data_path = surface_manifest_path.parent / data_file
    data = json.loads(data_path.read_text(encoding="utf-8"))
    require_schema(data, SMPLX_SURFACE_PROXY_SCHEMA, "SMPL-X surface proxy data")
    frames = data.get("frames")
    if not isinstance(frames, list) or len(frames) < 8:
        raise ValueError("SMPL-X surface proxy data must contain at least 8 frames")
    return manifest, frames
