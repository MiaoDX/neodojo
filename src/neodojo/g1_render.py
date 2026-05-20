from __future__ import annotations

import json
import binascii
import html
import os
import shutil
import struct
import subprocess
import sys
import time
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import require_schema
from .fixtures import BONES, TRAJECTORY_JOINTS
from .g1_visual import ROBOT_MODEL_SCHEMA, SUPPORTED_ROBOT, load_g1_track_frames, resolve_g1_track_manifest
from .motion_contract import _relative_path, _write_json, validate_output_dir

G1_RENDER_SCHEMA = "neodojo.g1_render.v1"
G1_RENDER_BACKEND = "neodojo_svg_schematic.v1"
G1_MUJOCO_RENDER_BACKEND = "mujoco_python_offscreen.v1"
G1_ROBOHARNESS_REPORT_BACKEND = "roboharness_checkpoint_report.v1"
G1_MUJOCO_BACKEND_COMPARISON_SCHEMA = "neodojo.g1_mujoco_backend_comparison.v1"
G1_MUJOCO_BACKEND_BENCHMARK_SCHEMA = "neodojo.g1_mujoco_backend_benchmark.v1"
G1_MUJOCO_VISUAL_THEME = "roboharness_g1_reach_scene_v1"
DEFAULT_G1_REPLAY_FPS = 5.0
G1_MUJOCO_SCENE_STYLE = {
    "skybox": "builtin gradient rgb1=0.6 0.8 1.0 rgb2=0.2 0.3 0.5",
    "ground": "mujoco checker texture rgb1=0.85 0.85 0.85 rgb2=0.65 0.65 0.65 texrepeat=8 8",
    "lighting": "roboharness g1_reach two-light setup with MuJoCo headlight",
    "cameras": ["front", "side", "top", "close_up"],
    "props": "qigong replay omits reach-task table and targets",
}


@dataclass(frozen=True)
class G1RenderWriteResult:
    html_path: Path
    manifest_path: Path
    frame_paths: dict[str, Path]


@dataclass(frozen=True)
class G1MujocoBackendComparisonResult:
    html_path: Path
    manifest_path: Path
    backend_results: list[dict[str, Any]]


@dataclass(frozen=True)
class G1MujocoBackendBenchmarkResult:
    markdown_path: Path
    manifest_path: Path
    backend_summaries: list[dict[str, Any]]


@dataclass(frozen=True)
class G1RoboharnessReportResult:
    html_path: Path
    manifest_path: Path
    stage_paths: dict[str, dict[str, Path]]


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


def _render_image_html(manifest: dict[str, Any], frame_paths: dict[str, Path]) -> str:
    cards = "\n".join(
        f'<section><h2>{name.title()}</h2><img src="frames/{path.name}" alt="{name} G1 simulator render"></section>'
        for name, path in frame_paths.items()
    )
    pose_source = manifest.get("pose_application", {}).get("source")
    pose_note = (
        "Imported GMR joint-angle pose evidence"
        if pose_source == "imported_gmr_joint_angles"
        else "Neutral-pose simulator mesh evidence"
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>neodojo G1 MuJoCo render evidence</title>
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
    <h1>neodojo G1 MuJoCo render evidence</h1>
    <div class="badge">registered model</div>
  </header>
  <main>
    {cards}
  </main>
  <footer>
    Renderer: {manifest["renderer"]["backend"]}. {pose_note}; scoring source remains SMPL-X.
  </footer>
</body>
</html>
"""


def _truncate_text(value: str, limit: int = 2400) -> str:
    if len(value) <= limit:
        return value
    return value[-limit:]


def _xvfb_prefix_for_backend(backend: str, mode: str, env: dict[str, str]) -> list[str]:
    if backend != "glfw":
        return []
    if mode == "never":
        return []
    if mode == "always":
        xvfb = shutil.which("xvfb-run")
        if xvfb is None:
            raise ValueError("--xvfb-glfw=always requires xvfb-run on PATH")
        return [xvfb, "-a"]
    if mode != "auto":
        raise ValueError("xvfb_glfw must be one of: auto, always, never")
    if env.get("DISPLAY"):
        return []
    xvfb = shutil.which("xvfb-run")
    return [xvfb, "-a"] if xvfb else []


def _safe_mujoco_backend_name(backend: str) -> str:
    backend_name = backend.strip()
    if not backend_name:
        raise ValueError("backend names must be non-empty")
    if "/" in backend_name or "\\" in backend_name or backend_name in {".", ".."}:
        raise ValueError(f"backend name is not safe for an output directory: {backend_name}")
    return backend_name


def _run_mujoco_backend_render(
    *,
    backend_name: str,
    out_dir: Path,
    relative_start: Path,
    model_descriptor_path: Path,
    g1_track: Path,
    allow_fixture_model: bool,
    width: int,
    height: int,
    xvfb_glfw: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    env = os.environ.copy()
    env["MUJOCO_GL"] = backend_name
    if backend_name == "osmesa":
        env.setdefault("PYOPENGL_PLATFORM", "osmesa")
    command = [
        sys.executable,
        "-m",
        "neodojo",
        "render",
        "mujoco-g1",
        "--model-descriptor",
        str(model_descriptor_path),
        "--g1-track",
        str(g1_track),
        "--width",
        str(width),
        "--height",
        str(height),
        "--out",
        str(out_dir),
    ]
    if allow_fixture_model:
        command.append("--allow-fixture-model")
    command_prefix = _xvfb_prefix_for_backend(backend_name, xvfb_glfw, env)
    run_command = [*command_prefix, *command]
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            run_command,
            check=False,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout_seconds,
        )
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        returncode = -1
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        stderr = f"timed out after {timeout_seconds}s\n{stderr}"
    elapsed = time.perf_counter() - started
    render_manifest_path = out_dir / "manifest.json"
    item: dict[str, Any] = {
        "backend": backend_name,
        "status": "rendered" if returncode == 0 and render_manifest_path.exists() else "failed",
        "elapsed_seconds": round(elapsed, 3),
        "returncode": returncode,
        "command": run_command,
        "env": {
            "MUJOCO_GL": env.get("MUJOCO_GL"),
            "PYOPENGL_PLATFORM": env.get("PYOPENGL_PLATFORM"),
            "DISPLAY": env.get("DISPLAY"),
        },
        "stdout_tail": _truncate_text(stdout),
        "stderr_tail": _truncate_text(stderr),
    }
    if item["status"] == "rendered":
        render_manifest = json.loads(render_manifest_path.read_text(encoding="utf-8"))
        frame_paths = {}
        for view, relative in render_manifest.get("frame_paths", {}).items():
            if isinstance(relative, str):
                frame_paths[view] = _relative_path(render_manifest_path.parent / relative, relative_start)
        item.update(
            {
                "manifest": _relative_path(render_manifest_path, relative_start),
                "html": _relative_path(out_dir / "index.html", relative_start),
                "renderer": render_manifest.get("renderer"),
                "pose_application": render_manifest.get("pose_application"),
                "nonblank_views": render_manifest.get("nonblank_views"),
                "actual_g1_model_replay": bool(render_manifest.get("actual_g1_model_replay")),
                "frame_paths": frame_paths,
            }
        )
    return item


def _render_backend_comparison_html(manifest: dict[str, Any]) -> str:
    cards = []
    for item in manifest["backend_results"]:
        backend = html.escape(str(item["backend"]))
        status = html.escape(str(item["status"]))
        elapsed = f'{float(item.get("elapsed_seconds", 0.0)):.2f}s'
        renderer = item.get("renderer")
        resolution = renderer.get("resolution") if isinstance(renderer, dict) else None
        resolution_label = (
            f'{resolution.get("width")}x{resolution.get("height")}'
            if isinstance(resolution, dict)
            else "unavailable"
        )
        images = ""
        frame_paths = item.get("frame_paths") if isinstance(item.get("frame_paths"), dict) else {}
        for view in ("front", "side", "top"):
            path = frame_paths.get(view)
            if isinstance(path, str) and path:
                images += (
                    f'<figure><img src="{html.escape(path)}" alt="{backend} {view} render">'
                    f"<figcaption>{view}</figcaption></figure>"
                )
        stderr = html.escape(str(item.get("stderr_tail") or ""))
        stdout = html.escape(str(item.get("stdout_tail") or ""))
        output = ""
        if stderr or stdout:
            output = f"<pre>{stderr or stdout}</pre>"
        cards.append(
            f"""<section class="backend {status}">
      <header>
        <h2>{backend}</h2>
        <span>{status}</span>
      </header>
      <dl>
        <div><dt>Elapsed</dt><dd>{elapsed}</dd></div>
        <div><dt>Resolution</dt><dd>{html.escape(resolution_label)}</dd></div>
        <div><dt>Return code</dt><dd>{html.escape(str(item.get("returncode")))}</dd></div>
      </dl>
      <div class="frames">{images or '<p class="empty">No rendered frames</p>'}</div>
      {output}
    </section>"""
        )
    backend_labels = ", ".join(html.escape(str(item["backend"])) for item in manifest["backend_results"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>neodojo MuJoCo GL backend comparison</title>
  <style>
    body {{ margin: 0; background: #f4f6f8; color: #17212b; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
    body > header {{ padding: 18px 20px; background: #fff; border-bottom: 1px solid #d8e0e8; }}
    h1 {{ margin: 0 0 6px; font-size: 20px; }}
    p {{ margin: 0; color: #66717f; font-size: 13px; line-height: 1.5; }}
    main {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; padding: 14px; }}
    .backend {{ min-width: 0; background: #fff; border: 1px solid #d8e0e8; border-radius: 8px; overflow: hidden; }}
    .backend > header {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 14px; border-bottom: 1px solid #d8e0e8; }}
    h2 {{ margin: 0; font-size: 16px; }}
    span {{ border: 1px solid #d8e0e8; border-radius: 999px; padding: 4px 8px; color: #66717f; font-size: 12px; font-weight: 700; }}
    .rendered span {{ color: #17663a; border-color: #abd6bd; background: #edf8f1; }}
    .failed span {{ color: #8c2f24; border-color: #e2b8b2; background: #fff0ee; }}
    dl {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1px; margin: 0; background: #d8e0e8; border-bottom: 1px solid #d8e0e8; }}
    dl div {{ background: #fbfcfe; padding: 8px 10px; }}
    dt {{ color: #66717f; font-size: 11px; font-weight: 700; text-transform: uppercase; }}
    dd {{ margin: 2px 0 0; font-size: 13px; }}
    .frames {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1px; background: #d8e0e8; }}
    figure {{ margin: 0; background: #fbfcfe; }}
    img {{ display: block; width: 100%; background: #fff; }}
    figcaption {{ padding: 6px 8px; color: #66717f; font-size: 12px; text-transform: capitalize; }}
    .empty {{ padding: 14px; }}
    pre {{ margin: 0; max-height: 260px; overflow: auto; padding: 12px 14px; background: #17212b; color: #f8fafc; font-size: 12px; line-height: 1.45; white-space: pre-wrap; }}
    footer {{ padding: 0 20px 18px; color: #66717f; font-size: 13px; }}
  </style>
</head>
<body>
  <header>
    <h1>MuJoCo GL backend comparison</h1>
    <p>Backends: {backend_labels}. Compare visible output, elapsed time, and backend setup errors from the same model, track, camera, and resolution.</p>
  </header>
  <main>
    {"".join(cards)}
  </main>
  <footer>
    Minor pixel-level differences can come from OpenGL drivers and anti-aliasing. Use this page for manual picking; exact PNG hashes are not expected to match across backends.
  </footer>
</body>
</html>
"""


def _mujoco_pose_application_for_frame(
    mujoco: Any,
    model: Any,
    data: Any,
    *,
    joint_angle_frames: list[dict[str, float]],
    joint_angle_names: list[str],
    frame_index: int,
) -> dict[str, Any]:
    data.qpos[:] = model.qpos0
    if not joint_angle_frames:
        mujoco.mj_forward(model, data)
        return {
            "source": "neutral_qpos",
            "selected_frame": frame_index,
            "joint_angle_count": 0,
            "applied_joint_count": 0,
            "missing_joint_count": 0,
            "skipped_joint_count": 0,
            "clipped_joint_count": 0,
            "notes": "No imported GMR joint-angle stream was found; rendered the model neutral qpos.",
        }

    application = _apply_mujoco_joint_angles(
        mujoco,
        model,
        data,
        joint_angle_frames[frame_index],
    )
    mujoco.mj_forward(model, data)
    return {
        "source": "imported_gmr_joint_angles",
        "selected_frame": frame_index,
        "joint_angle_count": len(joint_angle_names),
        "notes": "Applied matching imported GMR joint angles to MuJoCo qpos; unmatched or unsupported joints remain at model defaults.",
        **application,
    }


def _roboharness_scene_xml(model_path: Path, *, width: int = 640, height: int = 480) -> str:
    """Build the same visual scene style used by roboharness G1 reach reports."""
    model_path = model_path.resolve()
    mesh_dir = model_path.parent / "assets"
    mesh_dir_attr = html.escape(str(mesh_dir), quote=True)
    model_path_attr = html.escape(str(model_path), quote=True)
    return f"""\
<mujoco model="neodojo_g1_roboharness_scene">
  <include file="{model_path_attr}"/>

  <option gravity="0 0 -9.81" timestep="0.002"/>
  <compiler meshdir="{mesh_dir_attr}"/>

  <statistic center="0 0 0.8" extent="1.5"/>

  <visual>
    <global offwidth="{int(width)}" offheight="{int(height)}"/>
    <headlight diffuse="0.6 0.6 0.6" ambient="0.3 0.3 0.3" specular="0.5 0.5 0.5"/>
    <rgba haze="0.15 0.25 0.35 1"/>
  </visual>

  <asset>
    <texture type="skybox" builtin="gradient" rgb1="0.6 0.8 1.0" rgb2="0.2 0.3 0.5"
             width="256" height="256"/>
    <texture name="grid" type="2d" builtin="checker" rgb1="0.85 0.85 0.85" rgb2="0.65 0.65 0.65"
             width="256" height="256"/>
    <material name="grid_mat" texture="grid" texrepeat="8 8" reflectance="0.1"/>
  </asset>

  <worldbody>
    <geom name="floor" type="plane" size="3 3 0.05" material="grid_mat"/>
    <light pos="1 1 3" dir="-0.3 -0.3 -1" diffuse="0.7 0.7 0.7"/>
    <light pos="-1 1 3" dir="0.3 -0.3 -1" diffuse="0.4 0.4 0.4"/>

    <camera name="front" pos="4.0 0 1.25" xyaxes="0 1 0 -0.15 0 1"/>
    <camera name="side" pos="0 4.0 1.25" xyaxes="-1 0 0 0 -0.15 1"/>
    <camera name="top" pos="0 0 4.5" xyaxes="1 0 0 0 1 0"/>
    <camera name="close_up" pos="1.2 0.5 1.2" xyaxes="-0.4 1 0 -0.2 -0.1 1"/>
  </worldbody>
</mujoco>
"""


def _load_mujoco_model_for_render(
    mujoco: Any,
    model_path: Path,
    *,
    model_format: str | None,
    width: int,
    height: int,
) -> tuple[Any, dict[str, Any]]:
    if model_format == "mjcf":
        scene_xml = _roboharness_scene_xml(model_path, width=width, height=height)
        try:
            model = mujoco.MjModel.from_xml_string(scene_xml)
        except Exception as exc:
            raise ValueError(f"failed to load roboharness-style G1 scene with MuJoCo: {exc}") from exc
        return model, {
            "theme": G1_MUJOCO_VISUAL_THEME,
            **G1_MUJOCO_SCENE_STYLE,
        }

    try:
        model = mujoco.MjModel.from_xml_path(str(model_path))
    except Exception as exc:
        raise ValueError(f"failed to load model with MuJoCo: {exc}") from exc
    return model, {
        "theme": "direct_model_scene_fallback",
        "notes": "non-MJCF descriptors are rendered without the roboharness wrapper scene",
    }


def _positive_float(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a positive number")
    number = float(value)
    if number <= 0:
        raise ValueError(f"{label} must be positive")
    return number


def _g1_track_fps(g1_manifest: dict[str, Any]) -> float:
    if g1_manifest.get("fps") is not None:
        return _positive_float(g1_manifest["fps"], "G1 track fps")
    timing = g1_manifest.get("timing")
    if isinstance(timing, dict) and timing.get("fps") is not None:
        return _positive_float(timing["fps"], "G1 track timing fps")
    return 25.0


def _sample_replay_frame_indices(frame_count: int, *, source_fps: float, replay_fps: float | None) -> list[int]:
    if frame_count <= 0:
        return []
    source_fps = _positive_float(source_fps, "source_fps")
    if replay_fps is None or replay_fps >= source_fps:
        return list(range(frame_count))
    replay_fps = _positive_float(replay_fps, "replay_fps")
    duration_seconds = frame_count / source_fps
    sample_count = max(1, round(duration_seconds * replay_fps))
    indices: list[int] = []
    for sample_index in range(sample_count):
        source_frame = min(frame_count - 1, round(sample_index * source_fps / replay_fps))
        if indices and source_frame <= indices[-1]:
            source_frame = min(frame_count - 1, indices[-1] + 1)
        if not indices or source_frame != indices[-1]:
            indices.append(source_frame)
    return indices


def _render_mujoco_replay_sequence(
    *,
    mujoco: Any,
    model: Any,
    data: Any,
    renderer: Any,
    frame_dir: Path,
    joint_angle_frames: list[dict[str, float]],
    joint_angle_names: list[str],
    source_fps: float,
    replay_fps: float | None,
) -> dict[str, Any]:
    source_fps = _positive_float(source_fps, "source_fps")
    requested_replay_fps = None if replay_fps is None else _positive_float(replay_fps, "replay_fps")
    if not joint_angle_frames:
        return {
            "available": False,
            "actual_g1_model_replay": False,
            "view": "front",
            "source_fps": source_fps,
            "replay_fps": requested_replay_fps or source_fps,
            "source_frame_count": 0,
            "source_frame_indices": [],
            "background": "roboharness_skybox",
            "ground": "roboharness_checker_floor",
            "frame_count": 0,
            "paths": [],
            "nonblank_frame_count": 0,
            "nonblank_pixel_check": False,
            "changed_frame_pair_count": 0,
            "changed_frame_check": False,
            "pose_source": "neutral_qpos",
            "applied_joint_count_min": 0,
            "missing_joint_count_max": 0,
            "skipped_joint_count_max": 0,
        }

    camera = _camera_for_view(mujoco, model, "front")
    replay_dir = frame_dir / "replay"
    source_frame_indices = _sample_replay_frame_indices(
        len(joint_angle_frames),
        source_fps=source_fps,
        replay_fps=requested_replay_fps,
    )
    paths: list[Path] = []
    nonblank_checks: list[bool] = []
    changed_checks: list[bool] = []
    applied_counts: list[int] = []
    missing_counts: list[int] = []
    skipped_counts: list[int] = []
    previous_pixels: bytes | None = None

    for replay_index, frame_index in enumerate(source_frame_indices):
        application = _mujoco_pose_application_for_frame(
            mujoco,
            model,
            data,
            joint_angle_frames=joint_angle_frames,
            joint_angle_names=joint_angle_names,
            frame_index=frame_index,
        )
        rgb = _render_mujoco_rgb(renderer, data, camera)
        signature = rgb.tobytes()
        if previous_pixels is not None:
            changed_checks.append(signature != previous_pixels)
        previous_pixels = signature
        nonblank_checks.append(bool(rgb.max() > rgb.min()))
        applied_counts.append(int(application.get("applied_joint_count", 0)))
        missing_counts.append(int(application.get("missing_joint_count", 0)))
        skipped_counts.append(int(application.get("skipped_joint_count", 0)))
        path = replay_dir / f"front-{replay_index:06d}.png"
        _write_rgb_png(path, rgb)
        paths.append(path)

    return {
        "available": True,
        "actual_g1_model_replay": bool(
            len(paths) == len(source_frame_indices)
            and all(nonblank_checks)
            and any(changed_checks)
            and bool(applied_counts)
            and min(applied_counts) > 0
        ),
        "view": "front",
        "source_fps": source_fps,
        "replay_fps": requested_replay_fps or source_fps,
        "source_frame_count": len(joint_angle_frames),
        "source_frame_indices": source_frame_indices,
        "background": "roboharness_skybox",
        "ground": "roboharness_checker_floor",
        "visual_style": "mujoco-png-frame-sequence.v1",
        "frame_count": len(paths),
        "paths": paths,
        "nonblank_frame_count": sum(1 for check in nonblank_checks if check),
        "nonblank_pixel_check": all(nonblank_checks),
        "changed_frame_pair_count": sum(1 for check in changed_checks if check),
        "changed_frame_check": any(changed_checks),
        "pose_source": "imported_gmr_joint_angles",
        "joint_angle_count": len(joint_angle_names),
        "applied_joint_count_min": min(applied_counts) if applied_counts else 0,
        "applied_joint_count_max": max(applied_counts) if applied_counts else 0,
        "missing_joint_count_max": max(missing_counts) if missing_counts else 0,
        "skipped_joint_count_max": max(skipped_counts) if skipped_counts else 0,
    }


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    )


def _write_rgb_png(path: Path, pixels: Any) -> None:
    rgb = pixels[..., :3]
    height = int(rgb.shape[0])
    width = int(rgb.shape[1])
    raw = b"".join(b"\x00" + rgb[row].astype("uint8").tobytes() for row in range(height))
    payload = b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            _png_chunk(b"IDAT", zlib.compress(raw)),
            _png_chunk(b"IEND", b""),
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _render_mujoco_rgb(renderer: Any, data: Any, camera: Any) -> Any:
    renderer.update_scene(data, camera=camera)
    return renderer.render()[..., :3].copy()


def _load_mujoco() -> Any:
    try:
        import mujoco
    except ModuleNotFoundError as exc:
        raise ValueError(
            "MuJoCo rendering requires the optional mujoco package; install with "
            "`python -m pip install '.[sim]'` or `python -m pip install mujoco`"
        ) from exc
    return mujoco


def _camera_for_view(mujoco: Any, model: Any, view: str) -> Any:
    camera_id = int(mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, view))
    if camera_id >= 0:
        return view

    camera = mujoco.MjvCamera()
    mujoco.mjv_defaultFreeCamera(model, camera)
    try:
        camera.lookat[:] = model.stat.center
    except AttributeError:
        camera.lookat[:] = [0.0, 0.0, 0.6]
    camera.distance = max(float(model.stat.extent) * 2.2, 1.5)
    if view == "front":
        camera.azimuth = 180
        camera.elevation = -15
    elif view == "side":
        camera.azimuth = 90
        camera.elevation = -15
    elif view == "top":
        camera.azimuth = 0
        camera.elevation = -90
    else:
        raise ValueError(f"unsupported view: {view}")
    return camera


def _load_g1_joint_angle_frames(
    track_manifest_path: Path,
    track_manifest: dict[str, Any],
    *,
    expected_frame_count: int,
) -> tuple[list[dict[str, float]], list[str]]:
    pose_stream = track_manifest.get("pose_stream")
    if not isinstance(pose_stream, dict) or pose_stream.get("kind") != "unitree_g1_joint_angles":
        return [], []

    data_file = track_manifest.get("data_files", {}).get("frames")
    if not data_file:
        raise ValueError("G1 track manifest is missing data_files.frames")
    data_path = track_manifest_path.parent / data_file
    data = json.loads(data_path.read_text(encoding="utf-8"))

    raw_frames = data.get("joint_angles")
    if not isinstance(raw_frames, list) or len(raw_frames) != expected_frame_count:
        raise ValueError("GMR G1 joint-angle frame count must match visual frame count")

    joint_names = data.get("joint_angle_names")
    if not isinstance(joint_names, list) or not all(isinstance(name, str) and name for name in joint_names):
        joint_names = sorted(raw_frames[0]) if raw_frames and isinstance(raw_frames[0], dict) else []

    angle_frames: list[dict[str, float]] = []
    expected_names = sorted(joint_names)
    for frame_index, raw_frame in enumerate(raw_frames):
        if not isinstance(raw_frame, dict):
            raise ValueError(f"GMR G1 joint-angle frame {frame_index} must be an object")
        normalized: dict[str, float] = {}
        for joint, value in raw_frame.items():
            if not isinstance(joint, str) or not joint:
                raise ValueError(f"GMR G1 joint-angle frame {frame_index} contains an invalid joint name")
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"GMR G1 joint angle {joint} at frame {frame_index} must be numeric")
            normalized[joint] = float(value)
        if sorted(normalized) != expected_names:
            raise ValueError(f"GMR G1 joint-angle keys changed at frame {frame_index}")
        angle_frames.append(normalized)

    return angle_frames, expected_names


def _apply_mujoco_joint_angles(
    mujoco: Any,
    model: Any,
    data: Any,
    joint_angles: dict[str, float],
) -> dict[str, Any]:
    hinge_type = int(mujoco.mjtJoint.mjJNT_HINGE)
    slide_type = int(mujoco.mjtJoint.mjJNT_SLIDE)
    supported_types = {hinge_type, slide_type}

    applied: dict[str, float] = {}
    missing: list[str] = []
    skipped: dict[str, str] = {}
    clipped: dict[str, dict[str, float]] = {}

    for joint_name, raw_value in sorted(joint_angles.items()):
        joint_id = int(mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name))
        if joint_id < 0:
            missing.append(joint_name)
            continue

        joint_type = int(model.jnt_type[joint_id])
        if joint_type not in supported_types:
            skipped[joint_name] = f"unsupported_mujoco_joint_type:{joint_type}"
            continue

        value = float(raw_value)
        if bool(model.jnt_limited[joint_id]):
            lower = float(model.jnt_range[joint_id][0])
            upper = float(model.jnt_range[joint_id][1])
            clipped_value = min(max(value, lower), upper)
            if clipped_value != value:
                clipped[joint_name] = {
                    "requested": round(value, 6),
                    "applied": round(clipped_value, 6),
                    "lower": round(lower, 6),
                    "upper": round(upper, 6),
                }
                value = clipped_value

        qpos_address = int(model.jnt_qposadr[joint_id])
        data.qpos[qpos_address] = value
        applied[joint_name] = round(value, 6)

    return {
        "applied_joints": sorted(applied),
        "applied_joint_values": applied,
        "missing_joints": missing,
        "skipped_joints": skipped,
        "clipped_joints": clipped,
        "applied_joint_count": len(applied),
        "missing_joint_count": len(missing),
        "skipped_joint_count": len(skipped),
        "clipped_joint_count": len(clipped),
    }


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


def write_g1_mujoco_render(
    out_dir: Path,
    *,
    model_descriptor_path: Path,
    g1_track: Path,
    allow_fixture_model: bool = False,
    width: int = 640,
    height: int = 480,
    replay_fps: float | None = DEFAULT_G1_REPLAY_FPS,
) -> G1RenderWriteResult:
    if width <= 0 or height <= 0:
        raise ValueError("MuJoCo render width and height must be positive")
    validate_output_dir(out_dir)
    model_descriptor = _load_model_descriptor(model_descriptor_path, allow_fixture_model=allow_fixture_model)
    if model_descriptor.get("fixture_only"):
        raise ValueError("MuJoCo render evidence requires a registered URDF/MJCF model descriptor")
    if model_descriptor.get("model_format") not in {"mjcf", "urdf"}:
        raise ValueError("MuJoCo render evidence requires a URDF or MJCF model descriptor")

    model_path = Path(model_descriptor.get("resolved_model_path") or model_descriptor.get("model_path", ""))
    if not model_path.exists():
        raise ValueError(f"registered model path does not exist: {model_path}")

    g1_track_manifest_path = resolve_g1_track_manifest(g1_track)
    g1_manifest, frames = load_g1_track_frames(g1_track_manifest_path)
    source_fps = _g1_track_fps(g1_manifest)
    selected_frame = len(frames) // 2
    joint_angle_frames, joint_angle_names = _load_g1_joint_angle_frames(
        g1_track_manifest_path,
        g1_manifest,
        expected_frame_count=len(frames),
    )
    mujoco = _load_mujoco()
    model, visual_theme = _load_mujoco_model_for_render(
        mujoco,
        model_path,
        model_format=model_descriptor.get("model_format"),
        width=width,
        height=height,
    )
    try:
        model.vis.global_.offwidth = max(int(model.vis.global_.offwidth), width)
        model.vis.global_.offheight = max(int(model.vis.global_.offheight), height)
    except AttributeError:
        pass
    data = mujoco.MjData(model)
    pose_application = _mujoco_pose_application_for_frame(
        mujoco,
        model,
        data,
        joint_angle_frames=joint_angle_frames,
        joint_angle_names=joint_angle_names,
        frame_index=selected_frame,
    )

    frame_dir = out_dir / "frames"
    frame_paths = {
        view: frame_dir / f"{view}.png"
        for view in ("front", "side", "top")
    }
    renderer = mujoco.Renderer(model, height=height, width=width)
    nonblank_checks: dict[str, bool] = {}
    replay_sequence: dict[str, Any]
    try:
        for view, path in frame_paths.items():
            camera = _camera_for_view(mujoco, model, view)
            _mujoco_pose_application_for_frame(
                mujoco,
                model,
                data,
                joint_angle_frames=joint_angle_frames,
                joint_angle_names=joint_angle_names,
                frame_index=selected_frame,
            )
            pixels = _render_mujoco_rgb(renderer, data, camera)
            nonblank_checks[view] = bool(pixels.max() > pixels.min())
            _write_rgb_png(path, pixels)
        replay_sequence = _render_mujoco_replay_sequence(
            mujoco=mujoco,
            model=model,
            data=data,
            renderer=renderer,
            frame_dir=frame_dir,
            joint_angle_frames=joint_angle_frames,
            joint_angle_names=joint_angle_names,
            source_fps=source_fps,
            replay_fps=replay_fps,
        )
    finally:
        renderer.close()
    if not all(nonblank_checks.values()):
        raise ValueError(f"MuJoCo rendered blank views: {nonblank_checks}")

    actual_replay = bool(
        replay_sequence.get("actual_g1_model_replay")
        and not g1_manifest.get("fixture_only")
        and pose_application.get("source") == "imported_gmr_joint_angles"
    )

    manifest_path = out_dir / "manifest.json"
    html_path = out_dir / "index.html"
    manifest = {
        "schema": G1_RENDER_SCHEMA,
        "fixture_only": bool(g1_manifest.get("fixture_only")),
        "actual_g1_model_replay": actual_replay,
        "renderer": {
            "backend": G1_MUJOCO_RENDER_BACKEND,
            "role": (
                "MuJoCo offscreen G1 model frame-sequence replay"
                if actual_replay
                else "MuJoCo offscreen neutral/static mesh render evidence"
            ),
            "mujoco_version": getattr(mujoco, "__version__", None),
            "gl_backend": os.environ.get("MUJOCO_GL") or "mujoco_default",
            "resolution": {"width": width, "height": height},
            "replay_fps": replay_sequence.get("replay_fps"),
            "background": "roboharness_skybox",
            "ground": "roboharness_checker_floor",
            "visual_theme": visual_theme,
        },
        "robot": SUPPORTED_ROBOT,
        "model_descriptor": _relative_path(model_descriptor_path, manifest_path.parent),
        "model_fixture_only": False,
        "model_format": model_descriptor.get("model_format"),
        "model_root_name": model_descriptor.get("root_name"),
        "model_joint_count": model_descriptor.get("joint_count"),
        "g1_track": _relative_path(g1_track_manifest_path, manifest_path.parent),
        "track_fixture_only": bool(g1_manifest.get("fixture_only")),
        "pose_stream": g1_manifest.get("derivation", "unknown"),
        "pose_application": pose_application,
        "frame_count": len(frames),
        "timing": g1_manifest.get("timing"),
        "coordinates": g1_manifest.get("coordinates"),
        "contact": g1_manifest.get("contact"),
        "selected_frame": selected_frame,
        "camera_definitions": {
            "front": {"source": "roboharness named camera", "name": "front"},
            "side": {"source": "roboharness named camera", "name": "side"},
            "top": {"source": "roboharness named camera", "name": "top"},
        },
        "frame_paths": {
            view: _relative_path(path, manifest_path.parent)
            for view, path in frame_paths.items()
        },
        "replay_frames": {
            **{
                key: value
                for key, value in replay_sequence.items()
                if key != "paths"
            },
            "paths": [
                _relative_path(path, manifest_path.parent)
                for path in replay_sequence.get("paths", [])
            ],
        },
        "html": _relative_path(html_path, manifest_path.parent),
        "scoring_source": "smplx",
        "g1_scoring_allowed": False,
        "mesh_loaded": True,
        "nonblank_pixel_check": all(nonblank_checks.values()),
        "nonblank_views": nonblank_checks,
    }
    _write_json(manifest_path, manifest)
    html_path.write_text(_render_image_html(manifest, frame_paths), encoding="utf-8")
    return G1RenderWriteResult(html_path=html_path, manifest_path=manifest_path, frame_paths=frame_paths)


def _sample_roboharness_stages(frame_count: int) -> list[tuple[str, int]]:
    if frame_count <= 0:
        raise ValueError("G1 track must contain at least one frame")
    candidates = [
        ("start", 0),
        ("early", frame_count // 4),
        ("middle", frame_count // 2),
        ("late", (frame_count * 3) // 4),
        ("finish", frame_count - 1),
    ]
    stages: list[tuple[str, int]] = []
    seen: set[int] = set()
    for name, index in candidates:
        clamped = min(max(index, 0), frame_count - 1)
        if clamped in seen:
            continue
        seen.add(clamped)
        stages.append((name, clamped))
    return stages


def _load_roboharness_report_tools() -> tuple[Any, Any, Any, Any]:
    try:
        from roboharness.backends.mujoco_meshcat import MuJoCoMeshcatBackend
        from roboharness.core.checkpoint import Checkpoint
        from roboharness.core.harness import Harness
        from roboharness.core.protocol import TaskPhase, TaskProtocol
        from roboharness.reporting import generate_html_report
    except ModuleNotFoundError as exc:
        raise ValueError(
            "Roboharness report generation requires roboharness; install with "
            "`python -m pip install '.[real-g1-replay]'` or install `roboharness[demo]`."
        ) from exc
    return MuJoCoMeshcatBackend, Harness, Checkpoint, (TaskProtocol, TaskPhase, generate_html_report)


def write_g1_roboharness_report(
    out_dir: Path,
    *,
    model_descriptor_path: Path,
    g1_track: Path,
    allow_fixture_model: bool = False,
    width: int = 640,
    height: int = 480,
) -> G1RoboharnessReportResult:
    if width <= 0 or height <= 0:
        raise ValueError("roboharness report width and height must be positive")
    validate_output_dir(out_dir)
    model_descriptor = _load_model_descriptor(model_descriptor_path, allow_fixture_model=allow_fixture_model)
    if model_descriptor.get("fixture_only"):
        raise ValueError("roboharness report requires a registered G1 MJCF descriptor")
    if model_descriptor.get("model_format") != "mjcf":
        raise ValueError("roboharness report currently requires a registered MJCF descriptor")

    model_path = Path(model_descriptor.get("resolved_model_path") or model_descriptor.get("model_path", ""))
    if not model_path.exists():
        raise ValueError(f"registered model path does not exist: {model_path}")

    g1_track_manifest_path = resolve_g1_track_manifest(g1_track)
    g1_manifest, frames = load_g1_track_frames(g1_track_manifest_path)
    joint_angle_frames, joint_angle_names = _load_g1_joint_angle_frames(
        g1_track_manifest_path,
        g1_manifest,
        expected_frame_count=len(frames),
    )
    if not joint_angle_frames:
        raise ValueError("roboharness report requires an imported G1 joint-angle pose stream")

    mujoco = _load_mujoco()
    MuJoCoMeshcatBackend, Harness, Checkpoint, protocol_tools = _load_roboharness_report_tools()
    TaskProtocol, TaskPhase, generate_html_report = protocol_tools

    task_name = "neodojo_g1_replay"
    cameras = ["front", "side", "top", "close_up"]
    stages = _sample_roboharness_stages(len(frames))
    protocol = TaskProtocol(
        name="neodojo_qigong_replay",
        description="Sampled G1 replay stages from the imported neodojo visual track",
        phases=[
            TaskPhase(
                name,
                f"Imported G1 replay frame {frame_index}",
                cameras=cameras,
                metadata={"frame_index": frame_index},
            )
            for name, frame_index in stages
        ],
    )

    backend = MuJoCoMeshcatBackend(
        xml_string=_roboharness_scene_xml(model_path, width=width, height=height),
        cameras=cameras,
        render_width=width,
        render_height=height,
        visualizer=None,
    )
    model = backend._model
    data = backend._data
    harness = Harness(backend, output_dir=str(out_dir), task_name=task_name)
    harness.load_protocol(protocol)
    harness.reset()

    stage_paths: dict[str, dict[str, Path]] = {}
    for phase in protocol.phases:
        frame_index = int(phase.metadata["frame_index"])
        _mujoco_pose_application_for_frame(
            mujoco,
            model,
            data,
            joint_angle_frames=joint_angle_frames,
            joint_angle_names=joint_angle_names,
            frame_index=frame_index,
        )
        backend.visualizer.sync()
        harness._step_count = frame_index
        checkpoint = Checkpoint(name=phase.name, cameras=phase.cameras, metadata=phase.metadata)
        result = harness.capture(checkpoint)
        stage_dir = out_dir / task_name / "trial_001" / phase.name
        stage_paths[phase.name] = {
            view.name: stage_dir / f"{view.name}_rgb.png"
            for view in result.views
        }

    report_path = generate_html_report(
        out_dir,
        task_name,
        title="neodojo: G1 Roboharness Replay",
        subtitle=(
            "Imported Unitree G1 replay stages captured through the roboharness "
            "MuJoCo scene, cameras, checker floor, and report shell."
        ),
        accent_color="#d94a4a",
        footer_text="Generated by <code>neodojo render roboharness-g1</code>",
        meshcat_mode="none",
    )

    manifest_path = out_dir / "manifest.json"
    manifest = {
        "schema": G1_RENDER_SCHEMA,
        "fixture_only": bool(g1_manifest.get("fixture_only")),
        "actual_g1_model_replay": bool(not g1_manifest.get("fixture_only")),
        "renderer": {
            "backend": G1_ROBOHARNESS_REPORT_BACKEND,
            "role": "roboharness checkpoint report for sampled G1 replay stages",
            "mujoco_version": getattr(mujoco, "__version__", None),
            "gl_backend": os.environ.get("MUJOCO_GL") or "mujoco_default",
            "resolution": {"width": width, "height": height},
            "visual_theme": {
                "theme": G1_MUJOCO_VISUAL_THEME,
                **G1_MUJOCO_SCENE_STYLE,
            },
        },
        "robot": SUPPORTED_ROBOT,
        "model_descriptor": _relative_path(model_descriptor_path, manifest_path.parent),
        "g1_track": _relative_path(g1_track_manifest_path, manifest_path.parent),
        "pose_stream": g1_manifest.get("derivation", "unknown"),
        "joint_angle_count": len(joint_angle_names),
        "frame_count": len(frames),
        "stages": [
            {
                "name": name,
                "frame_index": frame_index,
                "paths": {
                    camera_name: _relative_path(path, manifest_path.parent)
                    for camera_name, path in stage_paths[name].items()
                },
            }
            for name, frame_index in stages
        ],
        "html": _relative_path(report_path, manifest_path.parent),
        "scoring_source": "smplx",
        "g1_scoring_allowed": False,
    }
    _write_json(manifest_path, manifest)
    return G1RoboharnessReportResult(
        html_path=report_path,
        manifest_path=manifest_path,
        stage_paths=stage_paths,
    )


def write_g1_mujoco_backend_comparison(
    out_dir: Path,
    *,
    model_descriptor_path: Path,
    g1_track: Path,
    backends: list[str],
    allow_fixture_model: bool = False,
    width: int = 640,
    height: int = 480,
    xvfb_glfw: str = "auto",
    timeout_seconds: int = 180,
) -> G1MujocoBackendComparisonResult:
    if width <= 0 or height <= 0:
        raise ValueError("MuJoCo render width and height must be positive")
    if not backends:
        raise ValueError("at least one MuJoCo GL backend is required")
    validate_output_dir(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    backend_results: list[dict[str, Any]] = []
    for backend in backends:
        backend_name = _safe_mujoco_backend_name(backend)
        backend_out_dir = out_dir / backend_name
        backend_results.append(
            _run_mujoco_backend_render(
                backend_name=backend_name,
                out_dir=backend_out_dir,
                relative_start=out_dir,
                model_descriptor_path=model_descriptor_path,
                g1_track=g1_track,
                allow_fixture_model=allow_fixture_model,
                width=width,
                height=height,
                xvfb_glfw=xvfb_glfw,
                timeout_seconds=timeout_seconds,
            )
        )

    manifest_path = out_dir / "manifest.json"
    html_path = out_dir / "index.html"
    manifest = {
        "schema": G1_MUJOCO_BACKEND_COMPARISON_SCHEMA,
        "status": "generated",
        "model_descriptor": _relative_path(model_descriptor_path, manifest_path.parent),
        "g1_track": _relative_path(g1_track, manifest_path.parent),
        "width": width,
        "height": height,
        "xvfb_glfw": xvfb_glfw,
        "backend_results": backend_results,
        "notes": (
            "Backend comparison renders the same model, track, camera, and resolution "
            "in isolated subprocesses because MUJOCO_GL is selected at import time."
        ),
    }
    _write_json(manifest_path, manifest)
    html_path.write_text(_render_backend_comparison_html(manifest), encoding="utf-8")
    return G1MujocoBackendComparisonResult(
        html_path=html_path,
        manifest_path=manifest_path,
        backend_results=backend_results,
    )


def _time_stats(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {
            "min_seconds": None,
            "mean_seconds": None,
            "median_seconds": None,
            "max_seconds": None,
        }
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    median = ordered[midpoint] if len(ordered) % 2 else (ordered[midpoint - 1] + ordered[midpoint]) / 2
    return {
        "min_seconds": round(ordered[0], 3),
        "mean_seconds": round(sum(ordered) / len(ordered), 3),
        "median_seconds": round(median, 3),
        "max_seconds": round(ordered[-1], 3),
    }


def _format_seconds(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def _render_backend_benchmark_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# MuJoCo GL Backend Benchmark",
        "",
        (
            f"Resolution: `{manifest['width']}x{manifest['height']}`. "
            f"Measured runs per backend: `{manifest['runs']}`. "
            f"Warmup runs: `{manifest['warmup_runs']}`."
        ),
        "",
        "| Backend | Status | Success | Min s | Mean s | Median s | Max s |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in manifest["backend_summaries"]:
        stats = item["stats"]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item["backend"]),
                    str(item["status"]),
                    f"{item['successful_runs']}/{item['measured_runs']}",
                    _format_seconds(stats["min_seconds"]),
                    _format_seconds(stats["mean_seconds"]),
                    _format_seconds(stats["median_seconds"]),
                    _format_seconds(stats["max_seconds"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Notes:",
            "- Timings include MuJoCo import/context setup, model load, selected front/side/top PNGs, and replay PNG sequence generation.",
            "- Exact PNG hashes are not expected to match across GL drivers; use this for performance picking.",
            "- Full per-run stdout/stderr and command details are in `manifest.json`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_g1_mujoco_backend_benchmark(
    out_dir: Path,
    *,
    model_descriptor_path: Path,
    g1_track: Path,
    backends: list[str],
    allow_fixture_model: bool = False,
    width: int = 640,
    height: int = 480,
    runs: int = 3,
    warmup_runs: int = 0,
    xvfb_glfw: str = "auto",
    timeout_seconds: int = 180,
) -> G1MujocoBackendBenchmarkResult:
    if width <= 0 or height <= 0:
        raise ValueError("MuJoCo render width and height must be positive")
    if runs <= 0:
        raise ValueError("benchmark runs must be positive")
    if warmup_runs < 0:
        raise ValueError("warmup runs must be non-negative")
    if not backends:
        raise ValueError("at least one MuJoCo GL backend is required")
    validate_output_dir(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    backend_summaries: list[dict[str, Any]] = []
    for backend in backends:
        backend_name = _safe_mujoco_backend_name(backend)
        run_results: list[dict[str, Any]] = []
        total_runs = warmup_runs + runs
        for index in range(total_runs):
            is_warmup = index < warmup_runs
            measured_index = index - warmup_runs
            run_label = f"warmup-{index + 1:02d}" if is_warmup else f"run-{measured_index + 1:02d}"
            run_out_dir = out_dir / backend_name / run_label
            item = _run_mujoco_backend_render(
                backend_name=backend_name,
                out_dir=run_out_dir,
                relative_start=out_dir,
                model_descriptor_path=model_descriptor_path,
                g1_track=g1_track,
                allow_fixture_model=allow_fixture_model,
                width=width,
                height=height,
                xvfb_glfw=xvfb_glfw,
                timeout_seconds=timeout_seconds,
            )
            item["run_label"] = run_label
            item["run_kind"] = "warmup" if is_warmup else "measured"
            item["run_index"] = index + 1
            run_results.append(item)

        measured = [item for item in run_results if item["run_kind"] == "measured"]
        successful = [float(item["elapsed_seconds"]) for item in measured if item["status"] == "rendered"]
        failed = [item for item in measured if item["status"] != "rendered"]
        if len(successful) == runs:
            status = "complete"
        elif successful:
            status = "partial"
        else:
            status = "failed"
        backend_summaries.append(
            {
                "backend": backend_name,
                "status": status,
                "measured_runs": runs,
                "warmup_runs": warmup_runs,
                "successful_runs": len(successful),
                "failed_runs": len(failed),
                "stats": _time_stats(successful),
                "run_results": run_results,
            }
        )

    manifest_path = out_dir / "manifest.json"
    markdown_path = out_dir / "benchmark.md"
    manifest = {
        "schema": G1_MUJOCO_BACKEND_BENCHMARK_SCHEMA,
        "status": "generated",
        "model_descriptor": _relative_path(model_descriptor_path, manifest_path.parent),
        "g1_track": _relative_path(g1_track, manifest_path.parent),
        "width": width,
        "height": height,
        "runs": runs,
        "warmup_runs": warmup_runs,
        "xvfb_glfw": xvfb_glfw,
        "backend_summaries": backend_summaries,
        "notes": (
            "Benchmark renders each backend in isolated subprocesses because "
            "MUJOCO_GL is selected at import time."
        ),
    }
    _write_json(manifest_path, manifest)
    markdown_path.write_text(_render_backend_benchmark_markdown(manifest), encoding="utf-8")
    return G1MujocoBackendBenchmarkResult(
        markdown_path=markdown_path,
        manifest_path=manifest_path,
        backend_summaries=backend_summaries,
    )
