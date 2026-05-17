from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import ANNOTATION_SCHEMA, PLAYBACK_SCHEMA, local_file_metadata, require_schema
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
from .smplx_surface import load_smplx_surface_layer, resolve_smplx_surface_manifest


@dataclass(frozen=True)
class TeachingPlaybackWriteResult:
    html_path: Path
    manifest_path: Path


def _select_primary_keyframe(keyframes: list[Any], frame_count: int) -> dict[str, Any]:
    selected = None
    for candidate in keyframes:
        if not isinstance(candidate, dict):
            raise ValueError("annotation keyframes must be objects")
        frame = candidate.get("frame")
        if not isinstance(frame, int):
            raise ValueError("annotation keyframe must contain integer frame")
        if frame < 0 or frame >= frame_count:
            raise ValueError("annotation key_frame is outside the available frame range")
        if candidate.get("primary") is True and selected is None:
            selected = candidate
    return selected or keyframes[0]


def _normalize_annotation_manifest(
    annotations_path: Path | None,
    frame_count: int,
) -> tuple[int, str | None, dict[str, Any] | None, dict[str, Any] | None]:
    if annotations_path is None:
        return frame_count - 1, None, None, None

    annotations = json.loads(annotations_path.read_text(encoding="utf-8"))
    if not isinstance(annotations, dict):
        raise ValueError("annotations file must contain a JSON object")

    if annotations.get("schema") is None:
        key_frame = annotations.get("key_frame")
        name = annotations.get("name")
        keyframes = [
            {
                "name": name or "manual key frame",
                "frame": key_frame,
                "primary": True,
                "terms": [],
                "constraints": [],
            }
        ]
        normalized = {
            "schema": ANNOTATION_SCHEMA,
            "source_format": "legacy_key_frame",
            "keyframes": keyframes,
        }
    else:
        require_schema(annotations, ANNOTATION_SCHEMA, "annotation manifest")
        keyframes = annotations.get("keyframes")
        if not isinstance(keyframes, list) or not keyframes:
            raise ValueError("annotation manifest must contain non-empty keyframes")
        normalized = annotations

    primary_keyframe = _select_primary_keyframe(keyframes, frame_count)
    key_frame = primary_keyframe["frame"]
    name = primary_keyframe.get("name")
    if name is not None and not isinstance(name, str):
        raise ValueError("annotations name must be a string when provided")
    routine_review = normalized.get("routine_review")
    if routine_review is not None and not isinstance(routine_review, dict):
        raise ValueError("annotation routine_review must be an object when provided")
    return key_frame, name, normalized, routine_review


def _reference_video_sync(reference_video: Path | None, trim_start_seconds: float = 0.0) -> dict[str, Any] | None:
    if reference_video is None:
        return None
    media = local_file_metadata(
        reference_video,
        label="reference video",
        allowed_suffixes={".mp4", ".mov", ".m4v", ".webm"},
    )
    return {
        "schema": "neodojo.reference_video_sync.v1",
        "local_only": True,
        "media": media,
        "trim_start_seconds": round(trim_start_seconds, 3),
        "frame_zero_offset_seconds": round(trim_start_seconds, 3),
        "sync_confidence": "local path and trim metadata only",
    }


def _surface_label(surface_manifest: dict[str, Any]) -> str:
    if surface_manifest.get("licensed_smplx_mesh"):
        return "SMPL-X licensed mesh surface"
    return "SMPL-X surface proxy"


def _surface_layer_key(surface_manifest: dict[str, Any]) -> str:
    if surface_manifest.get("licensed_smplx_mesh"):
        return "smplx_mesh"
    return "smplx_proxy"


def write_teaching_playback_demo(
    out_dir: Path,
    motion_record: Path,
    g1_track: Path,
    annotations_path: Path | None = None,
    smplx_surface: Path | None = None,
    reference_video: Path | None = None,
    reference_trim_start_seconds: float = 0.0,
) -> TeachingPlaybackWriteResult:
    validate_output_dir(out_dir)
    motion_manifest_path = resolve_motion_record_manifest(motion_record)
    g1_track_manifest_path = resolve_g1_track_manifest(g1_track)

    motion_manifest, smplx_frames = load_motion_record_frames(motion_manifest_path)
    g1_manifest, g1_frames = load_g1_track_frames(g1_track_manifest_path)
    if len(smplx_frames) != len(g1_frames):
        raise ValueError("SMPL-X and G1 tracks must have matching frame counts")

    smplx_surface_manifest_path: Path | None = None
    surface_manifest: dict[str, Any] | None = None
    surface_data: dict[str, Any] | None = None
    if smplx_surface is not None:
        smplx_surface_manifest_path = resolve_smplx_surface_manifest(smplx_surface)
        surface_manifest, surface_data = load_smplx_surface_layer(smplx_surface_manifest_path)
        surface_frames = surface_data["frames"]
        if len(surface_frames) != len(smplx_frames):
            raise ValueError("SMPL-X surface frame count must match the source motion record")

    key_frame, annotation_name, annotation_manifest, routine_review = _normalize_annotation_manifest(
        annotations_path,
        len(smplx_frames),
    )
    fixture_only = bool(motion_manifest.get("fixture_only") or g1_manifest.get("fixture_only"))
    fixture = build_fixture_from_smplx_frames(
        smplx_frames,
        g1_frames=g1_frames,
        key_frame=key_frame,
        fixture_only=fixture_only,
    )
    if routine_review is not None:
        fixture["routine_review"] = routine_review
    if surface_manifest is not None and surface_data is not None:
        surface_payload = {
            "track_id": "smplx",
            "label": _surface_label(surface_manifest),
            "surface_kind": surface_manifest.get("surface_kind"),
            "licensed_smplx_mesh": bool(surface_manifest.get("licensed_smplx_mesh", False)),
            "scoring_allowed": False,
            "frames": surface_data["frames"],
        }
        if isinstance(surface_data.get("faces"), list):
            surface_payload["faces"] = surface_data["faces"]
        fixture["surface_proxy"] = {
            **surface_payload,
        }

    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "index.html"
    manifest_path = out_dir / "manifest.json"
    html_path.write_text(render_demo_html(fixture), encoding="utf-8")

    surface_layers: dict[str, Any] = {}
    if surface_manifest is not None and smplx_surface_manifest_path is not None:
        surface_layers[_surface_layer_key(surface_manifest)] = {
            "role": surface_manifest.get("role"),
            "manifest": _relative_path(smplx_surface_manifest_path, manifest_path.parent),
            "surface_kind": surface_manifest.get("surface_kind"),
            "label": _surface_label(surface_manifest),
            "licensed_smplx_mesh": bool(surface_manifest.get("licensed_smplx_mesh", False)),
            "scoring_allowed": False,
        }

    manifest = {
        "schema": PLAYBACK_SCHEMA,
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
        "surface_layers": surface_layers,
        "annotations": _relative_path(annotations_path, manifest_path.parent) if annotations_path else None,
        "annotation_name": annotation_name,
        "frame_count": len(smplx_frames),
        "fps": motion_manifest.get("fps"),
        "timing": motion_manifest.get("timing"),
        "coordinates": motion_manifest.get("coordinates"),
        "contact": motion_manifest.get("contact"),
        "key_frame": key_frame,
        "scoring_source": "smplx",
        "feedback": fixture["feedback"],
        "routine_review": routine_review,
        "annotation_manifest": annotation_manifest,
        "reference_video_sync": _reference_video_sync(reference_video, reference_trim_start_seconds),
        "evidence": {
            "kind": "html_frame_payload",
            "rendered_tracks": ["smplx", "g1"],
            "rendered_surface_layers": list(surface_layers),
            "trajectory_joints": fixture["trajectory_joints"],
        },
    }
    _write_json(manifest_path, manifest)
    return TeachingPlaybackWriteResult(html_path=html_path, manifest_path=manifest_path)
