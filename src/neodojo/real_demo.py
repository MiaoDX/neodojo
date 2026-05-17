from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .annotations import write_detected_annotations
from .capture_bundle import write_capture_bundle
from .g1_render import write_g1_render
from .g1_visual import build_g1_visual_track, write_fixture_g1_model_descriptor
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


def write_real_conversion_demo(
    out_dir: Path,
    *,
    source_materialization: Path,
    gvhmr_json: Path,
    g1_track: Path | None = None,
    model_descriptor: Path | None = None,
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
        raise ValueError("real conversion demo rendering requires a G1 model descriptor")

    render = write_g1_render(
        out_dir / "g1-render",
        model_descriptor_path=model_descriptor_path,
        g1_track=g1_track_path,
        allow_fixture_model=True,
    )
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
        g1_render_manifest_path=render.manifest_path,
        recording_path=out_dir / "public-demo" / "neodojo-demo.rrd",
        use_rerun_sdk=use_rerun_sdk,
    )
    public_smoke = smoke_check_public_demo(public.manifest_path)
    viser = write_viser_runtime_contract(
        out_dir / "viser-runtime",
        playback_manifest_path=playback.manifest_path,
        g1_render_manifest_path=render.manifest_path,
    )
    capture = write_capture_bundle(
        out_dir / "capture",
        public_demo=public.manifest_path,
        viser_runtime=viser.manifest_path,
        g1_render=render.manifest_path,
    )

    manifest_path = out_dir / "manifest.json"
    fixture_components = []
    if generated_fixture_model:
        fixture_components.append("g1_model_descriptor")
    if generated_g1_track is not None:
        fixture_components.append("derived_g1_visual_track")
    manifest = {
        "schema": REAL_CONVERSION_DEMO_SCHEMA,
        "status": "generated",
        "fixture_only": bool(fixture_components),
        "fixture_components": fixture_components,
        "real_gvhmr_artifact_imported": True,
        "source_materialization": _relative_path(source_materialization, manifest_path.parent),
        "source_validation": _relative_path(validation.report_path, manifest_path.parent),
        "validated_gvhmr_json": _relative_path(validation.validated_export_path, manifest_path.parent),
        "motion_record": _relative_path(motion.motion_record_manifest_path, manifest_path.parent),
        "smplx_surface": _relative_path(surface.manifest_path, manifest_path.parent),
        "annotations": _relative_path(annotations.manifest_path, manifest_path.parent),
        "g1_track": _relative_path(g1_track_path, manifest_path.parent),
        "g1_track_generated_from_smplx": generated_g1_track is not None,
        "g1_model_descriptor": _relative_path(model_descriptor_path, manifest_path.parent),
        "g1_render": _relative_path(render.manifest_path, manifest_path.parent),
        "teaching_playback": _relative_path(playback.manifest_path, manifest_path.parent),
        "public_demo": _relative_path(public.manifest_path, manifest_path.parent),
        "viser_runtime": _relative_path(viser.manifest_path, manifest_path.parent),
        "capture_bundle": _relative_path(capture.manifest_path, manifest_path.parent),
        "reference_video_sync_available": reference_video is not None,
        "scoring_source": "smplx",
        "g1_scoring_allowed": False,
        "notes": (
            "This command consumes an externally generated GVHMR JSON export. It "
            "does not run GVHMR locally or commit source video, motion outputs, "
            "rendered media, or model assets."
        ),
    }
    _write_json(manifest_path, manifest)
    checked_paths = list(dict.fromkeys([
        validation.report_path,
        motion.motion_record_manifest_path,
        surface.manifest_path,
        annotations.manifest_path,
        g1_track_path,
        render.manifest_path,
        playback.manifest_path,
        public.manifest_path,
        viser.manifest_path,
        capture.manifest_path,
        *public_smoke.checked_paths,
        *capture.checked_paths,
    ]))
    return RealConversionDemoWriteResult(manifest_path=manifest_path, checked_paths=checked_paths)
