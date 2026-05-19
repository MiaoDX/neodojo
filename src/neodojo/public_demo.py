from __future__ import annotations

import html
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import PLAYBACK_SCHEMA, PUBLIC_DEMO_SCHEMA, TWO_PANEL_TEACHING_HTML_PROFILE, require_schema
from .fixtures import BONES, TRAJECTORY_JOINTS
from .g1_render import G1_RENDER_SCHEMA
from .g1_visual import load_g1_track_frames
from .motion_contract import _relative_path, _write_json, load_motion_record_frames, validate_output_dir
from .smplx_surface import load_smplx_surface_layer

SCENE_TIMELINE_SCHEMA = "neodojo.scene_timeline.v1"
RERUN_RECORDING_EXPORT_SCHEMA = "neodojo.rerun_recording_export.v1"


@dataclass(frozen=True)
class PublicDemoWriteResult:
    html_path: Path
    manifest_path: Path
    scene_path: Path
    recording_path: Path
    screenshot_path: Path


@dataclass(frozen=True)
class PublicDemoSmokeResult:
    manifest_path: Path
    checked_paths: list[Path]


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _resolve_relative(base_file: Path, reference: str) -> Path:
    return (base_file.parent / reference).resolve()


def _load_optional_render_manifest(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = _load_json(path)
    require_schema(payload, G1_RENDER_SCHEMA, "G1 render manifest")
    return payload


def _actual_g1_replay_available(render_manifest: dict[str, Any] | None) -> bool:
    if not render_manifest:
        return False
    replay = render_manifest.get("replay_frames")
    renderer = render_manifest.get("renderer")
    return bool(
        isinstance(replay, dict)
        and replay.get("actual_g1_model_replay") is True
        and replay.get("available") is True
        and replay.get("nonblank_pixel_check") is True
        and replay.get("changed_frame_check") is True
        and isinstance(renderer, dict)
        and renderer.get("backend") == "mujoco_python_offscreen.v1"
        and render_manifest.get("model_fixture_only") is False
        and render_manifest.get("track_fixture_only") is False
    )


def _load_rerun_sdk() -> Any:
    try:
        import rerun as rr
    except ModuleNotFoundError as exc:
        raise ValueError(
            "Rerun SDK export requires the optional rerun-sdk package; install with "
            "`python -m pip install '.[rerun]'` or `python -m pip install rerun-sdk`"
        ) from exc
    return rr


def _surface_label(surface_manifest: dict[str, Any], layer_manifest: dict[str, Any] | None = None) -> str:
    if layer_manifest and isinstance(layer_manifest.get("label"), str):
        return layer_manifest["label"]
    if surface_manifest.get("licensed_smplx_mesh"):
        return "SMPL-X licensed mesh surface"
    return "SMPL-X surface proxy"


def _surface_layer_key(surface_layer: dict[str, Any] | None) -> str:
    if surface_layer and surface_layer.get("licensed_smplx_mesh"):
        return "smplx_mesh"
    return "smplx_proxy"


def build_scene_timeline(
    *,
    playback_manifest_path: Path,
    g1_render_manifest_path: Path | None = None,
) -> dict[str, Any]:
    playback = _load_json(playback_manifest_path)
    require_schema(playback, PLAYBACK_SCHEMA, "playback manifest")

    motion_manifest_path = _resolve_relative(playback_manifest_path, playback["motion_record"])
    g1_manifest_path = _resolve_relative(playback_manifest_path, playback["tracks"]["g1"]["manifest"])
    motion_manifest, smplx_frames = load_motion_record_frames(motion_manifest_path)
    g1_manifest, g1_frames = load_g1_track_frames(g1_manifest_path)
    if len(smplx_frames) != len(g1_frames):
        raise ValueError("SMPL-X and G1 tracks must have matching frame counts")

    surface_proxy = None
    surface_manifest_reference = None
    surface_layers = playback.get("surface_layers", {})
    if isinstance(surface_layers, dict):
        for layer_key in ("smplx_mesh", "smplx_proxy"):
            layer = surface_layers.get(layer_key)
            if not isinstance(layer, dict) or not layer.get("manifest"):
                continue
            surface_manifest_reference = layer["manifest"]
            surface_manifest_path = _resolve_relative(playback_manifest_path, surface_manifest_reference)
            surface_manifest, surface_data = load_smplx_surface_layer(surface_manifest_path)
            surface_frames = surface_data["frames"]
            if len(surface_frames) != len(smplx_frames):
                raise ValueError("SMPL-X surface layer must match playback frame count")
            surface_proxy = {
                "label": _surface_label(surface_manifest, layer),
                "surface_kind": surface_manifest.get("surface_kind"),
                "licensed_smplx_mesh": bool(surface_manifest.get("licensed_smplx_mesh", False)),
                "scoring_allowed": False,
                "frames": surface_frames,
                "manifest": surface_manifest_reference,
            }
            if isinstance(surface_data.get("faces"), list):
                surface_proxy["faces"] = surface_data["faces"]
            break

    render_manifest = _load_optional_render_manifest(g1_render_manifest_path)
    actual_g1_replay = _actual_g1_replay_available(render_manifest)
    g1_panel_label = "Unitree G1 MuJoCo model replay" if actual_g1_replay else "Unitree G1 schematic evidence"
    g1_visual_style = (
        "mujoco-png-frame-sequence.v1"
        if actual_g1_replay
        else "robot-body-schematic.v1"
    )
    fixture_only = bool(playback.get("fixture_only") or g1_manifest.get("fixture_only"))
    key_frame = int(playback.get("key_frame", len(smplx_frames) - 1))
    annotations = playback.get("annotation_manifest")
    routine_review = playback.get("routine_review")
    feedback_anchor_labels = []
    if isinstance(annotations, dict):
        keyframes = annotations.get("keyframes", [])
        if isinstance(keyframes, list):
            feedback_anchor_labels = [
                str(keyframe.get("name"))
                for keyframe in keyframes
                if isinstance(keyframe, dict) and isinstance(keyframe.get("name"), str)
            ]

    return {
        "schema": SCENE_TIMELINE_SCHEMA,
        "fixture_only": fixture_only,
        "source_manifests": {
            "playback": str(playback_manifest_path),
            "motion_record": playback["motion_record"],
            "g1_track": playback["tracks"]["g1"]["manifest"],
            "g1_render": str(g1_render_manifest_path) if g1_render_manifest_path else None,
            "smplx_surface": surface_manifest_reference,
        },
        "timing": playback.get("timing") or motion_manifest.get("timing"),
        "coordinates": playback.get("coordinates") or motion_manifest.get("coordinates"),
        "contact": playback.get("contact") or motion_manifest.get("contact"),
        "camera_definitions": {
            "front": {"projection_axes": ["x", "y"]},
            "side": {"projection_axes": ["z", "y"]},
            "top": {"projection_axes": ["x", "z"]},
        },
        "key_frame": key_frame,
        "trajectory_joints": TRAJECTORY_JOINTS,
        "bones": BONES,
        "tracks": {
            "smplx": {
                "label": "SMPL-X teacher",
                "role": "teaching accuracy source",
                "scoring_allowed": True,
                "frames": smplx_frames,
            },
            "g1": {
                "label": g1_panel_label,
                "role": g1_manifest["role"],
                "scoring_allowed": False,
                "frames": g1_frames,
            },
        },
        "track_metadata": {
            "smplx": {
                "fixture_only": bool(motion_manifest.get("fixture_only")),
                "frame_count": len(smplx_frames),
                "fps": motion_manifest.get("fps"),
                "role": "teaching accuracy source",
            },
            "g1": {
                "fixture_only": bool(g1_manifest.get("fixture_only")),
                "robot": g1_manifest.get("robot"),
                "role": g1_manifest.get("role"),
                "derivation": g1_manifest.get("derivation"),
                "model_descriptor": g1_manifest.get("model_descriptor"),
                "source_motion_record": g1_manifest.get("source_motion_record"),
                "pose_stream": g1_manifest.get("pose_stream"),
                "frame_count": len(g1_frames),
                "fps": g1_manifest.get("fps"),
                "scoring_allowed": False,
            },
        },
        "annotations": annotations,
        "routine_review": routine_review,
        "feedback_anchor_labels": feedback_anchor_labels,
        "surface_proxy": surface_proxy,
        "reference_video_sync": playback.get("reference_video_sync"),
        "feedback": playback.get("feedback"),
        "render_evidence": render_manifest,
        "g1_render_frame_sequence": {
            "available": False,
            "actual_g1_model_replay": actual_g1_replay,
            "visual_style": g1_visual_style,
            "paths": [],
            "frame_count": 0,
        },
        "public_labels": [
            "fixture-only" if fixture_only else "real-artifact",
            "SMPL-X teacher",
            g1_panel_label,
            "G1 non-scoring",
            "Routine feedback",
            *([surface_proxy["label"]] if surface_proxy else []),
            *feedback_anchor_labels,
        ],
        "scoring_source": "smplx",
    }


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
    scale = min(360 / width, 230 / height)
    x = 240 + (point[0] - ((min_x + max_x) / 2)) * scale
    y = 180 - (point[1] - ((min_y + max_y) / 2)) * scale
    return x, y


def _track_svg(track: dict[str, Any], view: str, frame_index: int, stroke: str) -> str:
    frame = track["frames"][frame_index]
    points = [_project(point, view) for point in frame.values()]
    bounds = _bounds(points)
    lines = []
    for start, end in BONES:
        if start not in frame or end not in frame:
            continue
        x1, y1 = _scale(_project(frame[start], view), bounds)
        x2, y2 = _scale(_project(frame[end], view), bounds)
        lines.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="4" stroke-linecap="round"/>'
        )
    joints = []
    for point in frame.values():
        x, y = _scale(_project(point, view), bounds)
        joints.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{stroke}"/>')
    return "\n".join(lines + joints)


def _track_line_strips(track: dict[str, Any], frame_index: int) -> list[list[list[float]]]:
    frame = track["frames"][frame_index]
    strips = []
    for start, end in BONES:
        if start in frame and end in frame:
            strips.append([frame[start], frame[end]])
    return strips


def _write_rerun_recording(scene: dict[str, Any], recording_path: Path) -> dict[str, Any]:
    rr = _load_rerun_sdk()
    rr.init("neodojo_public_demo", spawn=False)
    rr.save(recording_path)
    try:
        rr.log(
            "neodojo/readme",
            rr.TextDocument(
                "neodojo fixture teaching scene. SMPL-X is the scoring source; Unitree G1 is visual-only.",
                media_type="text/markdown",
            ),
            static=True,
        )
        rr.log(
            "neodojo/public_labels",
            rr.TextDocument("\n".join(scene["public_labels"]), media_type="text/plain"),
            static=True,
        )
        frame_count = int((scene.get("timing") or {}).get("frame_count") or len(scene["tracks"]["smplx"]["frames"]))
        for frame_index in range(frame_count):
            rr.set_time("frame", sequence=frame_index)
            for track_id, track in scene["tracks"].items():
                frame = track["frames"][frame_index]
                labels = list(frame)
                positions = [frame[label] for label in labels]
                rr.log(
                    f"tracks/{track_id}/joints",
                    rr.Points3D(positions, labels=labels, radii=0.025),
                )
                rr.log(
                    f"tracks/{track_id}/bones",
                    rr.LineStrips3D(_track_line_strips(track, frame_index), radii=0.01),
                )
    finally:
        rr.disconnect()
    return {
        "schema": RERUN_RECORDING_EXPORT_SCHEMA,
        "actual_rerun_rrd": True,
        "format": "rerun_sdk_rrd",
        "sdk_version": getattr(rr, "__version__", None),
    }


def _surface_svg(surface_proxy: dict[str, Any] | None, smplx_track: dict[str, Any], view: str, frame_index: int) -> str:
    if not surface_proxy:
        return ""
    frame = smplx_track["frames"][frame_index]
    points = [_project(point, view) for point in frame.values()]
    bounds = _bounds(points)
    surface_frame = surface_proxy["frames"][frame_index]
    elements = []
    for capsule in surface_frame.get("capsules", []):
        start = capsule.get("start")
        end = capsule.get("end")
        if not isinstance(start, list) or not isinstance(end, list):
            continue
        x1, y1 = _scale(_project(start, view), bounds)
        x2, y2 = _scale(_project(end, view), bounds)
        width = max(8, float(capsule.get("radius_m", 0.04)) * 180)
        elements.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#147c72" stroke-opacity="0.16" stroke-width="{width:.1f}" stroke-linecap="round"/>'
        )
    vertices = surface_frame.get("vertices")
    faces = surface_frame.get("faces") or surface_proxy.get("faces")
    if isinstance(vertices, list) and isinstance(faces, list):
        mesh_points = [_project(vertex, view) for vertex in vertices if isinstance(vertex, list) and len(vertex) == 3]
        if mesh_points:
            bounds = _bounds(points + mesh_points)
        for face in faces[:400]:
            if not isinstance(face, list) or len(face) != 3:
                continue
            try:
                projected = [_scale(_project(vertices[index], view), bounds) for index in face]
            except (IndexError, TypeError):
                continue
            path = " ".join(f"{x:.1f},{y:.1f}" for x, y in projected)
            elements.append(
                f'<polygon points="{path}" fill="#147c72" fill-opacity="0.08" '
                f'stroke="#147c72" stroke-opacity="0.18" stroke-width="1"/>'
            )
    return "\n".join(elements)


def _render_screenshot_svg(scene: dict[str, Any]) -> str:
    key_frame = int(scene["key_frame"])
    surface = _surface_svg(scene.get("surface_proxy"), scene["tracks"]["smplx"], "front", key_frame)
    smplx = _track_svg(scene["tracks"]["smplx"], "front", key_frame, "#147c72")
    g1 = _track_svg(scene["tracks"]["g1"], "front", key_frame, "#b84e32")
    fixture_label = "FIXTURE-ONLY" if scene["fixture_only"] else "REAL ARTIFACT"
    feedback = scene.get("feedback") or {}
    anchors = scene.get("feedback_anchor_labels") or []
    anchor_text = ", ".join(anchors[:3]) if anchors else "none"
    surface_layer = scene.get("surface_proxy")
    surface_text = surface_layer.get("label") if surface_layer else "off"
    g1_label = scene.get("tracks", {}).get("g1", {}).get("label", "Unitree G1 schematic evidence")
    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" role="img">',
            "<style>text{font-family:Inter,Arial,sans-serif}.title{font-size:30px;font-weight:760;fill:#17212b}.muted{font-size:16px;fill:#66717f}.badge{font-size:14px;font-weight:760;fill:#b54708}</style>",
            '<rect width="1280" height="720" fill="#eef2f6"/>',
            '<rect x="32" y="28" width="1216" height="86" rx="8" fill="#ffffff" stroke="#d8e0e8"/>',
            '<text x="56" y="68" class="title">neodojo public fixture demo</text>',
            f'<text x="56" y="94" class="muted">SMPL-X teacher + {g1_label} - frame {key_frame + 1}</text>',
            f'<text x="1080" y="66" class="badge">{fixture_label}</text>',
            '<rect x="48" y="144" width="560" height="500" rx="8" fill="#ffffff" stroke="#d8e0e8"/>',
            '<rect x="672" y="144" width="560" height="500" rx="8" fill="#ffffff" stroke="#d8e0e8"/>',
            '<text x="72" y="184" class="title">SMPL-X teacher</text>',
            f'<text x="696" y="184" class="title">{g1_label}</text>',
            f'<g transform="translate(80 210)">{surface}{smplx}</g>',
            f'<g transform="translate(704 210)">{g1}</g>',
            f'<text x="56" y="684" class="muted">Scoring source: SMPL-X. G1 scoring allowed: false. Feedback passed: {feedback.get("passed")}</text>',
            f'<text x="696" y="672" class="muted">Routine feedback anchors: {anchor_text}</text>',
            f'<text x="696" y="696" class="muted">SMPL-X surface layer: {surface_text}</text>',
            "</svg>",
        ]
    )


def _render_public_html(scene: dict[str, Any], manifest: dict[str, Any]) -> str:
    payload = json.dumps(scene, sort_keys=True, separators=(",", ":"))
    fixture_note = "fixture-only" if scene["fixture_only"] else "real-artifact"
    anchor_labels = scene.get("feedback_anchor_labels") or []
    anchor_text = ", ".join(anchor_labels) if anchor_labels else "none"
    routine_review = scene.get("routine_review") or {}
    routine_summary = routine_review.get("summary") if isinstance(routine_review, dict) else {}
    if not isinstance(routine_summary, dict):
        routine_summary = {}
    routine_status = routine_summary.get("status", "pending")
    surface_proxy = scene.get("surface_proxy")
    surface_label = surface_proxy.get("label") if surface_proxy else "off"
    g1_meta = scene.get("track_metadata", {}).get("g1", {})
    render_evidence = scene.get("render_evidence") or {}
    renderer = render_evidence.get("renderer") if isinstance(render_evidence, dict) else {}
    renderer_backend = renderer.get("backend") if isinstance(renderer, dict) else "none"
    g1_sequence = scene.get("g1_render_frame_sequence") or {}
    actual_g1_replay = bool(g1_sequence.get("actual_g1_model_replay"))
    g1_panel_label = (
        "Unitree G1 MuJoCo model replay"
        if actual_g1_replay
        else "Unitree G1 schematic evidence"
    )
    g1_panel_role = "actual MuJoCo frame replay" if actual_g1_replay else "schematic evidence"
    g1_visual_style = (
        "mujoco-png-frame-sequence.v1"
        if actual_g1_replay
        else "robot-body-schematic.v1"
    )
    g1_track_source = "fixture-derived track" if g1_meta.get("fixture_only") else "imported GMR track"
    g1_model_source = (
        "fixture model descriptor"
        if render_evidence.get("model_fixture_only")
        else "registered model descriptor"
        if render_evidence
        else "model descriptor unavailable"
    )
    reference_video = scene.get("reference_video") or {}
    reference_video_available = bool(
        isinstance(reference_video, dict)
        and reference_video.get("available")
        and reference_video.get("path")
    )
    layout_class = "three-panel" if reference_video_available else "two-panel"
    layout_label = (
        "source video, SMPL-X, and G1 synchronized teaching replay"
        if reference_video_available
        else "two-panel synchronized teaching replay"
    )
    source_panel = ""
    if reference_video_available:
        source_path = html.escape(str(reference_video["path"]), quote=True)
        trim_start = reference_video.get("trim_start_seconds", 0.0)
        try:
            trim_label = f"{float(trim_start):.2f}s"
        except (TypeError, ValueError):
            trim_label = "local clip"
        source_panel = f"""
    <section class="panel" data-panel="source">
      <div class="panel-head">
        <h2>Original video</h2>
        <span>source clip</span>
      </div>
      <video id="referenceVideo" class="reference-video" src="{source_path}" muted playsinline preload="auto" aria-label="Original source video"></video>
      <div class="meta">
        <div class="metric"><span>Clip source</span><strong>local reference video</strong></div>
        <div class="metric"><span>Source offset</span><strong>{trim_label}</strong></div>
        <div class="metric"><span>Sync</span><strong>same timeline</strong></div>
      </div>
    </section>"""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>neodojo teaching replay</title>
  <style>
    :root {{ --bg: #eef2f6; --panel: #fff; --ink: #17212b; --muted: #66717f; --line: #d8e0e8; --smplx: #147c72; --g1: #b84e32; --trail: #d73f7c; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-height: 100vh; background: var(--bg); color: var(--ink); font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .app {{ min-height: 100vh; display: grid; grid-template-rows: auto minmax(0, 1fr) auto; }}
    header {{ display: flex; justify-content: space-between; gap: 16px; align-items: center; padding: 14px 18px; background: var(--panel); border-bottom: 1px solid var(--line); }}
    h1, h2, p {{ margin: 0; }}
    h1 {{ font-size: 19px; }}
    .badges {{ display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }}
    .badge {{ border: 1px solid var(--line); border-radius: 999px; padding: 7px 11px; color: #334155; background: #f9fbfd; font-size: 12px; font-weight: 800; white-space: nowrap; }}
    main {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); min-height: 0; gap: 16px; padding: 16px; }}
    main.three-panel {{ grid-template-columns: minmax(260px, 0.9fr) minmax(0, 1fr) minmax(0, 1fr); }}
    .panel {{ min-width: 0; display: grid; grid-template-rows: auto minmax(0, 1fr) auto; gap: 10px; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 12px; }}
    .panel-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }}
    h2 {{ font-size: 17px; }}
    .panel-head span {{ color: var(--muted); font-size: 12px; font-weight: 800; text-align: right; }}
    canvas {{ width: 100%; min-height: 420px; aspect-ratio: 1 / 1; display: block; background: #fbfcfe; border: 1px solid var(--line); border-radius: 8px; }}
    .g1-frame {{ width: 100%; min-height: 420px; aspect-ratio: 1 / 1; display: block; object-fit: contain; background: #fbfcfe; border: 1px solid var(--line); border-radius: 8px; }}
    .reference-video {{ width: 100%; min-height: 420px; aspect-ratio: 1 / 1; display: block; object-fit: contain; background: #fbfcfe; border: 1px solid var(--line); border-radius: 8px; }}
    [hidden] {{ display: none !important; }}
    .meta {{ display: grid; gap: 7px; color: var(--muted); font-size: 13px; }}
    .metric {{ display: flex; justify-content: space-between; gap: 12px; padding-top: 7px; border-top: 1px solid var(--line); color: var(--muted); font-size: 13px; }}
    .metric strong {{ color: var(--ink); text-align: right; }}
    footer {{ display: grid; grid-template-columns: auto minmax(160px, 1fr) auto; gap: 12px; align-items: center; padding: 12px 16px 16px; background: rgba(255,255,255,0.92); border-top: 1px solid var(--line); }}
    button {{ min-width: 84px; min-height: 38px; border: 1px solid #b9c5d0; border-radius: 8px; background: #fff; color: var(--ink); font: inherit; font-weight: 800; cursor: pointer; }}
    input[type="range"] {{ width: 100%; accent-color: var(--smplx); }}
    .readout {{ min-width: 126px; color: var(--muted); font-size: 13px; font-weight: 800; text-align: right; }}
    @media (max-width: 1100px) {{ main, main.three-panel {{ grid-template-columns: 1fr; }} canvas, .g1-frame, .reference-video {{ min-height: 300px; }} footer {{ grid-template-columns: 1fr; }} .readout {{ text-align: left; }} }}
  </style>
</head>
<body data-teaching-html-profile="{TWO_PANEL_TEACHING_HTML_PROFILE}">
<div class="app">
  <header>
    <h1>neodojo teaching replay</h1>
    <div class="badges">
      <span class="badge">{fixture_note}</span>
      <span class="badge">SMPL-X scoring</span>
      <span class="badge">G1 non-scoring</span>
      <span class="badge">Synchronized timeline</span>
    </div>
  </header>
  <main class="{layout_class}" aria-label="{layout_label}">{source_panel}
    <section class="panel" data-panel="smplx">
      <div class="panel-head">
        <h2>SMPL-X skeleton teaching track</h2>
        <span>accuracy source</span>
      </div>
      <canvas id="smplxCanvas" width="720" height="720" aria-label="SMPL-X skeleton teaching track"></canvas>
      <div class="meta">
        <div class="metric"><span>Feedback source</span><strong>SMPL-X</strong></div>
        <div class="metric"><span>Surface layer</span><strong>{surface_label}</strong></div>
        <div class="metric"><span>Routine feedback</span><strong>{routine_status}</strong></div>
        <div class="metric"><span>Routine anchors</span><strong>{anchor_text}</strong></div>
      </div>
    </section>
    <section class="panel" data-panel="g1">
      <div class="panel-head">
        <h2>{g1_panel_label}</h2>
        <span>{g1_panel_role}</span>
      </div>
      <img id="g1ReplayImage" class="g1-frame" alt="Unitree G1 MuJoCo model replay frame" hidden>
      <canvas id="g1Canvas" width="720" height="720" aria-label="{g1_panel_label}" data-g1-render-style="{g1_visual_style}"></canvas>
      <div class="meta">
        <div class="metric"><span>Track source</span><strong>{g1_track_source}</strong></div>
        <div class="metric"><span>Model source</span><strong>{g1_model_source}</strong></div>
        <div class="metric"><span>Renderer</span><strong>{renderer_backend}</strong></div>
      </div>
    </section>
  </main>
  <footer aria-label="Synchronized timeline controls">
    <button id="playButton" type="button">Pause</button>
    <input id="timeline" type="range" min="0" max="0" value="0" aria-label="Synchronized timeline">
    <div class="readout" id="frameReadout">Frame 1</div>
  </footer>
</div>
<script>
const SCENE = {payload};
const BONES = SCENE.bones || [];
const smplxCanvas = document.getElementById("smplxCanvas");
const g1Canvas = document.getElementById("g1Canvas");
const g1ReplayImage = document.getElementById("g1ReplayImage");
const referenceVideo = document.getElementById("referenceVideo");
const playButton = document.getElementById("playButton");
const timeline = document.getElementById("timeline");
const frameReadout = document.getElementById("frameReadout");
const g1Sequence = SCENE.g1_render_frame_sequence || {{}};
const referenceInfo = SCENE.reference_video || {{}};
const frameCount = SCENE.tracks.smplx.frames.length;
const fps = Number((SCENE.timing && SCENE.timing.fps) || (SCENE.track_metadata.smplx && SCENE.track_metadata.smplx.fps) || 25);
let frame = 0;
let playing = true;
let lastTick = 0;
timeline.max = String(Math.max(0, frameCount - 1));

function project(point) {{
  return [point[0], point[1]];
}}

function boundsFor(pose) {{
  const values = Object.values(pose).map(project);
  const xs = values.map((point) => point[0]);
  const ys = values.map((point) => point[1]);
  return {{
    minX: Math.min(...xs),
    maxX: Math.max(...xs),
    minY: Math.min(...ys),
    maxY: Math.max(...ys)
  }};
}}

function toCanvas(point, bounds, width, height) {{
  const [x, y] = project(point);
  const spanX = Math.max(bounds.maxX - bounds.minX, 0.25);
  const spanY = Math.max(bounds.maxY - bounds.minY, 0.25);
  const scale = Math.min((width - 96) / spanX, (height - 96) / spanY);
  const centerX = (bounds.minX + bounds.maxX) / 2;
  const centerY = (bounds.minY + bounds.maxY) / 2;
  return [width / 2 + (x - centerX) * scale, height / 2 - (y - centerY) * scale];
}}

function drawGrid(ctx, width, height) {{
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#fbfcfe";
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = "#e5ebf1";
  ctx.lineWidth = 1;
  for (let offset = 48; offset < width; offset += 48) {{
    ctx.beginPath();
    ctx.moveTo(offset, 0);
    ctx.lineTo(offset, height);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(0, offset);
    ctx.lineTo(width, offset);
    ctx.stroke();
  }}
}}

function drawTrajectory(ctx, frames, bounds, width, height, color) {{
  const joints = SCENE.trajectory_joints || ["left_wrist", "right_wrist"];
  ctx.globalAlpha = 0.48;
  ctx.strokeStyle = color;
  ctx.lineWidth = 3;
  for (const joint of joints) {{
    ctx.beginPath();
    for (let index = 0; index <= frame; index += 1) {{
      const point = frames[index][joint];
      if (!point) continue;
      const [x, y] = toCanvas(point, bounds, width, height);
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }}
    ctx.stroke();
  }}
  ctx.globalAlpha = 1;
}}

function drawSkeleton(ctx, pose, bounds, width, height) {{
  ctx.strokeStyle = "#147c72";
  ctx.lineWidth = 5;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  for (const [a, b] of BONES) {{
    if (!pose[a] || !pose[b]) continue;
    const [ax, ay] = toCanvas(pose[a], bounds, width, height);
    const [bx, by] = toCanvas(pose[b], bounds, width, height);
    ctx.beginPath();
    ctx.moveTo(ax, ay);
    ctx.lineTo(bx, by);
    ctx.stroke();
  }}
  for (const [joint, point] of Object.entries(pose)) {{
    const [x, y] = toCanvas(point, bounds, width, height);
    ctx.fillStyle = joint.includes("wrist") || joint.includes("elbow") ? "#d73f7c" : "#ffffff";
    ctx.strokeStyle = "#147c72";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  }}
}}

function canvasPoint(pose, joint, bounds, width, height) {{
  if (!pose[joint]) return null;
  return toCanvas(pose[joint], bounds, width, height);
}}

function midPoint(a, b) {{
  return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
}}

function drawCapsule(ctx, a, b, thickness, fill, stroke) {{
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const length = Math.max(Math.hypot(dx, dy), thickness);
  ctx.save();
  ctx.translate((a[0] + b[0]) / 2, (a[1] + b[1]) / 2);
  ctx.rotate(Math.atan2(dy, dx));
  ctx.fillStyle = fill;
  ctx.strokeStyle = stroke;
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.roundRect(-length / 2, -thickness / 2, length, thickness, thickness / 2);
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}}

function drawBlock(ctx, center, width, height, fill, stroke) {{
  ctx.fillStyle = fill;
  ctx.strokeStyle = stroke;
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.roundRect(center[0] - width / 2, center[1] - height / 2, width, height, 5);
  ctx.fill();
  ctx.stroke();
}}

function drawTorsoPlate(ctx, shoulders, hips) {{
  const [leftShoulder, rightShoulder] = shoulders;
  const [leftHip, rightHip] = hips;
  ctx.fillStyle = "#bf5737";
  ctx.strokeStyle = "#7f2f1d";
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.moveTo(leftShoulder[0], leftShoulder[1]);
  ctx.lineTo(rightShoulder[0], rightShoulder[1]);
  ctx.lineTo(rightHip[0], rightHip[1]);
  ctx.lineTo(leftHip[0], leftHip[1]);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
}}

function drawRobotLink(ctx, pose, bounds, width, height, a, b, thickness, fill) {{
  const start = canvasPoint(pose, a, bounds, width, height);
  const end = canvasPoint(pose, b, bounds, width, height);
  if (!start || !end) return;
  drawCapsule(ctx, start, end, thickness, fill, "#8f351f");
}}

function drawRobotModel(ctx, pose, bounds, width, height) {{
  const leftShoulder = canvasPoint(pose, "left_shoulder", bounds, width, height);
  const rightShoulder = canvasPoint(pose, "right_shoulder", bounds, width, height);
  const leftHip = canvasPoint(pose, "left_hip", bounds, width, height);
  const rightHip = canvasPoint(pose, "right_hip", bounds, width, height);
  const pelvis = canvasPoint(pose, "pelvis", bounds, width, height);
  const spine = canvasPoint(pose, "spine", bounds, width, height);
  const neck = canvasPoint(pose, "neck", bounds, width, height);
  const head = canvasPoint(pose, "head", bounds, width, height);

  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  drawRobotLink(ctx, pose, bounds, width, height, "left_shoulder", "left_elbow", 20, "#c15a38");
  drawRobotLink(ctx, pose, bounds, width, height, "left_elbow", "left_wrist", 16, "#d77a57");
  drawRobotLink(ctx, pose, bounds, width, height, "right_shoulder", "right_elbow", 20, "#c15a38");
  drawRobotLink(ctx, pose, bounds, width, height, "right_elbow", "right_wrist", 16, "#d77a57");
  drawRobotLink(ctx, pose, bounds, width, height, "left_hip", "left_knee", 23, "#b84e32");
  drawRobotLink(ctx, pose, bounds, width, height, "left_knee", "left_ankle", 19, "#d06b46");
  drawRobotLink(ctx, pose, bounds, width, height, "right_hip", "right_knee", 23, "#b84e32");
  drawRobotLink(ctx, pose, bounds, width, height, "right_knee", "right_ankle", 19, "#d06b46");
  if (leftShoulder && rightShoulder && leftHip && rightHip) {{
    drawTorsoPlate(ctx, [leftShoulder, rightShoulder], [leftHip, rightHip]);
  }}
  if (spine && neck) drawCapsule(ctx, spine, neck, 22, "#9f3d25", "#6f2b1b");
  if (pelvis) drawBlock(ctx, pelvis, 42, 30, "#17212b", "#7f2f1d");
  if (head) drawBlock(ctx, head, 28, 28, "#17212b", "#7f2f1d");
  for (const joint of ["left_elbow", "right_elbow", "left_knee", "right_knee", "left_shoulder", "right_shoulder"]) {{
    const point = canvasPoint(pose, joint, bounds, width, height);
    if (point) drawBlock(ctx, point, 16, 16, "#fff7ed", "#8f351f");
  }}
  for (const joint of ["left_wrist", "right_wrist", "left_ankle", "right_ankle"]) {{
    const point = canvasPoint(pose, joint, bounds, width, height);
    if (point) drawBlock(ctx, point, 20, 14, "#ffffff", "#8f351f");
  }}
  if (leftShoulder && rightShoulder) {{
    const shoulderCenter = midPoint(leftShoulder, rightShoulder);
    drawBlock(ctx, shoulderCenter, 30, 20, "#17212b", "#7f2f1d");
  }}
}}

function drawPanel(canvas, trackId) {{
  const ctx = canvas.getContext("2d");
  const frames = SCENE.tracks[trackId].frames;
  const pose = frames[frame];
  const bounds = boundsFor(pose);
  drawGrid(ctx, canvas.width, canvas.height);
  drawTrajectory(ctx, frames, bounds, canvas.width, canvas.height, trackId === "smplx" ? "#147c72" : "#b84e32");
  if (trackId === "smplx") drawSkeleton(ctx, pose, bounds, canvas.width, canvas.height);
  else drawRobotModel(ctx, pose, bounds, canvas.width, canvas.height);
}}

function syncReferenceVideo() {{
  if (!referenceVideo || !referenceInfo.available) return;
  const offset = Number(referenceInfo.playback_offset_seconds || 0);
  let target = offset + frame / fps;
  if (Number.isFinite(referenceVideo.duration) && referenceVideo.duration > 0) {{
    target = Math.min(target, Math.max(0, referenceVideo.duration - 0.04));
  }}
  if (Math.abs(referenceVideo.currentTime - target) > 0.04) {{
    try {{
      referenceVideo.currentTime = target;
    }} catch (error) {{
      return;
    }}
  }}
}}

function render() {{
  drawPanel(smplxCanvas, "smplx");
  if (g1Sequence.available && Array.isArray(g1Sequence.paths) && g1Sequence.paths.length > 0) {{
    g1Canvas.hidden = true;
    g1ReplayImage.hidden = false;
    const index = Math.min(frame, g1Sequence.paths.length - 1);
    g1ReplayImage.src = g1Sequence.paths[index];
  }} else {{
    g1ReplayImage.hidden = true;
    g1Canvas.hidden = false;
    drawPanel(g1Canvas, "g1");
  }}
  syncReferenceVideo();
  timeline.value = String(frame);
  frameReadout.textContent = `Frame ${{frame + 1}} / ${{frameCount}}`;
}}

function tick(timestamp) {{
  if (!lastTick) lastTick = timestamp;
  if (playing && timestamp - lastTick > 1000 / fps) {{
    frame = (frame + 1) % frameCount;
    lastTick = timestamp;
    render();
  }}
  window.requestAnimationFrame(tick);
}}

playButton.addEventListener("click", () => {{
  playing = !playing;
  playButton.textContent = playing ? "Pause" : "Play";
}});

timeline.addEventListener("input", (event) => {{
  frame = Number(event.target.value);
  playing = false;
  playButton.textContent = "Play";
  render();
}});

if (referenceVideo) {{
  referenceVideo.addEventListener("loadedmetadata", render);
}}

render();
window.requestAnimationFrame(tick);
</script>
</body>
</html>
"""


def _attach_public_g1_replay_frames(
    scene: dict[str, Any],
    *,
    g1_render_manifest_path: Path | None,
    out_dir: Path,
) -> None:
    render_manifest = scene.get("render_evidence")
    if not isinstance(render_manifest, dict) or not _actual_g1_replay_available(render_manifest):
        scene["g1_render_frame_sequence"] = {
            "available": False,
            "actual_g1_model_replay": False,
            "visual_style": "robot-body-schematic.v1",
            "paths": [],
            "frame_count": 0,
        }
        return
    if g1_render_manifest_path is None:
        raise ValueError("actual G1 replay render evidence requires a render manifest path")

    replay = render_manifest["replay_frames"]
    source_paths = replay.get("paths")
    if not isinstance(source_paths, list) or not source_paths:
        raise ValueError("actual G1 replay render manifest is missing replay frame paths")

    frame_dir = out_dir / "g1-replay-frames"
    copied_paths: list[str] = []
    frame_dir.mkdir(parents=True, exist_ok=True)
    for index, reference in enumerate(source_paths):
        if not isinstance(reference, str) or not reference:
            raise ValueError("actual G1 replay frame paths must be non-empty strings")
        source = (g1_render_manifest_path.parent / reference).resolve()
        if not source.exists() or not source.read_bytes():
            raise ValueError(f"actual G1 replay frame is missing or blank: {source}")
        destination = frame_dir / f"front-{index:06d}.png"
        shutil.copyfile(source, destination)
        copied_paths.append(_relative_path(destination, out_dir))

    scene["g1_render_frame_sequence"] = {
        "available": True,
        "actual_g1_model_replay": True,
        "visual_style": "mujoco-png-frame-sequence.v1",
        "view": replay.get("view", "front"),
        "paths": copied_paths,
        "frame_count": len(copied_paths),
        "source_render_manifest": scene.get("source_manifests", {}).get("g1_render"),
        "nonblank_pixel_check": replay.get("nonblank_pixel_check"),
        "changed_frame_check": replay.get("changed_frame_check"),
        "applied_joint_count_min": replay.get("applied_joint_count_min"),
    }


def _candidate_reference_video_paths(
    media: dict[str, Any],
    *,
    playback_manifest_path: Path,
) -> list[Path]:
    candidates: list[Path] = []
    for key in ("resolved_path", "path"):
        reference = media.get(key)
        if not isinstance(reference, str) or not reference:
            continue
        path = Path(reference)
        if path.is_absolute():
            candidates.append(path)
        else:
            candidates.append(path.resolve())
            candidates.append((playback_manifest_path.parent / path).resolve())

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def _attach_public_reference_video(
    scene: dict[str, Any],
    *,
    playback_manifest_path: Path,
    out_dir: Path,
) -> None:
    reference_sync = scene.get("reference_video_sync")
    unavailable = {
        "available": False,
        "label": "Original video",
        "role": "source clip",
        "path": None,
        "reason": "no reference video was supplied",
    }
    if not isinstance(reference_sync, dict):
        scene["reference_video"] = unavailable
        return

    media = reference_sync.get("media")
    if not isinstance(media, dict):
        scene["reference_video"] = {**unavailable, "reason": "reference video metadata is missing media"}
        return

    source = next(
        (
            candidate
            for candidate in _candidate_reference_video_paths(media, playback_manifest_path=playback_manifest_path)
            if candidate.exists() and candidate.is_file() and candidate.stat().st_size > 0
        ),
        None,
    )
    if source is None:
        scene["reference_video"] = {
            **unavailable,
            "reason": "reference video file is not available on this machine",
            "media": media,
        }
        return

    suffix = source.suffix.lower()
    if suffix not in {".mp4", ".mov", ".m4v", ".webm"}:
        scene["reference_video"] = {
            **unavailable,
            "reason": f"unsupported reference video suffix: {suffix}",
            "media": media,
        }
        return

    media_dir = out_dir / "source-video"
    media_dir.mkdir(parents=True, exist_ok=True)
    destination = media_dir / f"original{suffix}"
    shutil.copyfile(source, destination)

    scene["reference_video"] = {
        "available": True,
        "label": "Original video",
        "role": "source clip",
        "path": _relative_path(destination, out_dir),
        "copied_from": str(source),
        "media": media,
        "trim_start_seconds": reference_sync.get("trim_start_seconds", 0.0),
        "frame_zero_offset_seconds": reference_sync.get("frame_zero_offset_seconds", 0.0),
        "playback_offset_seconds": 0.0,
        "sync_confidence": reference_sync.get("sync_confidence"),
    }
    labels = scene.setdefault("public_labels", [])
    if isinstance(labels, list) and "Original video" not in labels:
        labels.append("Original video")


def write_public_demo(
    *,
    playback_manifest_path: Path,
    recording_path: Path,
    g1_render_manifest_path: Path | None = None,
    use_rerun_sdk: bool = False,
) -> PublicDemoWriteResult:
    out_dir = recording_path.parent
    validate_output_dir(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scene = build_scene_timeline(
        playback_manifest_path=playback_manifest_path,
        g1_render_manifest_path=g1_render_manifest_path,
    )

    scene_path = out_dir / "scene.json"
    screenshot_path = out_dir / "screenshot.svg"
    html_path = out_dir / "index.html"
    manifest_path = out_dir / "manifest.json"

    _attach_public_g1_replay_frames(
        scene,
        g1_render_manifest_path=g1_render_manifest_path,
        out_dir=out_dir,
    )
    _attach_public_reference_video(
        scene,
        playback_manifest_path=playback_manifest_path,
        out_dir=out_dir,
    )
    _write_json(scene_path, scene)
    if use_rerun_sdk:
        recording = _write_rerun_recording(scene, recording_path)
    else:
        recording = {
            "schema": RERUN_RECORDING_EXPORT_SCHEMA,
            "actual_rerun_rrd": False,
            "format": "json_fallback_with_rrd_extension",
            "reason": "rerun-sdk is not a default project dependency; this artifact preserves the scene/timeline contract for the optional Rerun exporter",
            "scene": scene,
        }
        _write_json(recording_path, recording)
    screenshot_path.write_text(_render_screenshot_svg(scene), encoding="utf-8")

    surface_key = _surface_layer_key(scene.get("surface_proxy"))
    g1_meta = scene.get("track_metadata", {}).get("g1", {})
    render_evidence = scene.get("render_evidence") or {}
    g1_sequence = scene.get("g1_render_frame_sequence") or {}
    actual_g1_replay = bool(g1_sequence.get("actual_g1_model_replay"))
    g1_panel_label = (
        "Unitree G1 MuJoCo model replay"
        if actual_g1_replay
        else "Unitree G1 schematic evidence"
    )
    g1_visual_style = (
        "mujoco-png-frame-sequence.v1"
        if actual_g1_replay
        else "robot-body-schematic.v1"
    )
    reference_video = scene.get("reference_video") or {}
    reference_video_available = bool(
        isinstance(reference_video, dict)
        and reference_video.get("available")
        and reference_video.get("path")
    )
    teaching_layout = (
        "source_video_left_smplx_center_g1_right"
        if reference_video_available
        else "split_smplx_left_g1_right"
    )
    fixture_label = "fixture-only" if scene["fixture_only"] else "real-artifact"
    manifest = {
        "schema": PUBLIC_DEMO_SCHEMA,
        "fixture_only": bool(scene["fixture_only"]),
        "html": _relative_path(html_path, manifest_path.parent),
        "scene": _relative_path(scene_path, manifest_path.parent),
        "recording": _relative_path(recording_path, manifest_path.parent),
        "screenshot": _relative_path(screenshot_path, manifest_path.parent),
        "source_manifests": scene["source_manifests"],
        "scoring_source": "smplx",
        "tracks": {
            "smplx": {"label": "SMPL-X teacher", "scoring_allowed": True},
            "g1": {"label": g1_panel_label, "scoring_allowed": False},
        },
        "teaching_html": {
            "profile": TWO_PANEL_TEACHING_HTML_PROFILE,
            "layout": teaching_layout,
            "interactive": True,
            "synchronized_replay": True,
            "controls": ["play_pause", "timeline_slider"],
            "panels": {
                **(
                    {
                        "source": {
                            "track": "reference_video",
                            "label": "Original video",
                            "scoring_allowed": False,
                        }
                    }
                    if reference_video_available
                    else {}
                ),
                "left": {
                    "track": "smplx",
                    "label": "SMPL-X skeleton teaching track",
                    "scoring_allowed": True,
                },
                "right": {
                    "track": "g1",
                    "label": g1_panel_label,
                    "scoring_allowed": False,
                },
            },
            "panel_order": ["source", "smplx", "g1"] if reference_video_available else ["smplx", "g1"],
            "reference_video": {
                "available": reference_video_available,
                "label": "Original video",
                "path": reference_video.get("path") if isinstance(reference_video, dict) else None,
                "trim_start_seconds": reference_video.get("trim_start_seconds")
                if isinstance(reference_video, dict)
                else None,
                "frame_zero_offset_seconds": reference_video.get("frame_zero_offset_seconds")
                if isinstance(reference_video, dict)
                else None,
                "playback_offset_seconds": reference_video.get("playback_offset_seconds")
                if isinstance(reference_video, dict)
                else None,
            },
            "g1_replay": {
                "robot": g1_meta.get("robot"),
                "track_fixture_only": bool(g1_meta.get("fixture_only")),
                "track_derivation": g1_meta.get("derivation"),
                "pose_stream": g1_meta.get("pose_stream"),
                "model_fixture_only": render_evidence.get("model_fixture_only"),
                "renderer_backend": (render_evidence.get("renderer") or {}).get("backend")
                if isinstance(render_evidence.get("renderer"), dict)
                else None,
                "visual_style": g1_visual_style,
                "actual_g1_model_replay": actual_g1_replay,
                "rendered_frame_count": g1_sequence.get("frame_count", 0),
                "rendered_frame_paths": g1_sequence.get("paths", []),
            },
        },
        "routine_feedback": {
            "available": bool(scene.get("routine_review")),
            "anchor_count": len(scene.get("feedback_anchor_labels", [])),
            "scoring_source": "smplx",
        },
        "surface_layers": {
            surface_key: {
                "available": bool(scene.get("surface_proxy")),
                "surface_kind": scene.get("surface_proxy", {}).get("surface_kind")
                if scene.get("surface_proxy")
                else None,
                "label": scene.get("surface_proxy", {}).get("label") if scene.get("surface_proxy") else None,
                "licensed_smplx_mesh": bool(
                    scene.get("surface_proxy", {}).get("licensed_smplx_mesh", False)
                    if scene.get("surface_proxy")
                    else False
                ),
                "scoring_allowed": False,
            }
        },
        "rerun": {
            "target": "Rerun Web Viewer",
            "actual_rrd": bool(recording["actual_rerun_rrd"]),
            "sdk_version": recording.get("sdk_version"),
            "fallback_reason": None if recording["actual_rerun_rrd"] else "rerun-sdk not requested",
        },
        "visual_smoke_expectations": {
            "required_labels": [
                "SMPL-X skeleton teaching track",
                g1_panel_label,
                "Synchronized timeline",
                fixture_label,
                "Routine feedback",
                *(["Original video"] if reference_video_available else []),
                *([scene["surface_proxy"]["label"]] if scene.get("surface_proxy") else []),
            ],
            "nonblank_artifacts": ["index.html", "screenshot.svg"],
        },
    }
    _write_json(manifest_path, manifest)
    html_path.write_text(_render_public_html(scene, manifest), encoding="utf-8")
    return PublicDemoWriteResult(
        html_path=html_path,
        manifest_path=manifest_path,
        scene_path=scene_path,
        recording_path=recording_path,
        screenshot_path=screenshot_path,
    )


def _resolve_manifest_path(public_demo: Path) -> Path:
    if public_demo.is_file():
        return public_demo
    return public_demo / "manifest.json"


def _require_nonblank(path: Path) -> str:
    if not path.exists():
        raise ValueError(f"public demo artifact is missing: {path}")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"public demo artifact is blank: {path}")
    return text


def _require_nonblank_bytes(path: Path) -> bytes:
    if not path.exists():
        raise ValueError(f"public demo artifact is missing: {path}")
    payload = path.read_bytes()
    if not payload:
        raise ValueError(f"public demo artifact is blank: {path}")
    return payload


def smoke_check_public_demo(public_demo: Path) -> PublicDemoSmokeResult:
    manifest_path = _resolve_manifest_path(public_demo)
    manifest = _load_json(manifest_path)
    require_schema(manifest, PUBLIC_DEMO_SCHEMA, "public-demo manifest")
    if manifest.get("scoring_source") != "smplx":
        raise ValueError("public demo must keep SMPL-X as scoring_source")
    if manifest.get("tracks", {}).get("g1", {}).get("scoring_allowed"):
        raise ValueError("public demo cannot allow G1 scoring")
    teaching_html = manifest.get("teaching_html")
    if not isinstance(teaching_html, dict):
        raise ValueError("public demo manifest must define teaching_html metadata")
    if teaching_html.get("profile") != TWO_PANEL_TEACHING_HTML_PROFILE:
        raise ValueError("public demo teaching_html profile is not the two-panel teaching replay")
    teaching_layout = teaching_html.get("layout")
    valid_layouts = {"split_smplx_left_g1_right", "source_video_left_smplx_center_g1_right"}
    if teaching_layout not in valid_layouts:
        raise ValueError("public demo teaching_html layout must declare a supported synchronized replay layout")
    if teaching_html.get("interactive") is not True or teaching_html.get("synchronized_replay") is not True:
        raise ValueError("public demo teaching_html must be interactive and synchronized")
    reference_video = teaching_html.get("reference_video")
    if not isinstance(reference_video, dict):
        raise ValueError("public demo teaching_html must define reference_video metadata")
    reference_video_available = bool(reference_video.get("available"))
    if reference_video_available and teaching_layout != "source_video_left_smplx_center_g1_right":
        raise ValueError("reference-video public demo must use the source/SMPL-X/G1 layout")
    if not reference_video_available and teaching_layout != "split_smplx_left_g1_right":
        raise ValueError("public demo without reference video must use the SMPL-X/G1 layout")
    g1_replay = teaching_html.get("g1_replay")
    if not isinstance(g1_replay, dict):
        raise ValueError("public demo teaching_html must define g1_replay metadata")
    actual_g1_replay = bool(g1_replay.get("actual_g1_model_replay"))
    if actual_g1_replay:
        if g1_replay.get("visual_style") != "mujoco-png-frame-sequence.v1":
            raise ValueError("actual G1 replay must use the MuJoCo PNG frame-sequence visual style")
        if not isinstance(g1_replay.get("rendered_frame_paths"), list) or not g1_replay["rendered_frame_paths"]:
            raise ValueError("actual G1 replay must expose rendered frame paths")
    elif teaching_html.get("panels", {}).get("right", {}).get("label") != "Unitree G1 schematic evidence":
        raise ValueError("non-actual G1 public demo must label the right panel as schematic evidence")

    required_labels = manifest.get("visual_smoke_expectations", {}).get("required_labels", [])
    if not required_labels:
        raise ValueError("public demo manifest must define required visual smoke labels")

    html_path = manifest_path.parent / manifest["html"]
    scene_path = manifest_path.parent / manifest["scene"]
    recording_path = manifest_path.parent / manifest["recording"]
    screenshot_path = manifest_path.parent / manifest["screenshot"]
    html = _require_nonblank(html_path)
    scene = _load_json(scene_path)
    require_schema(scene, SCENE_TIMELINE_SCHEMA, "scene/timeline manifest")
    checked_extra_paths: list[Path] = []
    if reference_video_available:
        source_reference = reference_video.get("path")
        if not isinstance(source_reference, str) or not source_reference:
            raise ValueError("reference-video public demo must expose a copied video path")
        source_path = manifest_path.parent / source_reference
        _require_nonblank_bytes(source_path)
        checked_extra_paths.append(source_path)
        scene_reference_video = scene.get("reference_video")
        if not isinstance(scene_reference_video, dict) or scene_reference_video.get("available") is not True:
            raise ValueError("scene must expose the copied reference video")
    if actual_g1_replay:
        sequence = scene.get("g1_render_frame_sequence")
        if not isinstance(sequence, dict) or sequence.get("actual_g1_model_replay") is not True:
            raise ValueError("scene must expose the actual G1 replay frame sequence")
        if sequence.get("frame_count") != len(g1_replay["rendered_frame_paths"]):
            raise ValueError("actual G1 replay frame counts differ between scene and public manifest")
        for reference in g1_replay["rendered_frame_paths"]:
            if not isinstance(reference, str) or not reference:
                raise ValueError("actual G1 replay rendered frame paths must be non-empty strings")
            frame_path = manifest_path.parent / reference
            _require_nonblank_bytes(frame_path)
            checked_extra_paths.append(frame_path)
    if manifest.get("rerun", {}).get("actual_rrd"):
        recording_bytes = _require_nonblank_bytes(recording_path)
        if recording_bytes.startswith(b"{"):
            raise ValueError("public demo manifest claims actual Rerun .rrd but recording is JSON")
    else:
        recording = _load_json(recording_path)
        require_schema(recording, RERUN_RECORDING_EXPORT_SCHEMA, "Rerun recording export")
    screenshot = _require_nonblank(screenshot_path)

    smoke_text = "\n".join([html, screenshot])
    missing = [label for label in required_labels if label not in smoke_text]
    if missing:
        raise ValueError(f"public demo visual smoke labels are missing: {', '.join(missing)}")
    required_html_fragments = [
        f'data-teaching-html-profile="{TWO_PANEL_TEACHING_HTML_PROFILE}"',
        'data-panel="smplx"',
        'data-panel="g1"',
        'id="timeline"',
        "drawRobotModel",
    ]
    if reference_video_available:
        required_html_fragments.extend([
            'data-panel="source"',
            'id="referenceVideo"',
            "syncReferenceVideo",
        ])
    missing_fragments = [fragment for fragment in required_html_fragments if fragment not in html]
    if missing_fragments:
        raise ValueError("public demo HTML is missing interactive replay controls")

    return PublicDemoSmokeResult(
        manifest_path=manifest_path,
        checked_paths=[html_path, scene_path, recording_path, screenshot_path, *checked_extra_paths],
    )
