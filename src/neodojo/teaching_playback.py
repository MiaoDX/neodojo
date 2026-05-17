from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .demo_html import render_demo_html
from .fixtures import build_fixture_from_smplx_frames
from .g1_visual import load_g1_track_frames, resolve_g1_track_manifest
from .motion_contract import (
    _relative_path,
    _write_json,
    load_motion_record_frames,
    resolve_motion_record_manifest,
    validate_output_dir,
)


@dataclass(frozen=True)
class TeachingPlaybackWriteResult:
    html_path: Path
    manifest_path: Path


def _load_annotation_key_frame(annotations_path: Path | None, frame_count: int) -> tuple[int, str | None]:
    if annotations_path is None:
        return frame_count - 1, None

    annotations = json.loads(annotations_path.read_text(encoding="utf-8"))
    key_frame = annotations.get("key_frame")
    if not isinstance(key_frame, int):
        raise ValueError("annotations file must contain integer key_frame")
    if key_frame < 0 or key_frame >= frame_count:
        raise ValueError("annotation key_frame is outside the available frame range")
    name = annotations.get("name")
    if name is not None and not isinstance(name, str):
        raise ValueError("annotations name must be a string when provided")
    return key_frame, name


def write_teaching_playback_demo(
    out_dir: Path,
    motion_record: Path,
    g1_track: Path,
    annotations_path: Path | None = None,
) -> TeachingPlaybackWriteResult:
    validate_output_dir(out_dir)
    motion_manifest_path = resolve_motion_record_manifest(motion_record)
    g1_track_manifest_path = resolve_g1_track_manifest(g1_track)

    motion_manifest, smplx_frames = load_motion_record_frames(motion_manifest_path)
    g1_manifest, g1_frames = load_g1_track_frames(g1_track_manifest_path)
    if len(smplx_frames) != len(g1_frames):
        raise ValueError("SMPL-X and G1 tracks must have matching frame counts")

    key_frame, annotation_name = _load_annotation_key_frame(annotations_path, len(smplx_frames))
    fixture_only = bool(motion_manifest.get("fixture_only") or g1_manifest.get("fixture_only"))
    fixture = build_fixture_from_smplx_frames(
        smplx_frames,
        g1_frames=g1_frames,
        key_frame=key_frame,
        fixture_only=fixture_only,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "index.html"
    manifest_path = out_dir / "manifest.json"
    html_path.write_text(render_demo_html(fixture), encoding="utf-8")

    manifest = {
        "fixture_only": fixture_only,
        "html": "index.html",
        "motion_record": _relative_path(motion_manifest_path, manifest_path.parent),
        "tracks": {
            "smplx": {
                "role": "teaching accuracy source",
                "source": _relative_path(motion_manifest_path, manifest_path.parent),
            },
            "g1": {
                "role": g1_manifest["role"],
                "manifest": _relative_path(g1_track_manifest_path, manifest_path.parent),
                "scoring_allowed": False,
            },
        },
        "annotations": _relative_path(annotations_path, manifest_path.parent) if annotations_path else None,
        "annotation_name": annotation_name,
        "frame_count": len(smplx_frames),
        "fps": motion_manifest.get("fps"),
        "key_frame": key_frame,
        "scoring_source": "smplx",
        "feedback": fixture["feedback"],
        "evidence": {
            "kind": "html_frame_payload",
            "rendered_tracks": ["smplx", "g1"],
            "trajectory_joints": fixture["trajectory_joints"],
        },
    }
    _write_json(manifest_path, manifest)
    return TeachingPlaybackWriteResult(html_path=html_path, manifest_path=manifest_path)
