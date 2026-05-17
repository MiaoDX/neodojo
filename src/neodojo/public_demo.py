from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import PLAYBACK_SCHEMA, PUBLIC_DEMO_SCHEMA, require_schema
from .fixtures import BONES, TRAJECTORY_JOINTS
from .g1_render import G1_RENDER_SCHEMA
from .g1_visual import load_g1_track_frames
from .motion_contract import _relative_path, _write_json, load_motion_record_frames, validate_output_dir
from .smplx_surface import load_smplx_surface_proxy

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
    surface_layers = playback.get("surface_layers", {})
    if isinstance(surface_layers, dict):
        smplx_proxy = surface_layers.get("smplx_proxy")
        if isinstance(smplx_proxy, dict) and smplx_proxy.get("manifest"):
            surface_manifest_path = _resolve_relative(playback_manifest_path, smplx_proxy["manifest"])
            surface_manifest, surface_frames = load_smplx_surface_proxy(surface_manifest_path)
            if len(surface_frames) != len(smplx_frames):
                raise ValueError("SMPL-X surface proxy must match playback frame count")
            surface_proxy = {
                "label": "SMPL-X surface proxy",
                "surface_kind": surface_manifest.get("surface_kind"),
                "licensed_smplx_mesh": False,
                "scoring_allowed": False,
                "frames": surface_frames,
                "manifest": smplx_proxy["manifest"],
            }

    render_manifest = _load_optional_render_manifest(g1_render_manifest_path)
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
                "label": "Unitree G1 visual",
                "role": g1_manifest["role"],
                "scoring_allowed": False,
                "frames": g1_frames,
            },
        },
        "annotations": annotations,
        "routine_review": routine_review,
        "feedback_anchor_labels": feedback_anchor_labels,
        "surface_proxy": surface_proxy,
        "reference_video_sync": playback.get("reference_video_sync"),
        "feedback": playback.get("feedback"),
        "render_evidence": render_manifest,
        "public_labels": [
            "fixture-only" if fixture_only else "real-artifact",
            "SMPL-X teacher",
            "Unitree G1 visual",
            "G1 non-scoring",
            "Routine feedback",
            *(["SMPL-X surface proxy"] if surface_proxy else []),
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


def _surface_svg(surface_proxy: dict[str, Any] | None, smplx_track: dict[str, Any], view: str, frame_index: int) -> str:
    if not surface_proxy:
        return ""
    frame = smplx_track["frames"][frame_index]
    points = [_project(point, view) for point in frame.values()]
    bounds = _bounds(points)
    surface_frame = surface_proxy["frames"][frame_index]
    lines = []
    for capsule in surface_frame.get("capsules", []):
        start = capsule.get("start")
        end = capsule.get("end")
        if not isinstance(start, list) or not isinstance(end, list):
            continue
        x1, y1 = _scale(_project(start, view), bounds)
        x2, y2 = _scale(_project(end, view), bounds)
        width = max(8, float(capsule.get("radius_m", 0.04)) * 180)
        lines.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#147c72" stroke-opacity="0.16" stroke-width="{width:.1f}" stroke-linecap="round"/>'
        )
    return "\n".join(lines)


def _render_screenshot_svg(scene: dict[str, Any]) -> str:
    key_frame = int(scene["key_frame"])
    surface = _surface_svg(scene.get("surface_proxy"), scene["tracks"]["smplx"], "front", key_frame)
    smplx = _track_svg(scene["tracks"]["smplx"], "front", key_frame, "#147c72")
    g1 = _track_svg(scene["tracks"]["g1"], "front", key_frame, "#b84e32")
    fixture_label = "FIXTURE-ONLY" if scene["fixture_only"] else "REAL ARTIFACT"
    feedback = scene.get("feedback") or {}
    anchors = scene.get("feedback_anchor_labels") or []
    anchor_text = ", ".join(anchors[:3]) if anchors else "none"
    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" role="img">',
            "<style>text{font-family:Inter,Arial,sans-serif}.title{font-size:30px;font-weight:760;fill:#17212b}.muted{font-size:16px;fill:#66717f}.badge{font-size:14px;font-weight:760;fill:#b54708}</style>",
            '<rect width="1280" height="720" fill="#eef2f6"/>',
            '<rect x="32" y="28" width="1216" height="86" rx="8" fill="#ffffff" stroke="#d8e0e8"/>',
            '<text x="56" y="68" class="title">neodojo public fixture demo</text>',
            f'<text x="56" y="94" class="muted">SMPL-X teacher + Unitree G1 visual - frame {key_frame + 1}</text>',
            f'<text x="1080" y="66" class="badge">{fixture_label}</text>',
            '<rect x="48" y="144" width="560" height="500" rx="8" fill="#ffffff" stroke="#d8e0e8"/>',
            '<rect x="672" y="144" width="560" height="500" rx="8" fill="#ffffff" stroke="#d8e0e8"/>',
            '<text x="72" y="184" class="title">SMPL-X teacher</text>',
            '<text x="696" y="184" class="title">Unitree G1 visual</text>',
            f'<g transform="translate(80 210)">{surface}{smplx}</g>',
            f'<g transform="translate(704 210)">{g1}</g>',
            f'<text x="56" y="684" class="muted">Scoring source: SMPL-X. G1 scoring allowed: false. Feedback passed: {feedback.get("passed")}</text>',
            f'<text x="696" y="684" class="muted">Routine feedback anchors: {anchor_text}. SMPL-X surface proxy: {bool(scene.get("surface_proxy"))}</text>',
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
    surface_proxy = scene.get("surface_proxy")
    surface_label = "SMPL-X surface proxy" if surface_proxy else "off"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>neodojo public fixture demo</title>
  <style>
    :root {{ --bg: #eef2f6; --panel: #fff; --ink: #17212b; --muted: #66717f; --line: #d8e0e8; --smplx: #147c72; --g1: #b84e32; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-height: 100vh; background: var(--bg); color: var(--ink); font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
    header {{ display: flex; justify-content: space-between; gap: 16px; align-items: center; padding: 18px 22px; background: var(--panel); border-bottom: 1px solid var(--line); }}
    h1, h2, p {{ margin: 0; }}
    h1 {{ font-size: 20px; }}
    .badge {{ border: 1px solid var(--line); border-radius: 999px; padding: 7px 11px; color: #b54708; background: #fff8f2; font-size: 12px; font-weight: 800; }}
    main {{ display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 16px; padding: 16px; }}
    .stage {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }}
    .stage img {{ display: block; width: 100%; background: #fbfcfe; }}
    aside {{ display: grid; align-content: start; gap: 12px; }}
    section {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; }}
    h2 {{ font-size: 15px; margin-bottom: 10px; }}
    .metric {{ display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; border-top: 1px solid var(--line); color: var(--muted); font-size: 13px; }}
    .metric strong {{ color: var(--ink); text-align: right; }}
    a {{ color: #2c6fbb; }}
    @media (max-width: 900px) {{ main {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <header>
    <h1>neodojo public demo</h1>
    <div class="badge">{fixture_note}</div>
  </header>
  <main>
    <div class="stage"><img src="screenshot.svg" alt="SMPL-X teacher and Unitree G1 visual fixture demo"></div>
    <aside>
      <section>
        <h2>Tracks</h2>
        <div class="metric"><span>Teaching source</span><strong>SMPL-X teacher</strong></div>
        <div class="metric"><span>Surface layer</span><strong>{surface_label}</strong></div>
        <div class="metric"><span>Visual companion</span><strong>Unitree G1 visual</strong></div>
        <div class="metric"><span>G1 scoring</span><strong>false</strong></div>
      </section>
      <section>
        <h2>Artifacts</h2>
        <div class="metric"><span>Scene</span><strong>{manifest["scene"]}</strong></div>
        <div class="metric"><span>Recording</span><strong>{manifest["recording"]}</strong></div>
        <div class="metric"><span>Actual Rerun SDK .rrd</span><strong>{manifest["rerun"]["actual_rrd"]}</strong></div>
      </section>
      <section>
        <h2>Routine feedback</h2>
        <div class="metric"><span>Anchors</span><strong>{anchor_text}</strong></div>
        <div class="metric"><span>Terms</span><strong>{routine_summary.get("passed_terms", 0)} / {routine_summary.get("term_count", 0)}</strong></div>
        <div class="metric"><span>Source</span><strong>SMPL-X</strong></div>
      </section>
    </aside>
  </main>
  <script>const PUBLIC_DEMO = {payload};</script>
</body>
</html>
"""


def write_public_demo(
    *,
    playback_manifest_path: Path,
    recording_path: Path,
    g1_render_manifest_path: Path | None = None,
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

    recording = {
        "schema": RERUN_RECORDING_EXPORT_SCHEMA,
        "actual_rerun_rrd": False,
        "format": "json_fallback_with_rrd_extension",
        "reason": "rerun-sdk is not a project dependency yet; this artifact preserves the scene/timeline contract for the future Rerun exporter",
        "scene": scene,
    }
    _write_json(scene_path, scene)
    _write_json(recording_path, recording)
    screenshot_path.write_text(_render_screenshot_svg(scene), encoding="utf-8")

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
            "g1": {"label": "Unitree G1 visual", "scoring_allowed": False},
        },
        "routine_feedback": {
            "available": bool(scene.get("routine_review")),
            "anchor_count": len(scene.get("feedback_anchor_labels", [])),
            "scoring_source": "smplx",
        },
        "surface_layers": {
            "smplx_proxy": {
                "available": bool(scene.get("surface_proxy")),
                "surface_kind": scene.get("surface_proxy", {}).get("surface_kind")
                if scene.get("surface_proxy")
                else None,
                "licensed_smplx_mesh": False,
                "scoring_allowed": False,
            }
        },
        "rerun": {
            "target": "Rerun Web Viewer",
            "actual_rrd": False,
            "sdk_version": None,
            "fallback_reason": "rerun-sdk not installed",
        },
        "visual_smoke_expectations": {
            "required_labels": [
                "SMPL-X teacher",
                "Unitree G1 visual",
                "fixture-only",
                "Routine feedback",
                *(["SMPL-X surface proxy"] if scene.get("surface_proxy") else []),
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


def smoke_check_public_demo(public_demo: Path) -> PublicDemoSmokeResult:
    manifest_path = _resolve_manifest_path(public_demo)
    manifest = _load_json(manifest_path)
    require_schema(manifest, PUBLIC_DEMO_SCHEMA, "public-demo manifest")
    if manifest.get("scoring_source") != "smplx":
        raise ValueError("public demo must keep SMPL-X as scoring_source")
    if manifest.get("tracks", {}).get("g1", {}).get("scoring_allowed"):
        raise ValueError("public demo cannot allow G1 scoring")

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
    recording = _load_json(recording_path)
    require_schema(recording, RERUN_RECORDING_EXPORT_SCHEMA, "Rerun recording export")
    screenshot = _require_nonblank(screenshot_path)

    smoke_text = "\n".join([html, screenshot])
    missing = [label for label in required_labels if label not in smoke_text]
    if missing:
        raise ValueError(f"public demo visual smoke labels are missing: {', '.join(missing)}")

    return PublicDemoSmokeResult(
        manifest_path=manifest_path,
        checked_paths=[html_path, scene_path, recording_path, screenshot_path],
    )
