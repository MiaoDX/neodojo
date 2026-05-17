from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import require_schema
from .fixtures import BONES, TRAJECTORY_JOINTS
from .g1_visual import ROBOT_MODEL_SCHEMA, SUPPORTED_ROBOT, load_g1_track_frames, resolve_g1_track_manifest
from .motion_contract import _relative_path, _write_json, validate_output_dir

G1_RENDER_SCHEMA = "neodojo.g1_render.v1"
G1_RENDER_BACKEND = "neodojo_svg_schematic.v1"


@dataclass(frozen=True)
class G1RenderWriteResult:
    html_path: Path
    manifest_path: Path
    frame_paths: dict[str, Path]


def _load_model_descriptor(path: Path, *, allow_fixture_model: bool) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"G1 model descriptor does not exist: {path}")

    descriptor = json.loads(path.read_text(encoding="utf-8"))
    require_schema(descriptor, ROBOT_MODEL_SCHEMA, "G1 model descriptor")
    if descriptor.get("robot") != SUPPORTED_ROBOT:
        raise ValueError("only Unitree G1 descriptors are supported")
    if not descriptor.get("validation", {}).get("loadable"):
        raise ValueError("G1 model descriptor is not marked loadable")
    if descriptor.get("fixture_only") and not allow_fixture_model:
        raise ValueError("fixture G1 model descriptors require --allow-fixture-model")
    return descriptor


def _project(point: list[float], view: str) -> tuple[float, float]:
    x, y, z = point
    if view == "front":
        return x, y
    if view == "side":
        return z, y
    if view == "top":
        return x, z
    raise ValueError(f"unsupported view: {view}")


def _bounds(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), max(xs), min(ys), max(ys)


def _scale(point: tuple[float, float], bounds: tuple[float, float, float, float]) -> tuple[float, float]:
    min_x, max_x, min_y, max_y = bounds
    width = max(max_x - min_x, 0.1)
    height = max(max_y - min_y, 0.1)
    scale = min(360 / width, 260 / height)
    x = 220 + (point[0] - ((min_x + max_x) / 2)) * scale
    y = 170 - (point[1] - ((min_y + max_y) / 2)) * scale
    return x, y


def _trajectory_path(frames: list[dict[str, list[float]]], joint: str, view: str) -> list[tuple[float, float]]:
    return [_project(frame[joint], view) for frame in frames if joint in frame]


def _render_polyline(points: list[tuple[float, float]], bounds: tuple[float, float, float, float]) -> str:
    if len(points) < 2:
        return ""
    scaled = [_scale(point, bounds) for point in points]
    payload = " ".join(f"{x:.1f},{y:.1f}" for x, y in scaled)
    return f'<polyline points="{payload}" fill="none" stroke="#2c6fbb" stroke-width="2" opacity="0.28"/>'


def _render_svg(
    *,
    view: str,
    model_descriptor: dict[str, Any],
    track_manifest: dict[str, Any],
    frames: list[dict[str, list[float]]],
    frame_index: int,
) -> str:
    frame = frames[frame_index]
    projected = [_project(point, view) for point in frame.values()]
    trajectory_points = [
        point
        for joint in TRAJECTORY_JOINTS
        for point in _trajectory_path(frames, joint, view)
    ]
    bounds = _bounds(projected + trajectory_points)

    lines = []
    for start, end in BONES:
        if start not in frame or end not in frame:
            continue
        x1, y1 = _scale(_project(frame[start], view), bounds)
        x2, y2 = _scale(_project(frame[end], view), bounds)
        lines.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            'stroke="#17212b" stroke-width="5" stroke-linecap="round"/>'
        )

    trajectories = [
        _render_polyline(_trajectory_path(frames, joint, view), bounds)
        for joint in TRAJECTORY_JOINTS
    ]
    joints = []
    for name, point in frame.items():
        x, y = _scale(_project(point, view), bounds)
        radius = 6 if name in {"pelvis", "spine", "neck", "head"} else 4
        joints.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="#b84e32"/>')

    fixture_label = "fixture model" if model_descriptor.get("fixture_only") else "registered model"
    track_label = "fixture track" if track_manifest.get("fixture_only") else "imported track"
    title = f"{view} view - {fixture_label}, {track_label}"
    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="640" viewBox="0 0 440 340" role="img">',
            "<style>text{font-family:Inter,Arial,sans-serif}.muted{fill:#66717f;font-size:12px}.title{fill:#17212b;font-size:15px;font-weight:700}</style>",
            '<rect width="440" height="340" fill="#fbfcfe"/>',
            '<rect x="12" y="12" width="416" height="316" rx="8" fill="none" stroke="#d8e0e8"/>',
            f'<text x="24" y="36" class="title">{title}</text>',
            f'<text x="24" y="56" class="muted">frame {frame_index + 1} / {len(frames)} - backend {G1_RENDER_BACKEND}</text>',
            *trajectories,
            *lines,
            *joints,
            '<line x1="56" y1="294" x2="384" y2="294" stroke="#d8e0e8" stroke-width="2" stroke-dasharray="6 6"/>',
            "</svg>",
        ]
    )


def _render_html(manifest: dict[str, Any], frame_names: list[str]) -> str:
    cards = "\n".join(
        f'<section><h2>{name.title()}</h2><img src="{name}.svg" alt="{name} G1 render evidence"></section>'
        for name in frame_names
    )
    fixture_note = "fixture-only" if manifest["fixture_only"] else "registered-model"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>neodojo G1 render evidence</title>
  <style>
    body {{ margin: 0; background: #eef2f6; color: #17212b; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
    header {{ display: flex; justify-content: space-between; gap: 16px; align-items: center; padding: 18px 20px; background: #fff; border-bottom: 1px solid #d8e0e8; }}
    h1 {{ margin: 0; font-size: 18px; }}
    .badge {{ border: 1px solid #d8e0e8; border-radius: 999px; padding: 6px 10px; color: #66717f; font-size: 12px; font-weight: 700; }}
    main {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; padding: 14px; }}
    section {{ min-width: 0; background: #fff; border: 1px solid #d8e0e8; border-radius: 8px; overflow: hidden; }}
    h2 {{ margin: 0; padding: 10px 12px; font-size: 14px; border-bottom: 1px solid #d8e0e8; }}
    img {{ display: block; width: 100%; background: #fbfcfe; }}
    footer {{ padding: 0 20px 18px; color: #66717f; font-size: 13px; }}
    @media (max-width: 900px) {{ main {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <header>
    <h1>neodojo G1 render evidence</h1>
    <div class="badge">{fixture_note}</div>
  </header>
  <main>
    {cards}
  </main>
  <footer>
    Renderer: {manifest["renderer"]["backend"]}. Scoring source remains SMPL-X; G1 scoring allowed is false.
  </footer>
</body>
</html>
"""


def write_g1_render(
    out_dir: Path,
    *,
    model_descriptor_path: Path,
    g1_track: Path,
    allow_fixture_model: bool = False,
) -> G1RenderWriteResult:
    validate_output_dir(out_dir)
    model_descriptor = _load_model_descriptor(model_descriptor_path, allow_fixture_model=allow_fixture_model)
    g1_track_manifest_path = resolve_g1_track_manifest(g1_track)
    g1_manifest, frames = load_g1_track_frames(g1_track_manifest_path)
    frame_index = len(frames) // 2

    frame_dir = out_dir / "frames"
    frame_paths = {
        view: frame_dir / f"{view}.svg"
        for view in ("front", "side", "top")
    }
    for view, path in frame_paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            _render_svg(
                view=view,
                model_descriptor=model_descriptor,
                track_manifest=g1_manifest,
                frames=frames,
                frame_index=frame_index,
            ),
            encoding="utf-8",
        )

    manifest_path = out_dir / "manifest.json"
    html_path = out_dir / "index.html"
    fixture_only = bool(model_descriptor.get("fixture_only") or g1_manifest.get("fixture_only"))
    manifest = {
        "schema": G1_RENDER_SCHEMA,
        "fixture_only": fixture_only,
        "renderer": {
            "backend": G1_RENDER_BACKEND,
            "role": "local SVG frame evidence; not MuJoCo/Genesis simulator rendering",
        },
        "robot": SUPPORTED_ROBOT,
        "model_descriptor": _relative_path(model_descriptor_path, manifest_path.parent),
        "model_fixture_only": bool(model_descriptor.get("fixture_only")),
        "model_format": model_descriptor.get("model_format"),
        "model_root_name": model_descriptor.get("root_name"),
        "model_joint_count": model_descriptor.get("joint_count"),
        "g1_track": _relative_path(g1_track_manifest_path, manifest_path.parent),
        "track_fixture_only": bool(g1_manifest.get("fixture_only")),
        "pose_stream": g1_manifest.get("derivation", "unknown"),
        "frame_count": len(frames),
        "timing": g1_manifest.get("timing"),
        "coordinates": g1_manifest.get("coordinates"),
        "contact": g1_manifest.get("contact"),
        "selected_frame": frame_index,
        "camera_definitions": {
            "front": {"projection_axes": ["x", "y"]},
            "side": {"projection_axes": ["z", "y"]},
            "top": {"projection_axes": ["x", "z"]},
        },
        "frame_paths": {
            view: _relative_path(path, manifest_path.parent)
            for view, path in frame_paths.items()
        },
        "html": _relative_path(html_path, manifest_path.parent),
        "scoring_source": "smplx",
        "g1_scoring_allowed": False,
    }
    _write_json(manifest_path, manifest)
    html_path.write_text(_render_html(manifest, list(frame_paths)), encoding="utf-8")
    return G1RenderWriteResult(html_path=html_path, manifest_path=manifest_path, frame_paths=frame_paths)
