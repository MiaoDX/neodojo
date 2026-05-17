from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .fixtures import BONES
from .motion_contract import _relative_path, _write_json, validate_output_dir
from .public_demo import build_scene_timeline

VISER_RUNTIME_SCHEMA = "neodojo.viser_runtime.v1"


@dataclass(frozen=True)
class ViserRuntimeWriteResult:
    manifest_path: Path
    scene_path: Path
    screenshot_paths: dict[str, Path]


@dataclass(frozen=True)
class ViserServeResult:
    manifest_path: Path
    scene_path: Path
    screenshot_paths: dict[str, Path]
    url: str
    server: Any | None = None


def _load_viser_sdk() -> Any:
    try:
        import viser
    except ModuleNotFoundError as exc:
        raise ValueError(
            "Viser runtime requires the optional viser package; install with "
            "`python -m pip install '.[viser]'` or `python -m pip install viser`"
        ) from exc
    return viser


def _camera_presets() -> dict[str, dict[str, Any]]:
    return {
        "front": {
            "position": [0.0, -4.0, 1.35],
            "look_at": [0.0, 0.0, 1.2],
            "source_projection_axes": ["x", "y"],
        },
        "side": {
            "position": [4.0, 0.0, 1.35],
            "look_at": [0.0, 0.0, 1.2],
            "source_projection_axes": ["z", "y"],
        },
        "top": {
            "position": [0.0, -0.2, 5.0],
            "look_at": [0.0, 0.0, 1.0],
            "source_projection_axes": ["x", "z"],
        },
    }


def _project_viser_point(point: list[float], view: str) -> tuple[float, float]:
    x, y, z = point
    if view == "front":
        return x, z
    if view == "side":
        return y, z
    if view == "top":
        return x, y
    raise ValueError(f"unsupported Viser preview view: {view}")


def _bounds(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), max(xs), min(ys), max(ys)


def _scale(point: tuple[float, float], bounds: tuple[float, float, float, float]) -> tuple[float, float]:
    min_x, max_x, min_y, max_y = bounds
    width = max(max_x - min_x, 0.1)
    height = max(max_y - min_y, 0.1)
    scale = min(420 / width, 300 / height)
    x = 320 + (point[0] - ((min_x + max_x) / 2)) * scale
    y = 220 - (point[1] - ((min_y + max_y) / 2)) * scale
    return x, y


def _preview_bounds(scene: dict[str, Any], view: str, frame_index: int) -> tuple[float, float, float, float]:
    projected = []
    for track_id, x_offset in [("smplx", -0.55), ("g1", 0.55)]:
        frame = scene["tracks"][track_id]["frames"][frame_index]
        projected.extend(_project_viser_point(_to_viser_point(point, x_offset=x_offset), view) for point in frame.values())
    return _bounds(projected)


def _render_preview_track(
    scene: dict[str, Any],
    *,
    track_id: str,
    x_offset: float,
    color: str,
    view: str,
    frame_index: int,
    bounds: tuple[float, float, float, float],
) -> str:
    frame = scene["tracks"][track_id]["frames"][frame_index]
    lines = []
    for start, end in BONES:
        if start not in frame or end not in frame:
            continue
        start_point = _project_viser_point(_to_viser_point(frame[start], x_offset=x_offset), view)
        end_point = _project_viser_point(_to_viser_point(frame[end], x_offset=x_offset), view)
        x1, y1 = _scale(start_point, bounds)
        x2, y2 = _scale(end_point, bounds)
        lines.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="4" stroke-linecap="round"/>'
        )
    joints = []
    for point in frame.values():
        x, y = _scale(_project_viser_point(_to_viser_point(point, x_offset=x_offset), view), bounds)
        joints.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"/>')
    return "\n".join(lines + joints)


def _render_viser_preview_svg(scene: dict[str, Any], view: str) -> str:
    frame_count = int((scene.get("timing") or {}).get("frame_count") or len(scene["tracks"]["smplx"]["frames"]))
    frame_index = min(max(0, int(scene.get("key_frame", 0))), max(0, frame_count - 1))
    bounds = _preview_bounds(scene, view, frame_index)
    smplx = _render_preview_track(
        scene,
        track_id="smplx",
        x_offset=-0.55,
        color="#147c72",
        view=view,
        frame_index=frame_index,
        bounds=bounds,
    )
    g1 = _render_preview_track(
        scene,
        track_id="g1",
        x_offset=0.55,
        color="#b84e32",
        view=view,
        frame_index=frame_index,
        bounds=bounds,
    )
    fixture_label = "fixture-only" if scene["fixture_only"] else "real-artifact"
    title = f"Viser {view} preview"
    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="640" viewBox="0 0 640 440" role="img">',
            "<style>text{font-family:Inter,Arial,sans-serif}.title{font-size:18px;font-weight:760;fill:#17212b}.muted{font-size:12px;fill:#66717f}.badge{font-size:12px;font-weight:760;fill:#b54708}</style>",
            '<rect width="640" height="440" fill="#eef2f6"/>',
            '<rect x="18" y="18" width="604" height="404" rx="8" fill="#ffffff" stroke="#d8e0e8"/>',
            f'<text x="40" y="50" class="title">{title}</text>',
            f'<text x="40" y="72" class="muted">Frame {frame_index + 1} / {frame_count}. Scoring source: SMPL-X teacher.</text>',
            f'<text x="500" y="50" class="badge">{fixture_label}</text>',
            f'<g>{smplx}</g>',
            f'<g>{g1}</g>',
            '<circle cx="40" cy="386" r="5" fill="#147c72"/>',
            '<text x="54" y="390" class="muted">SMPL-X teacher</text>',
            '<circle cx="190" cy="386" r="5" fill="#b84e32"/>',
            '<text x="204" y="390" class="muted">Unitree G1 visual</text>',
            '<text x="40" y="412" class="muted">G1 scoring allowed: false. Preview generated from the Viser scene/timeline contract.</text>',
            "</svg>",
        ]
    )


def _write_viser_preview_screenshots(out_dir: Path, scene: dict[str, Any]) -> dict[str, Path]:
    screenshot_dir = out_dir / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        view: screenshot_dir / f"{view}.svg"
        for view in ("front", "side", "top")
    }
    for view, path in paths.items():
        path.write_text(_render_viser_preview_svg(scene, view), encoding="utf-8")
    return paths


def _feedback_drilldown(scene: dict[str, Any]) -> list[dict[str, Any]]:
    annotations = scene.get("annotations") or {}
    keyframes = annotations.get("keyframes") if isinstance(annotations, dict) else []
    if not isinstance(keyframes, list):
        return []
    items: list[dict[str, Any]] = []
    for index, keyframe in enumerate(keyframes):
        if not isinstance(keyframe, dict):
            continue
        name = keyframe.get("name")
        if not isinstance(name, str):
            continue
        terms = keyframe.get("terms") if isinstance(keyframe.get("terms"), list) else []
        term_results = keyframe.get("term_results") if isinstance(keyframe.get("term_results"), list) else []
        constraints = keyframe.get("constraints") if isinstance(keyframe.get("constraints"), list) else []
        items.append(
            {
                "id": f"feedback_{index}",
                "label": name,
                "frame": int(keyframe.get("frame", 0)),
                "primary": bool(keyframe.get("primary")),
                "passed": bool(keyframe.get("passed")),
                "selected_joints": [
                    str(joint)
                    for joint in keyframe.get("selected_joints", [])
                    if isinstance(joint, str)
                ],
                "terms": [str(term) for term in terms if isinstance(term, str)],
                "term_results": [result for result in term_results if isinstance(result, dict)],
                "constraints": [result for result in constraints if isinstance(result, dict)],
            }
        )
    return items


def _production_teaching_ui(scene: dict[str, Any], frame_count: int) -> dict[str, Any]:
    feedback_items = _feedback_drilldown(scene)
    has_surface_proxy = bool(scene.get("surface_proxy"))
    return {
        "profile": "neodojo.viser_teaching_ui.v1",
        "status": "production_review_loop_contract",
        "review_loop": [
            {
                "id": "inspect_motion",
                "label": "Inspect synchronized SMPL-X and Unitree G1 motion",
                "required_controls": ["frame", "step_previous", "step_next", "camera_presets"],
            },
            {
                "id": "jump_to_feedback",
                "label": "Jump to a feedback anchor and inspect SMPL-X evidence",
                "required_controls": ["feedback_anchor_buttons", "feedback_drilldown"],
            },
            {
                "id": "compare_layers",
                "label": "Compare teacher, robot visual track, trajectories, and surface layers",
                "required_controls": ["layer_visibility"],
            },
        ],
        "control_groups": [
            {
                "id": "timeline",
                "label": "Timeline",
                "controls": ["frame", "step_previous", "step_next", "playback_speed", "reset_key_frame"],
            },
            {
                "id": "camera",
                "label": "Camera",
                "controls": [f"camera_{name}" for name in _camera_presets()],
            },
            {
                "id": "layers",
                "label": "Layers",
                "controls": [
                    "show_smplx_teacher",
                    "show_unitree_g1_visual",
                    "show_trajectories",
                    *(["show_smplx_surface_proxy"] if has_surface_proxy else []),
                ],
            },
            {
                "id": "feedback",
                "label": "Feedback",
                "controls": [item["id"] for item in feedback_items],
            },
        ],
        "timeline": {
            "frame_count": frame_count,
            "step": 1,
            "speed_options": [0.25, 0.5, 1.0, 1.5, 2.0],
            "initial_frame": int(scene.get("key_frame", 0)),
        },
        "layer_visibility": {
            "show_smplx_teacher": True,
            "show_unitree_g1_visual": True,
            "show_trajectories": True,
            "show_smplx_surface_proxy": has_surface_proxy,
        },
        "feedback_drilldown": feedback_items,
        "scoring_policy": {
            "scoring_source": "smplx",
            "g1_scoring_allowed": False,
            "surface_proxy_scoring_allowed": False,
        },
        "live_client_smoke": {
            "optional": True,
            "default_ci_required": False,
            "required_labels": [
                "SMPL-X teacher",
                "Unitree G1 visual",
                "Scoring source: SMPL-X",
                "Routine feedback",
            ],
        },
    }


def build_viser_runtime_manifest(
    scene: dict[str, Any],
    *,
    scene_path: Path,
    manifest_path: Path,
    screenshot_paths: dict[str, Path] | None = None,
) -> dict[str, Any]:
    timing = scene.get("timing") or {}
    frame_count = int(timing.get("frame_count") or len(scene["tracks"]["smplx"]["frames"]))
    screenshot_paths = screenshot_paths or {}
    return {
        "schema": VISER_RUNTIME_SCHEMA,
        "runtime": {
            "target": "viser",
            "optional_dependency": "viser>=1.0,<2",
            "entrypoint": "neodojo demo serve-viser",
        },
        "scene": _relative_path(scene_path, manifest_path.parent),
        "fixture_only": bool(scene["fixture_only"]),
        "frame_count": frame_count,
        "initial_frame": int(scene.get("key_frame", 0)),
        "coordinate_transform": {
            "source_world_up_axis": (scene.get("coordinates") or {}).get("world_up_axis", "y"),
            "viser_world_up_axis": "z",
            "mapping": "source [x, y, z] -> viser [x, z, y]",
        },
        "camera_presets": _camera_presets(),
        "controls": [
            {"id": "frame", "kind": "slider", "min": 0, "max": max(0, frame_count - 1), "step": 1},
            {"id": "reset_key_frame", "kind": "button", "frame": int(scene.get("key_frame", 0))},
            *[
                {"id": f"camera_{name}", "kind": "camera_preset_button", "preset": name}
                for name in _camera_presets()
            ],
            {"id": "step_previous", "kind": "button", "step": -1},
            {"id": "step_next", "kind": "button", "step": 1},
            {
                "id": "playback_speed",
                "kind": "speed_slider",
                "min": 0.25,
                "max": 2.0,
                "step": 0.25,
                "default": 1.0,
            },
            {"id": "show_smplx_teacher", "kind": "visibility_toggle", "target": "smplx", "default": True},
            {"id": "show_unitree_g1_visual", "kind": "visibility_toggle", "target": "g1", "default": True},
            {"id": "show_trajectories", "kind": "visibility_toggle", "target": "trajectories", "default": True},
            *(
                [
                    {
                        "id": "show_smplx_surface_proxy",
                        "kind": "visibility_toggle",
                        "target": "smplx_surface_proxy",
                        "default": True,
                    }
                ]
                if scene.get("surface_proxy")
                else []
            ),
            *[
                {
                    "id": f"anchor_{index}",
                    "kind": "annotation_keyframe_button",
                    "label": str(keyframe.get("name")),
                    "frame": int(keyframe.get("frame", 0)),
                }
                for index, keyframe in enumerate((scene.get("annotations") or {}).get("keyframes", []))
                if isinstance(keyframe, dict) and isinstance(keyframe.get("name"), str)
            ],
        ],
        "overlays": {
            "tracks": [
                {"track_id": "smplx", "label": "SMPL-X teacher", "scoring_allowed": True},
                {"track_id": "g1", "label": "Unitree G1 visual", "scoring_allowed": False},
            ],
            "trajectory_joints": scene.get("trajectory_joints", []),
            "feedback_anchor_labels": scene.get("feedback_anchor_labels", []),
            "public_labels": scene.get("public_labels", []),
        },
        "teaching_ui": _production_teaching_ui(scene, frame_count),
        "visual_smoke": {
            "kind": "generated_svg_multi_camera_preview",
            "views": ["front", "side", "top"],
            "screenshot_paths": {
                view: _relative_path(path, manifest_path.parent)
                for view, path in screenshot_paths.items()
            },
            "required_labels": [
                "SMPL-X teacher",
                "Unitree G1 visual",
                "G1 scoring allowed: false",
            ],
        },
        "scoring_source": "smplx",
        "g1_scoring_allowed": False,
    }


def write_viser_runtime_contract(
    out_dir: Path,
    *,
    playback_manifest_path: Path,
    g1_render_manifest_path: Path | None = None,
) -> ViserRuntimeWriteResult:
    validate_output_dir(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scene = build_scene_timeline(
        playback_manifest_path=playback_manifest_path,
        g1_render_manifest_path=g1_render_manifest_path,
    )
    scene_path = out_dir / "scene.json"
    manifest_path = out_dir / "viser-runtime.json"
    screenshot_paths = _write_viser_preview_screenshots(out_dir, scene)
    _write_json(scene_path, scene)
    _write_json(
        manifest_path,
        build_viser_runtime_manifest(
            scene,
            scene_path=scene_path,
            manifest_path=manifest_path,
            screenshot_paths=screenshot_paths,
        ),
    )
    return ViserRuntimeWriteResult(
        manifest_path=manifest_path,
        scene_path=scene_path,
        screenshot_paths=screenshot_paths,
    )


def _to_viser_point(point: list[float], *, x_offset: float = 0.0) -> list[float]:
    x, y, z = point
    return [x + x_offset, z, y]


def _track_points(frame: dict[str, list[float]], *, x_offset: float) -> list[list[float]]:
    return [_to_viser_point(point, x_offset=x_offset) for point in frame.values()]


def _track_segments(frame: dict[str, list[float]], *, x_offset: float) -> list[list[list[float]]]:
    segments = []
    for start, end in BONES:
        if start in frame and end in frame:
            segments.append(
                [
                    _to_viser_point(frame[start], x_offset=x_offset),
                    _to_viser_point(frame[end], x_offset=x_offset),
                ]
            )
    return segments


def _trajectory_segments(track: dict[str, Any], joint: str, *, x_offset: float) -> list[list[list[float]]]:
    points = [
        _to_viser_point(frame[joint], x_offset=x_offset)
        for frame in track["frames"]
        if isinstance(frame, dict) and joint in frame
    ]
    return [[points[index], points[index + 1]] for index in range(len(points) - 1)]


def _clear_handles(handles: dict[str, Any]) -> None:
    for handle in handles.values():
        handle.remove()
    handles.clear()


def _populate_static_viser_scene(server: Any, np: Any, scene: dict[str, Any]) -> None:
    server.initial_camera.position = tuple(_camera_presets()["front"]["position"])
    server.initial_camera.look_at = tuple(_camera_presets()["front"]["look_at"])
    server.initial_camera.up = (0.0, 0.0, 1.0)

    server.scene.add_label(
        "/labels/scoring",
        "Scoring source: SMPL-X teacher. Unitree G1 is visual-only.",
        position=(-1.25, -0.9, 2.2),
    )
    for index, keyframe in enumerate((scene.get("annotations") or {}).get("keyframes", [])):
        if not isinstance(keyframe, dict):
            continue
        name = keyframe.get("name")
        frame_index = int(keyframe.get("frame", 0))
        selected_joints = keyframe.get("selected_joints", [])
        if not isinstance(name, str) or not isinstance(selected_joints, list):
            continue
        frames = scene["tracks"]["smplx"]["frames"]
        if frame_index < 0 or frame_index >= len(frames):
            continue
        anchor_joint = next(
            (joint for joint in selected_joints if isinstance(joint, str) and joint in frames[frame_index]),
            None,
        )
        if anchor_joint is None:
            continue
        position = _to_viser_point(frames[frame_index][anchor_joint], x_offset=-0.55)
        position[2] += 0.16 + (index * 0.04)
        server.scene.add_label(
            f"/annotations/{index}_{name.replace(' ', '_')}",
            f"{name} - frame {frame_index + 1}",
            position=tuple(position),
        )
    for track_id, x_offset, color in [
        ("smplx", -0.55, (20, 124, 114)),
        ("g1", 0.55, (184, 78, 50)),
    ]:
        track = scene["tracks"][track_id]
        for joint in scene.get("trajectory_joints", []):
            segments = _trajectory_segments(track, joint, x_offset=x_offset)
            if segments:
                server.scene.add_line_segments(
                    f"/trajectories/{track_id}/{joint}",
                    points=np.asarray(segments, dtype=float),
                    colors=color,
                    line_width=1.0,
                )


def _apply_camera_preset(client: Any, preset: dict[str, Any]) -> None:
    client.camera.position = tuple(preset["position"])
    client.camera.look_at = tuple(preset["look_at"])
    client.camera.up_direction = (0.0, 0.0, 1.0)
    client.flush()


def _apply_camera_preset_to_clients(server: Any, preset: dict[str, Any], event: Any) -> None:
    event_client = getattr(event, "client", None)
    if event_client is not None:
        _apply_camera_preset(event_client, preset)
        return
    for client in server.get_clients().values():
        _apply_camera_preset(client, preset)


def _render_viser_frame(
    server: Any,
    np: Any,
    scene: dict[str, Any],
    frame_index: int,
    handles: dict[str, Any],
    *,
    visible_tracks: dict[str, bool] | None = None,
) -> None:
    visible_tracks = visible_tracks or {"smplx": True, "g1": True}
    _clear_handles(handles)
    for track_id, x_offset, color, label in [
        ("smplx", -0.55, (20, 124, 114), "SMPL-X teacher"),
        ("g1", 0.55, (184, 78, 50), "Unitree G1 visual"),
    ]:
        if not visible_tracks.get(track_id, True):
            continue
        frame = scene["tracks"][track_id]["frames"][frame_index]
        handles[f"{track_id}_joints"] = server.scene.add_point_cloud(
            f"/live/{track_id}/joints",
            points=np.asarray(_track_points(frame, x_offset=x_offset), dtype=float),
            colors=color,
            point_size=0.045,
            point_shape="circle",
        )
        handles[f"{track_id}_bones"] = server.scene.add_line_segments(
            f"/live/{track_id}/bones",
            points=np.asarray(_track_segments(frame, x_offset=x_offset), dtype=float),
            colors=color,
            line_width=3.0,
        )
        handles[f"{track_id}_label"] = server.scene.add_label(
            f"/live/{track_id}/label",
            f"{label} - frame {frame_index + 1}",
            position=(x_offset - 0.45, -0.75, 2.05),
        )
    server.flush()


def serve_viser_runtime(
    *,
    playback_manifest_path: Path,
    out_dir: Path,
    g1_render_manifest_path: Path | None = None,
    host: str = "127.0.0.1",
    port: int = 8080,
    block: bool = True,
    stop_after_start: bool = False,
    verbose: bool = True,
) -> ViserServeResult:
    result = write_viser_runtime_contract(
        out_dir,
        playback_manifest_path=playback_manifest_path,
        g1_render_manifest_path=g1_render_manifest_path,
    )
    scene = build_scene_timeline(
        playback_manifest_path=playback_manifest_path,
        g1_render_manifest_path=g1_render_manifest_path,
    )
    viser = _load_viser_sdk()
    import numpy as np

    server = viser.ViserServer(host=host, port=port, label="neodojo teaching runtime", verbose=verbose)
    handles: dict[str, Any] = {}
    _populate_static_viser_scene(server, np, scene)

    frame_count = int((scene.get("timing") or {}).get("frame_count") or len(scene["tracks"]["smplx"]["frames"]))
    initial_frame = min(max(0, int(scene.get("key_frame", 0))), max(0, frame_count - 1))
    visible_tracks = {"smplx": True, "g1": True}
    _render_viser_frame(server, np, scene, initial_frame, handles, visible_tracks=visible_tracks)

    server.gui.add_markdown(
        "**neodojo fixture runtime**\n\nSMPL-X is the scoring source. Unitree G1 is visual-only."
    )
    teaching_ui = _production_teaching_ui(scene, frame_count)
    server.gui.add_markdown(
        "### Review loop\n"
        "1. Inspect the synchronized SMPL-X teacher and Unitree G1 visual tracks.\n"
        "2. Jump to feedback anchors and inspect the SMPL-X evidence.\n"
        "3. Toggle layers while preserving SMPL-X as the scoring source."
    )
    frame_slider = server.gui.add_slider(
        "Frame",
        min=0,
        max=max(0, frame_count - 1),
        step=1,
        initial_value=initial_frame,
    )
    previous_button = server.gui.add_button("Step previous")
    next_button = server.gui.add_button("Step next")
    server.gui.add_slider("Playback speed", min=0.25, max=2.0, step=0.25, initial_value=1.0)
    reset_button = server.gui.add_button("Reset to key frame")
    show_smplx = server.gui.add_checkbox("Show SMPL-X teacher", initial_value=True)
    show_g1 = server.gui.add_checkbox("Show Unitree G1 visual", initial_value=True)
    camera_buttons = {
        name: server.gui.add_button(f"Camera: {name.title()}")
        for name in _camera_presets()
    }
    anchor_buttons = []
    for keyframe in (scene.get("annotations") or {}).get("keyframes", []):
        if not isinstance(keyframe, dict) or not isinstance(keyframe.get("name"), str):
            continue
        anchor_buttons.append(
            (
                server.gui.add_button(f"Anchor: {keyframe['name']}"),
                min(max(0, int(keyframe.get("frame", 0))), max(0, frame_count - 1)),
            )
        )
    feedback_lines = []
    for item in teaching_ui["feedback_drilldown"]:
        state = "pass" if item["passed"] else "review"
        terms = ", ".join(item["terms"])
        feedback_lines.append(f"- {item['label']} - frame {item['frame'] + 1} - {state}: {terms}")
    if feedback_lines:
        server.gui.add_markdown("### Routine feedback\n" + "\n".join(feedback_lines))

    def _update_visible_tracks() -> None:
        visible_tracks["smplx"] = bool(show_smplx.value)
        visible_tracks["g1"] = bool(show_g1.value)

    def _render_current_frame() -> None:
        _update_visible_tracks()
        _render_viser_frame(
            server,
            np,
            scene,
            int(frame_slider.value),
            handles,
            visible_tracks=visible_tracks,
        )

    @frame_slider.on_update
    def _(_: Any) -> None:
        _render_current_frame()

    @show_smplx.on_update
    def _(_: Any) -> None:
        _render_current_frame()

    @show_g1.on_update
    def _(_: Any) -> None:
        _render_current_frame()

    @previous_button.on_click
    def _(_: Any) -> None:
        frame_slider.value = max(0, int(frame_slider.value) - 1)
        _render_current_frame()

    @next_button.on_click
    def _(_: Any) -> None:
        frame_slider.value = min(max(0, frame_count - 1), int(frame_slider.value) + 1)
        _render_current_frame()

    @reset_button.on_click
    def _(_: Any) -> None:
        frame_slider.value = initial_frame
        _render_current_frame()

    for name, button in camera_buttons.items():
        preset = _camera_presets()[name]

        @button.on_click
        def _(_: Any, preset: dict[str, Any] = preset) -> None:
            _apply_camera_preset_to_clients(server, preset, _)

    for button, target_frame in anchor_buttons:

        @button.on_click
        def _(_: Any, target_frame: int = target_frame) -> None:
            frame_slider.value = target_frame
            _render_current_frame()

    url = f"http://{host}:{port}"
    if stop_after_start:
        server.stop()
        return ViserServeResult(
            manifest_path=result.manifest_path,
            scene_path=result.scene_path,
            screenshot_paths=result.screenshot_paths,
            url=url,
            server=None,
        )
    if block:
        server.sleep_forever()
    return ViserServeResult(
        manifest_path=result.manifest_path,
        scene_path=result.scene_path,
        screenshot_paths=result.screenshot_paths,
        url=url,
        server=server,
    )
