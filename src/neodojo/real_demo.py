from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .annotations import write_detected_annotations
from .capture_bundle import write_capture_bundle
from .execution_profiles import G1_ACTUAL_MUJOCO_REPLAY_EVIDENCE_PROFILE, require_satisfied_execution_profile
from .g1_render import DEFAULT_G1_REPLAY_FPS, write_g1_mujoco_render, write_g1_render
from .g1_visual import build_g1_visual_track, resolve_g1_track_manifest, write_fixture_g1_model_descriptor
from .motion_contract import _relative_path, _write_json, validate_output_dir, write_gvhmr_json_motion_contract
from .public_demo import smoke_check_public_demo, write_public_demo
from .real_conversion import SOURCE_MATERIALIZATION_SCHEMA, validate_gvhmr_source
from .smplx_surface import write_smplx_surface_proxy
from .teaching_playback import write_teaching_playback_demo
from .viser_runtime import write_viser_runtime_contract

REAL_CONVERSION_DEMO_SCHEMA = "neodojo.real_conversion_demo.v1"


@dataclass(frozen=True)
class RealConversionDemoWriteResult:
    manifest_path: Path
    checked_paths: list[Path]


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload


def _materialized_reference_video(source_materialization: Path) -> tuple[Path | None, float]:
    materialization = _load_json_object(source_materialization, "source materialization manifest")
    if materialization.get("schema") != SOURCE_MATERIALIZATION_SCHEMA:
        raise ValueError("source materialization manifest has an unsupported schema")

    outputs = materialization.get("outputs")
    if not isinstance(outputs, dict):
        return None, 0.0
    trimmed_video_path = outputs.get("trimmed_video_path")
    if not isinstance(trimmed_video_path, str) or not trimmed_video_path:
        return None, 0.0
    trimmed = Path(trimmed_video_path)
    if not trimmed.exists():
        return None, 0.0

    trim = materialization.get("trim")
    start = 0.0
    if isinstance(trim, dict):
        try:
            start = float(trim.get("start_seconds", 0.0))
        except (TypeError, ValueError):
            start = 0.0
    return trimmed, start


def _model_descriptor_from_track(g1_track: Path) -> Path | None:
    track_manifest_path = resolve_g1_track_manifest(g1_track)
    track = _load_json_object(track_manifest_path, "G1 track manifest")
    reference = track.get("model_descriptor")
    if not isinstance(reference, str) or not reference:
        return None
    return (track_manifest_path.parent / reference).resolve()


def write_real_conversion_demo(
    out_dir: Path,
    *,
    source_materialization: Path,
    gvhmr_json: Path,
    g1_track: Path | None = None,
    model_descriptor: Path | None = None,
    g1_render: Path | None = None,
    render_mujoco: bool = False,
    g1_replay_fps: float | None = DEFAULT_G1_REPLAY_FPS,
    g1_execution_profile: str = "auto",
    use_rerun_sdk: bool = False,
) -> RealConversionDemoWriteResult:
    validate_output_dir(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    validation = validate_gvhmr_source(
        out_dir / "real-conversion-validation",
        source_materialization=source_materialization,
        gvhmr_json=gvhmr_json,
    )
    if validation.status != "validated" or validation.validated_export_path is None:
        raise ValueError(
            "GVHMR source validation did not pass; inspect "
            f"{validation.report_path} before importing the real artifact"
        )
    materialization_payload = _load_json_object(source_materialization, "source materialization manifest")
    validated_export_payload = _load_json_object(validation.validated_export_path, "validated GVHMR export")
    source_materialization_fixture_only = bool(materialization_payload.get("fixture_only"))
    gvhmr_export_fixture_only = bool(validated_export_payload.get("fixture_only"))
    real_gvhmr_artifact_imported = not source_materialization_fixture_only and not gvhmr_export_fixture_only

    motion = write_gvhmr_json_motion_contract(
        out_dir / "motion-contract",
        validation.validated_export_path,
    )
    surface = write_smplx_surface_proxy(out_dir / "smplx-surface", motion.out_dir)
    annotations = write_detected_annotations(out_dir / "annotations", motion.out_dir)

    generated_g1_track = None
    generated_fixture_model = False
    model_descriptor_path = model_descriptor
    if g1_track is None:
        if model_descriptor_path is None:
            model = write_fixture_g1_model_descriptor(out_dir / "g1-visual")
            model_descriptor_path = model.descriptor_path
            generated_fixture_model = True
        generated_g1_track = build_g1_visual_track(
            motion.out_dir,
            out_dir / "g1-visual",
            model_descriptor_path=model_descriptor_path,
        )
        g1_track_path = generated_g1_track.track_manifest_path
    else:
        g1_track_path = g1_track
        if model_descriptor_path is None:
            model_descriptor_path = _model_descriptor_from_track(g1_track_path)

    if model_descriptor_path is None and g1_render is None:
        raise ValueError("real conversion demo rendering requires a G1 model descriptor")

    if g1_render is not None:
        render_manifest_path = g1_render
        render_checked_paths = [g1_render]
    elif render_mujoco:
        if model_descriptor_path is None:
            raise ValueError("MuJoCo G1 replay rendering requires a G1 model descriptor")
        render = write_g1_mujoco_render(
            out_dir / "g1-mujoco-render",
            model_descriptor_path=model_descriptor_path,
            g1_track=g1_track_path,
            replay_fps=g1_replay_fps,
            execution_profile=g1_execution_profile,
        )
        render_manifest_path = render.manifest_path
        render_checked_paths = [render.manifest_path, *render.frame_paths.values()]
    else:
        if model_descriptor_path is None:
            raise ValueError("G1 schematic rendering requires a G1 model descriptor")
        render = write_g1_render(
            out_dir / "g1-render",
            model_descriptor_path=model_descriptor_path,
            g1_track=g1_track_path,
            allow_fixture_model=True,
            execution_profile=g1_execution_profile,
        )
        render_manifest_path = render.manifest_path
        render_checked_paths = [render.manifest_path, *render.frame_paths.values()]

    render_manifest_payload = _load_json_object(render_manifest_path, "G1 render manifest")
    if g1_execution_profile != "auto":
        profile = render_manifest_payload.get("execution_profile")
        if not isinstance(profile, dict):
            raise ValueError("G1 render manifest is missing execution_profile")
        if profile.get("profile") != g1_execution_profile:
            raise ValueError(
                "G1 render manifest execution_profile does not match requested "
                f"profile {g1_execution_profile}"
            )
        require_satisfied_execution_profile(profile, label="G1 render manifest")
    reference_video, reference_trim_start = _materialized_reference_video(source_materialization)
    playback = write_teaching_playback_demo(
        out_dir / "teaching-demo",
        motion.out_dir,
        g1_track_path,
        annotations_path=annotations.manifest_path,
        smplx_surface=surface.manifest_path,
        reference_video=reference_video,
        reference_trim_start_seconds=reference_trim_start,
    )
    public = write_public_demo(
        playback_manifest_path=playback.manifest_path,
        g1_render_manifest_path=render_manifest_path,
        recording_path=out_dir / "public-demo" / "neodojo-demo.rrd",
        use_rerun_sdk=use_rerun_sdk,
    )
    public_manifest_payload = _load_json_object(public.manifest_path, "public-demo manifest")
    public_smoke = smoke_check_public_demo(public.manifest_path)
    viser = write_viser_runtime_contract(
        out_dir / "viser-runtime",
        playback_manifest_path=playback.manifest_path,
        g1_render_manifest_path=render_manifest_path,
    )
    capture = write_capture_bundle(
        out_dir / "capture",
        public_demo=public.manifest_path,
        viser_runtime=viser.manifest_path,
        g1_render=render_manifest_path,
    )

    manifest_path = out_dir / "manifest.json"
    fixture_components = []
    if generated_fixture_model:
        fixture_components.append("g1_model_descriptor")
    if generated_g1_track is not None:
        fixture_components.append("derived_g1_visual_track")
    actual_g1_model_replay = bool(render_manifest_payload.get("actual_g1_model_replay"))
    notes = (
        "This command consumes a returned GVHMR JSON export. It does not run "
        "GVHMR inside the import step or commit source video, motion outputs, "
        "rendered media, or model assets."
        if real_gvhmr_artifact_imported
        else (
            "This command consumed a fixture-only GVHMR-shaped JSON export for "
            "local contract smoke testing. It does not prove a real GVHMR run, "
            "and it does not commit source video, motion outputs, rendered media, "
            "or model assets."
        )
    )
    manifest = {
        "schema": REAL_CONVERSION_DEMO_SCHEMA,
        "status": "generated",
        "fixture_only": bool(
            fixture_components
            or source_materialization_fixture_only
            or gvhmr_export_fixture_only
        ),
        "fixture_components": fixture_components,
        "gvhmr_artifact_imported": True,
        "real_gvhmr_artifact_imported": real_gvhmr_artifact_imported,
        "source_materialization_fixture_only": source_materialization_fixture_only,
        "gvhmr_export_fixture_only": gvhmr_export_fixture_only,
        "source_materialization": _relative_path(source_materialization, manifest_path.parent),
        "source_validation": _relative_path(validation.report_path, manifest_path.parent),
        "validated_gvhmr_json": _relative_path(validation.validated_export_path, manifest_path.parent),
        "motion_record": _relative_path(motion.motion_record_manifest_path, manifest_path.parent),
        "smplx_surface": _relative_path(surface.manifest_path, manifest_path.parent),
        "annotations": _relative_path(annotations.manifest_path, manifest_path.parent),
        "g1_track": _relative_path(g1_track_path, manifest_path.parent),
        "g1_track_generated_from_smplx": generated_g1_track is not None,
        "g1_model_descriptor": _relative_path(model_descriptor_path, manifest_path.parent)
        if model_descriptor_path is not None
        else None,
        "g1_render": _relative_path(render_manifest_path, manifest_path.parent),
        "g1_render_supplied": g1_render is not None,
        "g1_render_mujoco_requested": render_mujoco,
        "actual_g1_model_replay": actual_g1_model_replay,
        "g1_replay_claim": "actual_mujoco_frame_sequence" if actual_g1_model_replay else "schematic_or_incomplete_evidence",
        "g1_execution_profile": render_manifest_payload.get("execution_profile"),
        "g1_actual_replay_profile_required": g1_execution_profile == G1_ACTUAL_MUJOCO_REPLAY_EVIDENCE_PROFILE,
        "teaching_playback": _relative_path(playback.manifest_path, manifest_path.parent),
        "public_demo": _relative_path(public.manifest_path, manifest_path.parent),
        "teaching_html": public_manifest_payload.get("teaching_html"),
        "viser_runtime": _relative_path(viser.manifest_path, manifest_path.parent),
        "capture_bundle": _relative_path(capture.manifest_path, manifest_path.parent),
        "reference_video_sync_available": reference_video is not None,
        "scoring_source": "smplx",
        "g1_scoring_allowed": False,
        "notes": notes,
    }
    _write_json(manifest_path, manifest)
    checked_paths = list(dict.fromkeys([
        validation.report_path,
        motion.motion_record_manifest_path,
        surface.manifest_path,
        annotations.manifest_path,
        g1_track_path,
        *render_checked_paths,
        playback.manifest_path,
        public.manifest_path,
        viser.manifest_path,
        capture.manifest_path,
        *public_smoke.checked_paths,
        *capture.checked_paths,
    ]))
    return RealConversionDemoWriteResult(manifest_path=manifest_path, checked_paths=checked_paths)
