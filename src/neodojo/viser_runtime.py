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


@dataclass(frozen=True)
class ViserServeResult:
    manifest_path: Path
    scene_path: Path
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


def build_viser_runtime_manifest(scene: dict[str, Any], *, scene_path: Path, manifest_path: Path) -> dict[str, Any]:
    timing = scene.get("timing") or {}
    frame_count = int(timing.get("frame_count") or len(scene["tracks"]["smplx"]["frames"]))
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
    _write_json(scene_path, scene)
    _write_json(manifest_path, build_viser_runtime_manifest(scene, scene_path=scene_path, manifest_path=manifest_path))
    return ViserRuntimeWriteResult(manifest_path=manifest_path, scene_path=scene_path)


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


def _render_viser_frame(server: Any, np: Any, scene: dict[str, Any], frame_index: int, handles: dict[str, Any]) -> None:
    _clear_handles(handles)
    for track_id, x_offset, color, label in [
        ("smplx", -0.55, (20, 124, 114), "SMPL-X teacher"),
        ("g1", 0.55, (184, 78, 50), "Unitree G1 visual"),
    ]:
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
    _render_viser_frame(server, np, scene, initial_frame, handles)

    server.gui.add_markdown(
        "**neodojo fixture runtime**\n\nSMPL-X is the scoring source. Unitree G1 is visual-only."
    )
    frame_slider = server.gui.add_slider(
        "Frame",
        min=0,
        max=max(0, frame_count - 1),
        step=1,
        initial_value=initial_frame,
    )
    reset_button = server.gui.add_button("Reset to key frame")

    @frame_slider.on_update
    def _(_: Any) -> None:
        _render_viser_frame(server, np, scene, int(frame_slider.value), handles)

    @reset_button.on_click
    def _(_: Any) -> None:
        frame_slider.value = initial_frame
        _render_viser_frame(server, np, scene, initial_frame, handles)

    url = f"http://{host}:{port}"
    if stop_after_start:
        server.stop()
        return ViserServeResult(
            manifest_path=result.manifest_path,
            scene_path=result.scene_path,
            url=url,
            server=None,
        )
    if block:
        server.sleep_forever()
    return ViserServeResult(
        manifest_path=result.manifest_path,
        scene_path=result.scene_path,
        url=url,
        server=server,
    )
