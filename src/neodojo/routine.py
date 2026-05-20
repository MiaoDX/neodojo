from __future__ import annotations

import html
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import local_file_metadata, require_schema
from .g1_visual import import_gmr_json_track, write_fixture_g1_model_descriptor
from .motion_contract import (
    _relative_path,
    _write_json,
    validate_output_dir,
    write_gvhmr_json_motion_contract,
)
from .real_conversion import (
    REAL_CONVERSION_PREP_SCHEMA,
    SOURCE_MATERIALIZATION_SCHEMA,
    materialize_real_conversion_source,
    package_gvhmr_gpu_handoff,
    write_real_conversion_prep,
)
from .real_demo import write_real_conversion_demo

ROUTINE_MANIFEST_SCHEMA = "neodojo.bilibili_routines.v1"
ROUTINE_SPLIT_SCHEMA = "neodojo.routine_split.v1"
ROUTINE_GPU_HANDOFF_SCHEMA = "neodojo.routine_gpu_handoffs.v1"
ROUTINE_HTML_SCHEMA = "neodojo.routine_html.v1"
ROUTINE_SMOKE_SCHEMA = "neodojo.routine_smoke.v1"
DEFAULT_ROUTINE_MANIFEST = Path("video/bilibili/routines.json")
DEFAULT_BILIBILI_MANIFEST = Path("video/bilibili/manifest.json")


@dataclass(frozen=True)
class RoutineSplitWriteResult:
    manifest_path: Path
    phase_count: int


@dataclass(frozen=True)
class RoutineGpuHandoffWriteResult:
    manifest_path: Path
    phase_count: int


@dataclass(frozen=True)
class RoutineHtmlWriteResult:
    html_path: Path
    manifest_path: Path
    checked_paths: list[Path]


@dataclass(frozen=True)
class RoutineSmokeResult:
    manifest_path: Path
    checked_paths: list[Path]


def _as_posix(path: Path) -> str:
    return str(path).replace("\\", "/")


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"{label} does not exist: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"failed to parse {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload


def _load_bilibili_entries(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    payload = _load_json_object(path, "Bilibili manifest")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        return {}
    by_bvid = {}
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("bvid"), str):
            by_bvid[entry["bvid"]] = entry
    return by_bvid


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _require_seconds(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric seconds")
    return round(float(value), 3)


def _normalize_phase(phase: dict[str, Any], index: int) -> dict[str, Any]:
    phase_id = _require_text(phase.get("phase_id"), f"phase {index} phase_id")
    name_zh = _require_text(phase.get("name_zh"), f"phase {index} name_zh")
    name_en = _require_text(phase.get("name_en"), f"phase {index} name_en")
    selection_rule = _require_text(phase.get("selection_rule"), f"phase {index} selection_rule")
    if selection_rule != "first_demo_only":
        raise ValueError("routine phases must use selection_rule first_demo_only")
    start = _require_seconds(phase.get("start_seconds"), f"phase {phase_id} start_seconds")
    end = _require_seconds(phase.get("end_seconds"), f"phase {phase_id} end_seconds")
    if start < 0:
        raise ValueError(f"phase {phase_id} start_seconds must be non-negative")
    if end <= start:
        raise ValueError(f"phase {phase_id} end_seconds must be greater than start_seconds")
    return {
        "phase_id": phase_id,
        "name_zh": name_zh,
        "name_en": name_en,
        "start_seconds": start,
        "end_seconds": end,
        "duration_seconds": round(end - start, 3),
        "selection_rule": selection_rule,
    }


def validate_routine_manifest(
    manifest_path: Path = DEFAULT_ROUTINE_MANIFEST,
    *,
    bilibili_manifest: Path = DEFAULT_BILIBILI_MANIFEST,
) -> dict[str, Any]:
    payload = _load_json_object(manifest_path, "routine manifest")
    require_schema(payload, ROUTINE_MANIFEST_SCHEMA, "routine manifest")
    routines = payload.get("routines")
    if not isinstance(routines, dict) or not routines:
        raise ValueError("routine manifest must contain non-empty routines")

    bilibili_entries = _load_bilibili_entries(bilibili_manifest)
    normalized: dict[str, Any] = {
        "schema": ROUTINE_MANIFEST_SCHEMA,
        "selection_rule": payload.get("selection_rule"),
        "routines": {},
    }
    for routine_key, raw_routine in sorted(routines.items()):
        if not isinstance(raw_routine, dict):
            raise ValueError(f"routine {routine_key} must be an object")
        routine = _require_text(raw_routine.get("routine"), f"routine {routine_key} routine")
        if routine != routine_key:
            raise ValueError(f"routine key {routine_key} does not match routine field {routine}")
        bvid = _require_text(raw_routine.get("bilibili_bvid"), f"routine {routine_key} bilibili_bvid")
        phases_raw = raw_routine.get("phases")
        if not isinstance(phases_raw, list) or not phases_raw:
            raise ValueError(f"routine {routine_key} must contain non-empty phases")
        phases = [_normalize_phase(phase, index) for index, phase in enumerate(phases_raw)]
        seen_phase_ids: set[str] = set()
        previous_end: float | None = None
        for phase in phases:
            if phase["phase_id"] in seen_phase_ids:
                raise ValueError(f"routine {routine_key} has duplicate phase_id {phase['phase_id']}")
            seen_phase_ids.add(phase["phase_id"])
            if previous_end is not None and phase["start_seconds"] < previous_end:
                raise ValueError(f"routine {routine_key} has overlapping phase timestamps")
            previous_end = phase["end_seconds"]
        source_entry = bilibili_entries.get(bvid, {})
        duration = source_entry.get("duration_seconds")
        if isinstance(duration, (int, float)):
            too_late = [phase["phase_id"] for phase in phases if phase["end_seconds"] > float(duration) + 0.5]
            if too_late:
                raise ValueError(f"routine {routine_key} phase exceeds source duration: {', '.join(too_late)}")
        normalized["routines"][routine_key] = {
            "routine": routine_key,
            "name_zh": _require_text(raw_routine.get("name_zh"), f"routine {routine_key} name_zh"),
            "name_en": _require_text(raw_routine.get("name_en"), f"routine {routine_key} name_en"),
            "bilibili_bvid": bvid,
            "source_video": _require_text(raw_routine.get("source_video"), f"routine {routine_key} source_video"),
            "source_entry": source_entry or None,
            "phases": phases,
        }
    return normalized


def get_routine_definition(
    routine: str,
    *,
    manifest_path: Path = DEFAULT_ROUTINE_MANIFEST,
    bilibili_manifest: Path = DEFAULT_BILIBILI_MANIFEST,
) -> dict[str, Any]:
    manifest = validate_routine_manifest(manifest_path, bilibili_manifest=bilibili_manifest)
    routines = manifest["routines"]
    if routine not in routines:
        raise ValueError(f"unknown routine: {routine}")
    return routines[routine]


def _phase_source_id(routine: str, phase_id: str) -> str:
    return f"bilibili-{routine}-{phase_id}"


def _phase_title(routine_def: dict[str, Any], phase: dict[str, Any]) -> str:
    return f"{routine_def['name_en']} - {phase['name_en']}"


def _phase_title_zh(routine_def: dict[str, Any], phase: dict[str, Any]) -> str:
    return f"{routine_def['name_zh']} - {phase['name_zh']}"


def _ffmpeg_commands(source_video: Path, trimmed_video_path: Path, frames_dir: Path, phase: dict[str, Any], frame_rate: float) -> list[dict[str, Any]]:
    start = f"{phase['start_seconds']:.3f}".rstrip("0").rstrip(".")
    end = f"{phase['end_seconds']:.3f}".rstrip("0").rstrip(".")
    return [
        {
            "kind": "trim_clip",
            "argv": [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                start,
                "-to",
                end,
                "-i",
                str(source_video),
                "-map",
                "0:v:0",
                "-an",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(trimmed_video_path),
            ],
        },
        {
            "kind": "extract_reference_frames",
            "argv": [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(trimmed_video_path),
                "-vf",
                f"fps={frame_rate:g}",
                str(frames_dir / "frame-%06d.jpg"),
            ],
        },
    ]


def _write_dry_phase_materialization(
    phase_dir: Path,
    *,
    routine_def: dict[str, Any],
    phase: dict[str, Any],
    source_video: Path,
    frame_rate: float,
) -> Path:
    prep_path = phase_dir / "prep" / "real-conversion-prep.json"
    materialization_path = phase_dir / "source-materialization.json"
    trimmed_video_path = phase_dir / "source" / "trimmed-clip.mp4"
    frames_dir = phase_dir / "source" / "frames"
    source_file = local_file_metadata(
        source_video,
        label="routine source video",
        allowed_suffixes={".mp4", ".mov", ".m4v", ".webm"},
    )
    trim = {
        "start_seconds": phase["start_seconds"],
        "end_seconds": phase["end_seconds"],
        "duration_seconds": phase["duration_seconds"],
    }
    source_id = _phase_source_id(routine_def["routine"], phase["phase_id"])
    source_entry = routine_def.get("source_entry") if isinstance(routine_def.get("source_entry"), dict) else {}
    prep = {
        "schema": REAL_CONVERSION_PREP_SCHEMA,
        "status": "gpu_gate_pending",
        "source": {
            "id": source_id,
            "source_kind": "bilibili_local_user_supplied",
            "routine": routine_def["routine"],
            "phase_id": phase["phase_id"],
            "category": routine_def["routine"],
            "category_chinese": routine_def["name_zh"],
            "article_title_chinese": source_entry.get("title") or routine_def["name_zh"],
            "title_english": _phase_title(routine_def, phase),
            "article_url": source_entry.get("page_url"),
            "source_mp4_url": source_entry.get("page_url"),
            "selected_quality": source_entry.get("selected_resolution"),
            "resolution": source_entry.get("selected_resolution"),
            "duration_seconds": source_entry.get("duration_seconds"),
            "recommended_output_path": _as_posix(source_video),
            "local_video_path": _as_posix(source_video),
            "rights_notes": "licensing unconfirmed; keep Bilibili media local unless rights are confirmed",
        },
        "source_media": {
            "schema": "neodojo.source_media.v1",
            "local_file": source_file,
            "probe": None,
        },
        "trim": trim,
        "gpu_run": {
            "required": True,
            "blocked_locally": True,
            "expected_output_dir": _as_posix(phase_dir / "prep" / "gvhmr-output"),
            "expected_export_json": _as_posix(phase_dir / "prep" / "gvhmr-smplx-joints.json"),
            "gvhmr_command_template": "python tools/demo/demo.py --video <trimmed-video> --output_root <gvhmr-output-dir>",
        },
    }
    materialization = {
        "schema": SOURCE_MATERIALIZATION_SCHEMA,
        "status": "dry_run",
        "fixture_only": False,
        "media_committed_to_repo": False,
        "routine": routine_def["routine"],
        "phase_id": phase["phase_id"],
        "source_prep": {
            "manifest": _as_posix(prep_path),
            "source_id": source_id,
            "source_kind": "bilibili_local_user_supplied",
            "title_english": _phase_title(routine_def, phase),
            "title_chinese": _phase_title_zh(routine_def, phase),
            "source_schema": REAL_CONVERSION_PREP_SCHEMA,
        },
        "source_media": {
            "schema": "neodojo.source_media_materialized.v1",
            "local_file": source_file,
            "prep_probe": None,
            "rights_notes": "licensing unconfirmed; keep Bilibili media local unless rights are confirmed",
        },
        "trim": trim,
        "ffmpeg": {
            "available": shutil.which("ffmpeg") is not None,
            "executable": shutil.which("ffmpeg"),
            "dry_run": True,
            "commands": _ffmpeg_commands(source_video, trimmed_video_path, frames_dir, phase, frame_rate),
        },
        "outputs": {
            "trimmed_video_path": _as_posix(trimmed_video_path),
            "trimmed_video": None,
            "frames_dir": _as_posix(frames_dir),
            "frame_pattern": _as_posix(frames_dir / "frame-%06d.jpg"),
            "extracted_frame_count": 0,
            "first_frame": None,
            "last_frame": None,
        },
        "validation": {
            "schema": "neodojo.source_materialization_validation.v1",
            "source_file_validated": True,
            "trimmed_video_written": False,
            "frames_extracted": False,
            "duration": {
                "checked": False,
                "succeeded": False,
                "expected_duration_seconds": phase["duration_seconds"],
                "actual_duration_seconds": None,
                "delta_seconds": None,
                "tolerance_seconds": None,
                "error": "routine split dry-run did not process media",
            },
            "gvhmr_input_ready": False,
        },
        "gpu_handoff": {
            "schema": "neodojo.gvhmr_input_handoff.v1",
            "blocked_locally": True,
            "trimmed_video_argument": _as_posix(trimmed_video_path),
            "expected_export_json": _as_posix(phase_dir / "gvhmr-smplx-joints.json"),
            "command_template": (
                "python tools/demo/demo.py "
                f"--video {_as_posix(trimmed_video_path)} --output_root <gvhmr-output-dir>"
            ),
            "notes": "Dry-run manifest only. Re-run routine split without --dry-run before a GVHMR run.",
        },
    }
    _write_json(prep_path, prep)
    _write_json(materialization_path, materialization)
    return materialization_path


def _phase_manifest_entry(
    phase: dict[str, Any],
    *,
    manifest_path: Path,
    materialization_path: Path,
    split_root: Path,
) -> dict[str, Any]:
    materialization = _load_json_object(materialization_path, "phase source materialization")
    outputs = materialization.get("outputs") if isinstance(materialization.get("outputs"), dict) else {}
    trimmed_path = outputs.get("trimmed_video_path") if isinstance(outputs.get("trimmed_video_path"), str) else None
    return {
        **phase,
        "source_materialization": _relative_path(materialization_path, manifest_path.parent),
        "source_materialization_status": materialization.get("status"),
        "clip_path": trimmed_path,
        "clip_available": bool(trimmed_path and Path(trimmed_path).exists()),
        "phase_dir": _relative_path(split_root / phase["phase_id"], manifest_path.parent),
    }


def write_routine_split(
    out_dir: Path,
    *,
    routine: str,
    source_video: Path | None = None,
    manifest_path: Path = DEFAULT_ROUTINE_MANIFEST,
    bilibili_manifest: Path = DEFAULT_BILIBILI_MANIFEST,
    frame_rate: float = 1.0,
    dry_run: bool = False,
) -> RoutineSplitWriteResult:
    validate_output_dir(out_dir)
    if frame_rate <= 0:
        raise ValueError("frame rate must be positive")
    routine_def = get_routine_definition(
        routine,
        manifest_path=manifest_path,
        bilibili_manifest=bilibili_manifest,
    )
    source = source_video or Path(routine_def["source_video"])
    if not source.exists():
        raise ValueError(f"routine source video does not exist: {source}")
    local_file_metadata(source, label="routine source video", allowed_suffixes={".mp4", ".mov", ".m4v", ".webm"})

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_out = out_dir / "manifest.json"
    phase_entries = []
    for phase in routine_def["phases"]:
        phase_dir = out_dir / phase["phase_id"]
        if dry_run:
            materialization_path = _write_dry_phase_materialization(
                phase_dir,
                routine_def=routine_def,
                phase=phase,
                source_video=source,
                frame_rate=frame_rate,
            )
        else:
            prep = write_real_conversion_prep(
                phase_dir / "prep",
                local_video=source,
                local_source_id=_phase_source_id(routine, phase["phase_id"]),
                local_title_english=_phase_title(routine_def, phase),
                local_title_chinese=_phase_title_zh(routine_def, phase),
                local_category=routine,
                local_category_chinese=routine_def["name_zh"],
                local_origin_url=(routine_def.get("source_entry") or {}).get("page_url")
                if isinstance(routine_def.get("source_entry"), dict)
                else None,
                start_seconds=phase["start_seconds"],
                end_seconds=phase["end_seconds"],
                rights_notes="licensing unconfirmed; keep Bilibili media local unless rights are confirmed",
            )
            materialized = materialize_real_conversion_source(
                phase_dir,
                prep_manifest=prep.manifest_path,
                local_video=source,
                frame_rate=frame_rate,
                dry_run=False,
            )
            materialization_path = materialized.manifest_path
        phase_entries.append(
            _phase_manifest_entry(
                phase,
                manifest_path=manifest_out,
                materialization_path=materialization_path,
                split_root=out_dir,
            )
        )

    manifest = {
        "schema": ROUTINE_SPLIT_SCHEMA,
        "routine": routine,
        "routine_name_zh": routine_def["name_zh"],
        "routine_name_en": routine_def["name_en"],
        "bilibili_bvid": routine_def["bilibili_bvid"],
        "source_video": _as_posix(source),
        "source_video_metadata": local_file_metadata(
            source,
            label="routine source video",
            allowed_suffixes={".mp4", ".mov", ".m4v", ".webm"},
        ),
        "dry_run": dry_run,
        "frame_rate": frame_rate,
        "phase_count": len(phase_entries),
        "phases": phase_entries,
        "source_materializations": [entry["source_materialization"] for entry in phase_entries],
        "selection_rule": "first_demo_only",
        "scoring_source": "smplx",
        "g1_scoring_allowed": False,
        "notes": (
            "Routine split writes local-only source materialization manifests and optional clips. "
            "It does not run GVHMR, GMR, MuJoCo, or Genesis."
        ),
    }
    _write_json(manifest_out, manifest)
    return RoutineSplitWriteResult(manifest_path=manifest_out, phase_count=len(phase_entries))


def _resolve_manifest_path(path: Path, default_name: str = "manifest.json") -> Path:
    return path if path.is_file() else path / default_name


def _resolve_relative(base: Path, reference: str) -> Path:
    path = Path(reference)
    if path.is_absolute():
        return path
    candidate = base.parent / path
    if candidate.exists():
        return candidate
    return path


def _load_split_manifest(clips: Path) -> tuple[Path, dict[str, Any]]:
    manifest_path = _resolve_manifest_path(clips)
    manifest = _load_json_object(manifest_path, "routine split manifest")
    require_schema(manifest, ROUTINE_SPLIT_SCHEMA, "routine split manifest")
    return manifest_path, manifest


def write_routine_gpu_handoffs(
    out_dir: Path,
    *,
    routine: str,
    clips: Path,
) -> RoutineGpuHandoffWriteResult:
    validate_output_dir(out_dir)
    split_manifest_path, split_manifest = _load_split_manifest(clips)
    if split_manifest.get("routine") != routine:
        raise ValueError("routine split manifest routine does not match --routine")

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    phase_entries = []
    for phase in split_manifest["phases"]:
        if not isinstance(phase, dict):
            raise ValueError("routine split phases must be objects")
        phase_id = _require_text(phase.get("phase_id"), "phase_id")
        source_reference = _require_text(phase.get("source_materialization"), f"{phase_id} source_materialization")
        source_materialization = _resolve_relative(split_manifest_path, source_reference)
        handoff = package_gvhmr_gpu_handoff(
            out_dir / phase_id,
            source_materialization=source_materialization,
            expected_export_json=out_dir / phase_id / "gvhmr-smplx-joints.json",
        )
        phase_entries.append(
            {
                "phase_id": phase_id,
                "name_zh": phase.get("name_zh"),
                "name_en": phase.get("name_en"),
                "source_materialization": _relative_path(source_materialization, manifest_path.parent),
                "handoff": _relative_path(handoff.manifest_path, manifest_path.parent),
                "readme": _relative_path(handoff.readme_path, manifest_path.parent),
                "expected_gvhmr_json": _relative_path(out_dir / phase_id / "gvhmr-smplx-joints.json", manifest_path.parent),
                "status": handoff.status,
            }
        )

    manifest = {
        "schema": ROUTINE_GPU_HANDOFF_SCHEMA,
        "routine": routine,
        "phase_count": len(phase_entries),
        "source_split": _relative_path(split_manifest_path, manifest_path.parent),
        "phases": phase_entries,
        "scoring_source": "smplx",
        "g1_scoring_allowed": False,
        "notes": "GPU handoffs prepare per-phase GVHMR workspaces only; no GVHMR or GMR runtime is bundled.",
    }
    _write_json(manifest_path, manifest)
    return RoutineGpuHandoffWriteResult(manifest_path=manifest_path, phase_count=len(phase_entries))


def _load_source_materializations(source_materializations: Path, routine: str) -> tuple[Path, dict[str, Any], list[dict[str, Any]]]:
    split_manifest_path, split_manifest = _load_split_manifest(source_materializations)
    if split_manifest.get("routine") != routine:
        raise ValueError("source materialization routine does not match --routine")
    phases = split_manifest.get("phases")
    if not isinstance(phases, list) or not phases:
        raise ValueError("routine split manifest has no phases")
    return split_manifest_path, split_manifest, phases


def _artifact_candidates(root: Path | None, phase_id: str, filenames: tuple[str, ...]) -> list[Path]:
    if root is None:
        return []
    candidates: list[Path] = []
    for filename in filenames:
        candidates.append(root / phase_id / filename)
        candidates.append(root / phase_id / "normalized" / filename)
    candidates.append(root / f"{phase_id}.json")
    return candidates


def _first_existing(candidates: list[Path]) -> Path | None:
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _resolve_trimmed_clip(source_materialization: Path) -> Path | None:
    materialization = _load_json_object(source_materialization, "source materialization")
    outputs = materialization.get("outputs") if isinstance(materialization.get("outputs"), dict) else {}
    reference = outputs.get("trimmed_video_path")
    if not isinstance(reference, str) or not reference:
        return None
    path = Path(reference)
    if path.is_absolute() and path.exists():
        return path
    candidates = [path, source_materialization.parent / path]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file() and candidate.stat().st_size > 0:
            return candidate
    return None


def _copy_reference_clip(source_materialization: Path, out_dir: Path, phase_id: str) -> str | None:
    clip = _resolve_trimmed_clip(source_materialization)
    if clip is None:
        return None
    clip_dir = out_dir / "clips"
    clip_dir.mkdir(parents=True, exist_ok=True)
    destination = clip_dir / f"{phase_id}{clip.suffix.lower()}"
    shutil.copyfile(clip, destination)
    return _relative_path(destination, out_dir)


def _phase_status_label(status: str) -> str:
    return status.replace("_", " ")


def _render_routine_html(payload: dict[str, Any]) -> str:
    routine_name = html.escape(payload["routine_name_en"])
    routine_name_zh = html.escape(payload["routine_name_zh"])
    nav = "\n".join(
        f'<a href="#phase-{html.escape(phase["phase_id"])}">{index + 1}. '
        f'{html.escape(phase["name_zh"])} · {html.escape(phase["name_en"])}</a>'
        for index, phase in enumerate(payload["phases"])
    )
    sections = []
    for index, phase in enumerate(payload["phases"]):
        phase_id = html.escape(phase["phase_id"])
        clip_html = (
            f'<video src="{html.escape(phase["reference_clip"])}" controls playsinline preload="metadata"></video>'
            if phase.get("reference_clip")
            else '<div class="missing">Original clip is not materialized in this output.</div>'
        )
        phase_demo = phase.get("phase_public_demo")
        smplx_panel = (
            f'<a class="open-demo" href="{html.escape(phase_demo)}">Open synchronized SMPL-X/G1 phase replay</a>'
            if phase_demo
            else f'<div class="missing">{html.escape(phase["gvhmr_status_label"])}</div>'
        )
        g1_detail = html.escape(phase["g1_status_label"])
        provenance_items = "\n".join(
            f"<li><span>{html.escape(label)}</span><code>{html.escape(str(value))}</code></li>"
            for label, value in [
                ("source materialization", phase.get("source_materialization")),
                ("GVHMR JSON", phase.get("gvhmr_json") or "missing"),
                ("GMR JSON", phase.get("gmr_json") or "missing"),
                ("phase demo", phase.get("phase_demo") or "not generated"),
            ]
        )
        sections.append(
            f"""
    <section id="phase-{phase_id}" class="phase">
      <div class="phase-head">
        <h2>{index + 1}. {html.escape(phase["name_zh"])} <span>{html.escape(phase["name_en"])}</span></h2>
        <div class="badges">
          <span>{html.escape(phase["source_status_label"])}</span>
          <span>{html.escape(phase["gvhmr_status_label"])}</span>
          <span>{g1_detail}</span>
        </div>
      </div>
      <div class="panels">
        <article>
          <h3>Original clip</h3>
          {clip_html}
        </article>
        <article>
          <h3>SMPL-X skeleton teaching track</h3>
          <p>Teaching feedback and scoring source: <strong>SMPL-X</strong>.</p>
          {smplx_panel}
        </article>
        <article>
          <h3>Unitree G1 visual replay</h3>
          <p>G1 is a visual companion only. G1 non-scoring: <strong>true</strong>.</p>
          <div class="missing">{g1_detail}</div>
        </article>
      </div>
      <details>
        <summary>Provenance</summary>
        <ul>{provenance_items}</ul>
      </details>
    </section>"""
        )
    section_html = "\n".join(sections)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>neodojo routine replay - {routine_name}</title>
  <style>
    :root {{ --bg:#eef2f6; --panel:#fff; --ink:#17212b; --muted:#5d6875; --line:#d8e0e8; --smplx:#147c72; --g1:#b84e32; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    header {{ padding:18px 22px; background:var(--panel); border-bottom:1px solid var(--line); display:flex; justify-content:space-between; gap:16px; align-items:flex-start; }}
    h1,h2,h3,p {{ margin:0; }}
    h1 {{ font-size:24px; }}
    .subtitle {{ margin-top:4px; color:var(--muted); font-size:14px; }}
    .top-badges,.badges {{ display:flex; flex-wrap:wrap; gap:8px; }}
    .top-badges span,.badges span {{ border:1px solid var(--line); background:#f9fbfd; border-radius:999px; padding:7px 10px; font-size:12px; font-weight:800; color:#334155; }}
    nav {{ position:sticky; top:0; z-index:2; display:flex; overflow-x:auto; gap:8px; padding:10px 16px; background:rgba(255,255,255,.94); border-bottom:1px solid var(--line); }}
    nav a {{ flex:0 0 auto; color:var(--ink); text-decoration:none; border:1px solid var(--line); border-radius:8px; padding:8px 10px; font-size:13px; font-weight:750; background:#fff; }}
    main {{ padding:16px; display:grid; gap:16px; }}
    .phase {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; display:grid; gap:12px; }}
    .phase-head {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }}
    h2 {{ font-size:20px; }}
    h2 span {{ display:block; margin-top:3px; color:var(--muted); font-size:14px; font-weight:650; }}
    .panels {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }}
    article {{ border:1px solid var(--line); border-radius:8px; padding:12px; min-width:0; display:grid; gap:10px; align-content:start; background:#fbfcfe; }}
    h3 {{ font-size:16px; }}
    video {{ width:100%; aspect-ratio:16/9; background:#101820; border-radius:8px; }}
    .missing,.open-demo {{ min-height:88px; display:grid; place-items:center; text-align:center; border:1px dashed #b9c5d0; border-radius:8px; padding:12px; color:var(--muted); background:#fff; }}
    .open-demo {{ color:var(--smplx); font-weight:800; text-decoration:none; }}
    details {{ border-top:1px solid var(--line); padding-top:10px; }}
    summary {{ cursor:pointer; font-weight:800; }}
    ul {{ display:grid; gap:7px; padding-left:0; list-style:none; }}
    li {{ display:flex; justify-content:space-between; gap:12px; color:var(--muted); }}
    code {{ color:var(--ink); word-break:break-all; text-align:right; }}
    @media (max-width: 980px) {{ header,.phase-head {{ display:grid; }} .panels {{ grid-template-columns:1fr; }} li {{ display:grid; }} code {{ text-align:left; }} }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>{routine_name_zh} · {routine_name}</h1>
      <p class="subtitle">One local routine page assembled from first-demo phase clips and returned artifacts.</p>
    </div>
    <div class="top-badges">
      <span>SMPL-X scoring</span>
      <span>G1 non-scoring</span>
      <span>Local-only media</span>
      <span>Fail-closed artifact labels</span>
    </div>
  </header>
  <nav aria-label="Phase navigation">{nav}</nav>
  <main>{section_html}
  </main>
</body>
</html>
"""


def write_routine_html(
    out_dir: Path,
    *,
    routine: str,
    source_materializations: Path,
    gvhmr_json_root: Path | None = None,
    gmr_json_root: Path | None = None,
    model_descriptor: Path | None = None,
    use_rerun_sdk: bool = False,
) -> RoutineHtmlWriteResult:
    validate_output_dir(out_dir)
    split_manifest_path, split_manifest, phases = _load_source_materializations(source_materializations, routine)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    html_path = out_dir / "index.html"
    checked_paths: list[Path] = []
    phase_entries = []

    for phase in phases:
        phase_id = _require_text(phase.get("phase_id"), "phase_id")
        source_reference = _require_text(phase.get("source_materialization"), f"{phase_id} source_materialization")
        source_materialization = _resolve_relative(split_manifest_path, source_reference)
        materialization = _load_json_object(source_materialization, "source materialization")
        require_schema(materialization, SOURCE_MATERIALIZATION_SCHEMA, "source materialization")
        reference_clip = _copy_reference_clip(source_materialization, out_dir, phase_id)
        if reference_clip:
            checked_paths.append(out_dir / reference_clip)

        gvhmr_json = _first_existing(
            _artifact_candidates(
                gvhmr_json_root,
                phase_id,
                ("gvhmr-smplx-joints.json", "gvhmr-smplx-joints.validated.json"),
            )
        )
        gmr_json = _first_existing(
            _artifact_candidates(
                gmr_json_root,
                phase_id,
                ("gmr-unitree-g1.json", "gmr-unitree-g1.normalized.json"),
            )
        )
        phase_out = out_dir / "phases" / phase_id
        phase_demo_path: Path | None = None
        phase_public_demo_index_path: Path | None = None
        phase_error: str | None = None
        g1_status = "missing_gmr_json"
        gvhmr_status = "missing_gvhmr_json"

        if gvhmr_json is not None:
            gvhmr_status = "gvhmr_json_found"
            try:
                g1_track = None
                g1_model = model_descriptor
                if gmr_json is not None:
                    g1_status = "gmr_json_found"
                    preimport_motion = write_gvhmr_json_motion_contract(
                        phase_out / "preimport-motion-contract",
                        gvhmr_json,
                    )
                    if g1_model is None:
                        g1_model = write_fixture_g1_model_descriptor(phase_out / "g1-model").descriptor_path
                    imported = import_gmr_json_track(
                        phase_out / "g1-import",
                        gmr_json,
                        motion_record=preimport_motion.out_dir,
                        model_descriptor_path=g1_model,
                    )
                    g1_track = imported.track_manifest_path
                demo = write_real_conversion_demo(
                    phase_out / "demo",
                    source_materialization=source_materialization,
                    gvhmr_json=gvhmr_json,
                    g1_track=g1_track,
                    model_descriptor=g1_model,
                    use_rerun_sdk=use_rerun_sdk,
                )
                phase_demo_path = demo.manifest_path
                public_demo = _load_json_object(phase_demo_path, "phase demo manifest").get("public_demo")
                if isinstance(public_demo, str):
                    phase_public_demo_manifest_path = (phase_demo_path.parent / public_demo).resolve()
                    phase_public_demo_index_path = phase_public_demo_manifest_path.parent / "index.html"
                gvhmr_status = "smplx_teaching_track_generated"
                if gmr_json is None:
                    g1_status = "missing_gmr_json_fixture_fallback"
                checked_paths.extend(demo.checked_paths)
            except ValueError as exc:
                phase_error = str(exc)
                gvhmr_status = "gvhmr_artifact_invalid"
                if gmr_json is not None:
                    g1_status = "gmr_artifact_not_imported"

        phase_entry = {
            "phase_id": phase_id,
            "name_zh": phase.get("name_zh"),
            "name_en": phase.get("name_en"),
            "start_seconds": phase.get("start_seconds"),
            "end_seconds": phase.get("end_seconds"),
            "source_materialization": _relative_path(source_materialization, manifest_path.parent),
            "source_status": "reference_clip_available" if reference_clip else "source_materialization_only",
            "source_status_label": "original clip available" if reference_clip else "original clip missing",
            "reference_clip": reference_clip,
            "gvhmr_json": _relative_path(gvhmr_json, manifest_path.parent) if gvhmr_json is not None else None,
            "gvhmr_status": gvhmr_status,
            "gvhmr_status_label": _phase_status_label(gvhmr_status),
            "gmr_json": _relative_path(gmr_json, manifest_path.parent) if gmr_json is not None else None,
            "g1_status": g1_status,
            "g1_status_label": _phase_status_label(g1_status),
            "phase_demo": _relative_path(phase_demo_path, manifest_path.parent) if phase_demo_path else None,
            "phase_public_demo": _relative_path(phase_public_demo_index_path, manifest_path.parent)
            if phase_public_demo_index_path
            else None,
            "error": phase_error,
        }
        phase_entries.append(phase_entry)

    payload = {
        "schema": ROUTINE_HTML_SCHEMA,
        "routine": routine,
        "routine_name_zh": split_manifest.get("routine_name_zh"),
        "routine_name_en": split_manifest.get("routine_name_en"),
        "source_split": _relative_path(split_manifest_path, manifest_path.parent),
        "source_video": split_manifest.get("source_video"),
        "source_video_metadata": split_manifest.get("source_video_metadata"),
        "phase_count": len(phase_entries),
        "phases": phase_entries,
        "html": "index.html",
        "scoring_source": "smplx",
        "g1_scoring_allowed": False,
        "artifact_roots": {
            "gvhmr_json_root": _as_posix(gvhmr_json_root) if gvhmr_json_root is not None else None,
            "gmr_json_root": _as_posix(gmr_json_root) if gmr_json_root is not None else None,
        },
        "notes": (
            "This is a local routine assembly page. Missing GVHMR/GMR/render inputs are labeled "
            "explicitly and are not treated as successful runtime execution."
        ),
    }
    _write_json(manifest_path, payload)
    html_path.write_text(_render_routine_html(payload), encoding="utf-8")
    checked_paths.extend([manifest_path, html_path])
    return RoutineHtmlWriteResult(html_path=html_path, manifest_path=manifest_path, checked_paths=checked_paths)


def smoke_check_routine_html(routine_html: Path) -> RoutineSmokeResult:
    manifest_path = _resolve_manifest_path(routine_html)
    manifest = _load_json_object(manifest_path, "routine HTML manifest")
    require_schema(manifest, ROUTINE_HTML_SCHEMA, "routine HTML manifest")
    if manifest.get("scoring_source") != "smplx":
        raise ValueError("routine HTML must keep SMPL-X as scoring_source")
    if manifest.get("g1_scoring_allowed") is not False:
        raise ValueError("routine HTML must keep G1 non-scoring")
    html_reference = manifest.get("html")
    if not isinstance(html_reference, str) or not html_reference:
        raise ValueError("routine HTML manifest is missing html")
    html_path = manifest_path.parent / html_reference
    if not html_path.exists() or not html_path.read_text(encoding="utf-8").strip():
        raise ValueError(f"routine HTML is missing or blank: {html_path}")
    html_text = html_path.read_text(encoding="utf-8")
    phases = manifest.get("phases")
    if not isinstance(phases, list) or not phases:
        raise ValueError("routine HTML manifest must contain phases")
    missing = []
    for phase in phases:
        if not isinstance(phase, dict):
            raise ValueError("routine HTML phases must be objects")
        for key in ("phase_id", "name_zh", "name_en"):
            value = phase.get(key)
            if not isinstance(value, str) or not value:
                raise ValueError(f"routine HTML phase is missing {key}")
            if value not in html_text:
                missing.append(value)
        anchor = f'href="#phase-{phase["phase_id"]}"'
        if anchor not in html_text:
            missing.append(anchor)
    required_fragments = [
        "SMPL-X skeleton teaching track",
        "SMPL-X scoring",
        "G1 non-scoring",
        "Original clip",
        "Unitree G1 visual replay",
        "Provenance",
    ]
    missing.extend(fragment for fragment in required_fragments if fragment not in html_text)
    if missing:
        raise ValueError(f"routine HTML smoke labels are missing: {', '.join(missing)}")
    checked = [manifest_path, html_path]
    for phase in phases:
        reference_clip = phase.get("reference_clip")
        if isinstance(reference_clip, str) and reference_clip:
            clip_path = manifest_path.parent / reference_clip
            if not clip_path.exists() or clip_path.stat().st_size == 0:
                raise ValueError(f"routine HTML reference clip is missing or blank: {clip_path}")
            checked.append(clip_path)
    smoke_path = manifest_path.parent / "smoke.json"
    _write_json(
        smoke_path,
        {
            "schema": ROUTINE_SMOKE_SCHEMA,
            "status": "validated",
            "routine": manifest.get("routine"),
            "phase_count": len(phases),
            "checked_paths": [_as_posix(path) for path in checked],
            "scoring_source": "smplx",
            "g1_scoring_allowed": False,
        },
    )
    checked.append(smoke_path)
    return RoutineSmokeResult(manifest_path=manifest_path, checked_paths=checked)
