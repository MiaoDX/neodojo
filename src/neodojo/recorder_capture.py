from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import require_schema
from .g1_render import G1_MUJOCO_RENDER_BACKEND, G1_RENDER_SCHEMA
from .motion_contract import _relative_path, _write_json, validate_output_dir

RECORDER_CAPTURE_SCHEMA = "neodojo.recorder_capture.v1"
RECORDER_CAPTURE_BACKEND = "mujoco_offscreen_frame_recorder.v1"
RECORDER_CAPTURE_VIEWS = ("front", "side", "top")


@dataclass(frozen=True)
class RecorderCaptureWriteResult:
    manifest_path: Path
    checked_paths: list[Path]


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _resolve_manifest_path(path: Path, default_name: str) -> Path:
    return path if path.is_file() else path / default_name


def _resolve_artifact(manifest_path: Path, reference: str) -> Path:
    path = Path(reference)
    if path.is_absolute():
        return path
    return manifest_path.parent / path


def _require_nonblank(path: Path, label: str) -> None:
    if not path.exists():
        raise ValueError(f"{label} artifact is missing: {path}")
    if not path.read_bytes():
        raise ValueError(f"{label} artifact is blank: {path}")


def _load_mujoco_render(render: Path) -> tuple[Path, dict[str, Any], dict[str, Path]]:
    manifest_path = _resolve_manifest_path(render, "manifest.json")
    manifest = _load_json(manifest_path)
    require_schema(manifest, G1_RENDER_SCHEMA, "G1 MuJoCo render manifest")
    renderer = manifest.get("renderer")
    if not isinstance(renderer, dict) or renderer.get("backend") != G1_MUJOCO_RENDER_BACKEND:
        raise ValueError("simulator recorder capture requires a MuJoCo offscreen render manifest")
    if manifest.get("scoring_source") != "smplx":
        raise ValueError("simulator recorder input must keep SMPL-X as scoring_source")
    if manifest.get("g1_scoring_allowed"):
        raise ValueError("simulator recorder input cannot allow G1 scoring")
    if not manifest.get("nonblank_pixel_check"):
        raise ValueError("simulator recorder input must pass nonblank_pixel_check")

    frame_refs = manifest.get("frame_paths")
    if not isinstance(frame_refs, dict):
        raise ValueError("G1 MuJoCo render manifest must include frame_paths")
    missing_views = [view for view in RECORDER_CAPTURE_VIEWS if view not in frame_refs]
    if missing_views:
        raise ValueError(f"G1 MuJoCo render is missing recorder views: {', '.join(missing_views)}")

    nonblank_views = manifest.get("nonblank_views")
    if isinstance(nonblank_views, dict):
        blank_views = [view for view in RECORDER_CAPTURE_VIEWS if not nonblank_views.get(view)]
        if blank_views:
            raise ValueError(f"G1 MuJoCo render reports blank recorder views: {', '.join(blank_views)}")

    paths = {
        view: _resolve_artifact(manifest_path, str(frame_refs[view]))
        for view in RECORDER_CAPTURE_VIEWS
    }
    for view, path in paths.items():
        _require_nonblank(path, f"simulator recorder {view} frame")
    return manifest_path, manifest, paths


def write_simulator_recorder_capture(
    out_dir: Path,
    *,
    simulator_render: Path,
) -> RecorderCaptureWriteResult:
    validate_output_dir(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    render_manifest_path, render_manifest, frame_paths = _load_mujoco_render(simulator_render)
    renderer = render_manifest.get("renderer", {})

    def rel(path: Path) -> str:
        return _relative_path(path, manifest_path.parent)

    manifest = {
        "schema": RECORDER_CAPTURE_SCHEMA,
        "capture_kind": "simulator_offscreen_camera_capture",
        "backend": {
            "kind": RECORDER_CAPTURE_BACKEND,
            "source_renderer": renderer.get("backend"),
            "source_command": "neodojo render mujoco-g1",
            "role": "direct simulator offscreen frame recorder evidence",
        },
        "source_render": rel(render_manifest_path),
        "fixture_only": bool(render_manifest.get("fixture_only")),
        "frame_count": int(render_manifest.get("frame_count", 0)),
        "selected_frame": int(render_manifest.get("selected_frame", 0)),
        "timing": render_manifest.get("timing"),
        "resolution": renderer.get("resolution"),
        "camera_captures": {
            view: {
                "camera_role": f"{view}_simulator_offscreen_recorder",
                "artifact": rel(path),
                "source_camera": (render_manifest.get("camera_definitions") or {}).get(view),
                "nonblank": True,
            }
            for view, path in frame_paths.items()
        },
        "real_browser_capture": False,
        "real_offscreen_recorder": True,
        "real_simulator_recorder": True,
        "real_roboharness_integration": False,
        "verification": {
            "required_views": list(RECORDER_CAPTURE_VIEWS),
            "nonblank_artifact_count": len(frame_paths),
            "source_nonblank_pixel_check": True,
        },
        "scoring_source": "smplx",
        "g1_scoring_allowed": False,
        "notes": (
            "Recorder evidence is derived from the selected MuJoCo offscreen "
            "render output. It is direct simulator capture evidence, not a "
            "roboharness integration and not a scoring source."
        ),
    }
    _write_json(manifest_path, manifest)
    return RecorderCaptureWriteResult(manifest_path=manifest_path, checked_paths=list(frame_paths.values()))
