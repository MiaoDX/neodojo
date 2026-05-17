from __future__ import annotations

import csv
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import local_file_metadata, require_schema, sha256_file
from .motion_contract import (
    GVHMR_JOINT_EXPORT_SCHEMA,
    _SMPLX_FRAME_PARAMETER_FIELDS,
    _SMPLX_REQUIRED_PARAMETER_FIELDS,
    _write_json,
    validate_output_dir,
)

REAL_CONVERSION_PREP_SCHEMA = "neodojo.real_conversion_prep.v1"
SOURCE_MATERIALIZATION_SCHEMA = "neodojo.real_conversion_source_materialization.v1"
GVHMR_SOURCE_VALIDATION_SCHEMA = "neodojo.gvhmr_source_validation.v1"
GVHMR_GPU_HANDOFF_SCHEMA = "neodojo.gvhmr_gpu_handoff.v1"
GVHMR_RESULT_INSPECTION_SCHEMA = "neodojo.gvhmr_result_inspection.v1"
DEFAULT_SOURCE_INDEX = Path("video/original_videos.csv")
DEFAULT_SOURCE_ID = "03-006"


@dataclass(frozen=True)
class RealConversionPrepWriteResult:
    manifest_path: Path


@dataclass(frozen=True)
class SourceMaterializationWriteResult:
    manifest_path: Path
    trimmed_video_path: Path
    frames_dir: Path


@dataclass(frozen=True)
class SourceValidationWriteResult:
    report_path: Path
    validated_export_path: Path | None
    status: str


@dataclass(frozen=True)
class GvhmrGpuHandoffWriteResult:
    manifest_path: Path
    readme_path: Path
    export_template_path: Path
    checked_paths: list[Path]
    status: str


@dataclass(frozen=True)
class GvhmrResultInspectionWriteResult:
    manifest_path: Path
    checked_paths: list[Path]
    status: str


def _as_posix(path: Path) -> str:
    return str(path).replace("\\", "/")


def _source_id(row: dict[str, str]) -> str:
    return f"{int(row['category_order']):02d}-{int(row['item_order']):03d}"


def _require_float(value: str, field: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"source index row has invalid {field}") from exc
    return parsed


def _load_source_row(source_index: Path, source_id: str) -> dict[str, str]:
    if not source_index.exists():
        raise ValueError(f"source index does not exist: {source_index}")

    with source_index.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    for row in rows:
        if _source_id(row) == source_id:
            return row
    raise ValueError(f"source id {source_id} was not found in {source_index}")


def _validate_trim(start_seconds: float, end_seconds: float, source_duration: float) -> dict[str, Any]:
    if start_seconds < 0:
        raise ValueError("trim start must be non-negative")
    if end_seconds <= start_seconds:
        raise ValueError("trim end must be greater than trim start")
    if end_seconds > source_duration:
        raise ValueError("trim end exceeds source duration")

    return {
        "start_seconds": round(start_seconds, 3),
        "end_seconds": round(end_seconds, 3),
        "duration_seconds": round(end_seconds - start_seconds, 3),
    }


def _parse_rate(value: str | None) -> float | None:
    if not value or value == "0/0":
        return None
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        try:
            parsed_denominator = float(denominator)
            if parsed_denominator == 0:
                return None
            return round(float(numerator) / parsed_denominator, 6)
        except ValueError:
            return None
    try:
        return round(float(value), 6)
    except ValueError:
        return None


def _parse_ffprobe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    streams = payload.get("streams", [])
    video_stream = None
    if isinstance(streams, list):
        for stream in streams:
            if isinstance(stream, dict) and stream.get("codec_type") == "video":
                video_stream = stream
                break

    format_info = payload.get("format", {})
    if not isinstance(format_info, dict):
        format_info = {}
    duration = None
    if video_stream and video_stream.get("duration") is not None:
        duration = video_stream.get("duration")
    elif format_info.get("duration") is not None:
        duration = format_info.get("duration")
    try:
        duration_seconds = round(float(duration), 6) if duration is not None else None
    except (TypeError, ValueError):
        duration_seconds = None

    return {
        "format": {
            "duration_seconds": duration_seconds,
            "size_bytes": int(format_info["size"]) if str(format_info.get("size", "")).isdigit() else None,
            "bit_rate_bps": int(format_info["bit_rate"])
            if str(format_info.get("bit_rate", "")).isdigit()
            else None,
            "format_name": format_info.get("format_name"),
        },
        "video_stream": {
            "codec": video_stream.get("codec_name"),
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "avg_frame_rate": _parse_rate(video_stream.get("avg_frame_rate")),
            "duration_seconds": duration_seconds,
        }
        if video_stream
        else None,
    }


def _ffprobe_media(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    probe: dict[str, Any] = {
        "schema": "neodojo.media_probe.v1",
        "tool": "ffprobe",
        "available": ffprobe is not None,
        "succeeded": False,
        "error": None,
        "format": None,
        "video_stream": None,
    }
    if ffprobe is None:
        probe["error"] = "ffprobe not found on PATH"
        return probe

    completed = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        capture_output=True,
        encoding="utf-8",
        timeout=20,
        check=False,
    )
    if completed.returncode != 0:
        probe["error"] = completed.stderr.strip() or f"ffprobe exited with {completed.returncode}"
        return probe

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        probe["error"] = f"ffprobe returned invalid JSON: {exc}"
        return probe
    if not isinstance(payload, dict):
        probe["error"] = "ffprobe returned non-object JSON"
        return probe

    parsed = _parse_ffprobe_payload(payload)
    probe.update(parsed)
    probe["succeeded"] = parsed["video_stream"] is not None
    if not probe["succeeded"]:
        probe["error"] = "ffprobe found no video stream"
    return probe


def _load_prep_manifest(prep: Path) -> tuple[Path, dict[str, Any]]:
    manifest_path = prep / "real-conversion-prep.json" if prep.is_dir() else prep
    if not manifest_path.exists():
        raise ValueError(f"real conversion prep manifest does not exist: {manifest_path}")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"failed to parse real conversion prep manifest: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("real conversion prep manifest must be a JSON object")
    require_schema(payload, REAL_CONVERSION_PREP_SCHEMA, "real conversion prep manifest")
    return manifest_path, payload


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"{label} does not exist: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"failed to parse {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def _trim_from_manifest(payload: dict[str, Any]) -> dict[str, float]:
    trim = payload.get("trim")
    if not isinstance(trim, dict):
        raise ValueError("real conversion prep manifest is missing trim metadata")
    try:
        start_seconds = float(trim["start_seconds"])
        end_seconds = float(trim["end_seconds"])
        duration_seconds = float(trim["duration_seconds"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("real conversion prep trim metadata must contain numeric start/end/duration") from exc
    if start_seconds < 0 or end_seconds <= start_seconds or duration_seconds <= 0:
        raise ValueError("real conversion prep trim metadata is invalid")
    return {
        "start_seconds": round(start_seconds, 3),
        "end_seconds": round(end_seconds, 3),
        "duration_seconds": round(duration_seconds, 3),
    }


def _resolve_materialization_source(payload: dict[str, Any], local_video: Path | None) -> Path:
    if local_video is not None:
        return local_video

    source_media = payload.get("source_media")
    if isinstance(source_media, dict):
        local_file = source_media.get("local_file")
        if isinstance(local_file, dict):
            resolved = local_file.get("resolved_path")
            if isinstance(resolved, str) and resolved:
                return Path(resolved)
            path = local_file.get("path")
            if isinstance(path, str) and path:
                return Path(path)

    raise ValueError(
        "materializing source media requires --local-video or a prep manifest created with --local-video"
    )


def _format_seconds(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _frame_pattern(frames_dir: Path) -> Path:
    return frames_dir / "frame-%06d.jpg"


def _file_metadata_or_none(
    path: Path,
    *,
    label: str,
    allowed_suffixes: set[str] | None = None,
) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return local_file_metadata(path, label=label, allowed_suffixes=allowed_suffixes)


def _run_ffmpeg(argv: list[str], label: str) -> None:
    completed = subprocess.run(
        argv,
        capture_output=True,
        encoding="utf-8",
        timeout=180,
        check=False,
    )
    if completed.returncode != 0:
        message = (
            completed.stderr.strip()
            or completed.stdout.strip()
            or f"{label} exited with {completed.returncode}"
        )
        raise ValueError(f"ffmpeg {label} failed: {message}")


def _duration_validation(expected_seconds: float, probe: dict[str, Any] | None) -> dict[str, Any]:
    if not probe or not probe.get("succeeded"):
        return {
            "checked": False,
            "succeeded": False,
            "expected_duration_seconds": expected_seconds,
            "actual_duration_seconds": None,
            "delta_seconds": None,
            "tolerance_seconds": None,
            "error": probe.get("error") if isinstance(probe, dict) else "trimmed clip was not probed",
        }

    format_info = probe.get("format")
    duration = None
    if isinstance(format_info, dict):
        duration = format_info.get("duration_seconds")
    try:
        actual_seconds = float(duration)
    except (TypeError, ValueError):
        return {
            "checked": True,
            "succeeded": False,
            "expected_duration_seconds": expected_seconds,
            "actual_duration_seconds": None,
            "delta_seconds": None,
            "tolerance_seconds": None,
            "error": "trimmed clip probe did not include duration_seconds",
        }

    tolerance_seconds = max(0.35, min(1.0, expected_seconds * 0.05))
    delta_seconds = abs(actual_seconds - expected_seconds)
    return {
        "checked": True,
        "succeeded": delta_seconds <= tolerance_seconds,
        "expected_duration_seconds": expected_seconds,
        "actual_duration_seconds": round(actual_seconds, 6),
        "delta_seconds": round(delta_seconds, 6),
        "tolerance_seconds": round(tolerance_seconds, 6),
        "error": None if delta_seconds <= tolerance_seconds else "trimmed clip duration differs from prep trim",
    }


def materialize_real_conversion_source(
    out_dir: Path,
    *,
    prep_manifest: Path = Path("outputs/real-conversion-gate/real-conversion-prep.json"),
    local_video: Path | None = None,
    frame_rate: float = 1.0,
    dry_run: bool = False,
) -> SourceMaterializationWriteResult:
    validate_output_dir(out_dir)
    if frame_rate <= 0:
        raise ValueError("frame rate must be positive")

    prep_manifest_path, prep_payload = _load_prep_manifest(prep_manifest)
    trim = _trim_from_manifest(prep_payload)
    source_video_path = _resolve_materialization_source(prep_payload, local_video)
    source_file = local_file_metadata(
        source_video_path,
        label="local source video",
        allowed_suffixes={".mp4", ".mov", ".m4v", ".webm"},
    )

    source_dir = out_dir / "source"
    frames_dir = source_dir / "frames"
    trimmed_video_path = source_dir / "trimmed-clip.mp4"
    manifest_path = out_dir / "source-materialization.json"
    ffmpeg = shutil.which("ffmpeg")

    trim_command = [
        ffmpeg or "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        _format_seconds(trim["start_seconds"]),
        "-to",
        _format_seconds(trim["end_seconds"]),
        "-i",
        str(source_video_path),
        "-map",
        "0:v:0",
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(trimmed_video_path),
    ]
    frame_command = [
        ffmpeg or "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(trimmed_video_path),
        "-vf",
        f"fps={frame_rate:g}",
        str(_frame_pattern(frames_dir)),
    ]

    if ffmpeg is None and not dry_run:
        raise ValueError("ffmpeg not found on PATH; rerun with --dry-run to write the handoff manifest only")

    materialized = False
    extracted_frame_paths: list[Path] = []
    trim_probe: dict[str, Any] | None = None
    if not dry_run:
        source_dir.mkdir(parents=True, exist_ok=True)
        frames_dir.mkdir(parents=True, exist_ok=True)
        _run_ffmpeg(trim_command, "trim")
        _run_ffmpeg(frame_command, "frame extraction")
        extracted_frame_paths = sorted(frames_dir.glob("frame-*.jpg"))
        if not extracted_frame_paths:
            raise ValueError("ffmpeg frame extraction wrote no frames")
        trim_probe = _ffprobe_media(trimmed_video_path)
        materialized = True

    trimmed_video = _file_metadata_or_none(
        trimmed_video_path,
        label="trimmed source video",
        allowed_suffixes={".mp4"},
    )
    first_frame = (
        _file_metadata_or_none(extracted_frame_paths[0], label="first extracted frame", allowed_suffixes={".jpg"})
        if extracted_frame_paths
        else None
    )
    last_frame = (
        _file_metadata_or_none(extracted_frame_paths[-1], label="last extracted frame", allowed_suffixes={".jpg"})
        if extracted_frame_paths
        else None
    )
    duration_validation = _duration_validation(trim["duration_seconds"], trim_probe)
    expected_export_json = None
    gpu_run = prep_payload.get("gpu_run")
    if isinstance(gpu_run, dict):
        expected_export_json = gpu_run.get("expected_export_json")

    manifest = {
        "schema": SOURCE_MATERIALIZATION_SCHEMA,
        "status": "materialized" if materialized else "dry_run",
        "fixture_only": False,
        "media_committed_to_repo": False,
        "source_prep": {
            "manifest": _as_posix(prep_manifest_path),
            "source_id": prep_payload.get("source", {}).get("id")
            if isinstance(prep_payload.get("source"), dict)
            else None,
            "source_schema": prep_payload.get("schema"),
        },
        "source_media": {
            "schema": "neodojo.source_media_materialized.v1",
            "local_file": source_file,
            "prep_probe": prep_payload.get("source_media", {}).get("probe")
            if isinstance(prep_payload.get("source_media"), dict)
            else None,
            "rights_notes": prep_payload.get("source", {}).get("rights_notes")
            if isinstance(prep_payload.get("source"), dict)
            else None,
        },
        "trim": trim,
        "ffmpeg": {
            "available": ffmpeg is not None,
            "executable": ffmpeg,
            "dry_run": dry_run,
            "commands": [
                {
                    "kind": "trim_clip",
                    "argv": trim_command,
                },
                {
                    "kind": "extract_reference_frames",
                    "argv": frame_command,
                },
            ],
        },
        "outputs": {
            "trimmed_video_path": _as_posix(trimmed_video_path),
            "trimmed_video": trimmed_video,
            "frames_dir": _as_posix(frames_dir),
            "frame_pattern": _as_posix(_frame_pattern(frames_dir)),
            "extracted_frame_count": len(extracted_frame_paths),
            "first_frame": first_frame,
            "last_frame": last_frame,
        },
        "validation": {
            "schema": "neodojo.source_materialization_validation.v1",
            "source_file_validated": True,
            "trimmed_video_written": trimmed_video is not None,
            "frames_extracted": len(extracted_frame_paths) > 0,
            "duration": duration_validation,
            "gvhmr_input_ready": materialized and trimmed_video is not None and len(extracted_frame_paths) > 0,
        },
        "gpu_handoff": {
            "schema": "neodojo.gvhmr_input_handoff.v1",
            "blocked_locally": True,
            "trimmed_video_argument": _as_posix(trimmed_video_path),
            "expected_export_json": expected_export_json,
            "command_template": (
                "python tools/demo/demo.py "
                f"--video {_as_posix(trimmed_video_path)} --output_root <gvhmr-output-dir>"
            ),
            "notes": "Use the materialized trimmed clip on a GPU-capable GVHMR machine; do not commit media outputs.",
        },
    }
    _write_json(manifest_path, manifest)
    return SourceMaterializationWriteResult(
        manifest_path=manifest_path,
        trimmed_video_path=trimmed_video_path,
        frames_dir=frames_dir,
    )


def _resolve_handoff_media_path(reference: str | None, source_materialization: Path) -> Path | None:
    if not reference:
        return None
    path = Path(reference)
    if path.is_absolute() or path.exists():
        return path
    candidate = source_materialization.parent / path
    return candidate if candidate.exists() else path


def _markdown_command(command: str) -> str:
    return f"```bash\n{command}\n```"


def _write_gpu_handoff_readme(
    path: Path,
    *,
    manifest_path: Path,
    status: str,
    input_video: str | None,
    expected_export_json: str,
    upstream_command: str,
    local_import_command: str,
) -> None:
    body = "\n".join(
        [
            "# neodojo GVHMR GPU Handoff",
            "",
            f"Status: `{status}`",
            "",
            "This directory is a metadata handoff for running GVHMR on a separate GPU-capable machine.",
            "It does not contain or copy source video by default, and it does not run GVHMR locally.",
            "",
            "## Files",
            "",
            f"- `{manifest_path.name}`: machine-readable handoff manifest.",
            "- `gvhmr-smplx-joints.template.json`: JSON shape and provenance fields to preserve in the returned export.",
            "",
            "## GPU Input",
            "",
            f"- Trimmed video argument: `{input_video or '<missing>'}`",
            "",
            "## Upstream GVHMR Command Template",
            "",
            _markdown_command(upstream_command),
            "",
            "Fill in the concrete GVHMR environment, checkpoint, and output directory on the GPU machine.",
            "",
            "## Return Artifact",
            "",
            f"Write the returned neodojo export to `{expected_export_json}` and include the provenance fields from the template.",
            "",
            "## Local Validation And Demo",
            "",
            _markdown_command(local_import_command),
            "",
            "The local command validates provenance, imports the SMPL-X teaching joints, and regenerates the local demo/capture lane.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def package_gvhmr_gpu_handoff(
    out_dir: Path,
    *,
    source_materialization: Path,
    expected_export_json: Path | None = None,
) -> GvhmrGpuHandoffWriteResult:
    validate_output_dir(out_dir)
    materialization = _load_json_object(source_materialization, "source materialization manifest")
    require_schema(materialization, SOURCE_MATERIALIZATION_SCHEMA, "source materialization manifest")

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    readme_path = out_dir / "README.md"
    export_template_path = out_dir / "gvhmr-smplx-joints.template.json"

    source_hash = sha256_file(source_materialization)
    trim = materialization.get("trim") if isinstance(materialization.get("trim"), dict) else {}
    source_prep = materialization.get("source_prep") if isinstance(materialization.get("source_prep"), dict) else {}
    outputs = materialization.get("outputs") if isinstance(materialization.get("outputs"), dict) else {}
    validation = materialization.get("validation") if isinstance(materialization.get("validation"), dict) else {}
    gpu_handoff = materialization.get("gpu_handoff") if isinstance(materialization.get("gpu_handoff"), dict) else {}
    trimmed_video = outputs.get("trimmed_video") if isinstance(outputs.get("trimmed_video"), dict) else {}

    input_video = gpu_handoff.get("trimmed_video_argument") or outputs.get("trimmed_video_path")
    input_video = input_video if isinstance(input_video, str) else None
    input_video_path = _resolve_handoff_media_path(input_video, source_materialization)
    input_exists = bool(input_video_path and input_video_path.exists())
    expected_sha = trimmed_video.get("sha256") if isinstance(trimmed_video.get("sha256"), str) else None
    actual_sha = sha256_file(input_video_path) if input_exists and input_video_path is not None else None
    checksum_matches = expected_sha is None or actual_sha == expected_sha
    materialized_ready = bool(validation.get("gvhmr_input_ready"))
    status = "ready_for_gpu" if input_exists and materialized_ready and checksum_matches else "needs_materialization"
    if input_exists and not checksum_matches:
        status = "checksum_mismatch"

    expected_export = (
        _as_posix(expected_export_json)
        if expected_export_json is not None
        else str(gpu_handoff.get("expected_export_json") or out_dir / "gvhmr-smplx-joints.json")
    )
    upstream_command = str(
        gpu_handoff.get("command_template")
        or "python tools/demo/demo.py --video <trimmed-video> --output_root <gvhmr-output-dir>"
    )
    local_import_command = (
        "PYTHONPATH=src python -m neodojo real-conversion import-demo "
        f"--source-materialization {_as_posix(source_materialization)} "
        f"--gvhmr-json {expected_export} "
        "--out outputs/real-demo"
    )
    provenance = {
        "source_materialization_manifest": _as_posix(source_materialization),
        "source_materialization_sha256": source_hash,
        "source_id": source_prep.get("source_id"),
        "trim": trim,
        "input_video": input_video,
        "input_video_sha256": expected_sha,
        "gpu_command": "<fill actual GVHMR command>",
        "runtime": "<fill GPU runtime and hardware>",
        "upstream_version": "<fill GVHMR commit or package version>",
    }

    export_template = {
        "schema": GVHMR_JOINT_EXPORT_SCHEMA,
        "template_only": True,
        "routine": "Baduanjin",
        "form": "imported GVHMR segment",
        "fps": "<fill exported fps>",
        "frames": [],
        "smplx_parameters": {
            "optional": "include mesh-ready SMPL-X pose/shape parameters when available",
        },
        "provenance": provenance,
    }
    _write_json(export_template_path, export_template)

    manifest = {
        "schema": GVHMR_GPU_HANDOFF_SCHEMA,
        "status": status,
        "fixture_only": False,
        "media_committed_to_repo": False,
        "source_materialization": _as_posix(source_materialization),
        "source_materialization_sha256": source_hash,
        "source": {
            "source_id": source_prep.get("source_id"),
            "source_schema": source_prep.get("source_schema"),
        },
        "trim": trim,
        "gpu_input": {
            "trimmed_video_argument": input_video,
            "local_path_checked": _as_posix(input_video_path) if input_video_path is not None else None,
            "exists": input_exists,
            "materialized_ready": materialized_ready,
            "sha256_expected": expected_sha,
            "sha256_actual": actual_sha,
            "checksum_matches": checksum_matches,
        },
        "expected_export": {
            "schema": GVHMR_JOINT_EXPORT_SCHEMA,
            "path": expected_export,
            "template": _as_posix(export_template_path),
        },
        "commands": {
            "upstream_gvhmr": upstream_command,
            "local_import_demo": local_import_command,
        },
        "provenance_to_preserve": provenance,
        "notes": (
            "This handoff packages metadata for an external GVHMR run. It does "
            "not copy source media, run GVHMR locally, or make the returned "
            "artifact valid until the template frames/provenance are filled by "
            "the GPU-side export step."
        ),
    }
    _write_json(manifest_path, manifest)
    _write_gpu_handoff_readme(
        readme_path,
        manifest_path=manifest_path,
        status=status,
        input_video=input_video,
        expected_export_json=expected_export,
        upstream_command=upstream_command,
        local_import_command=local_import_command,
    )

    checked_paths = [manifest_path, readme_path, export_template_path, source_materialization]
    if input_exists and input_video_path is not None:
        checked_paths.append(input_video_path)
    return GvhmrGpuHandoffWriteResult(
        manifest_path=manifest_path,
        readme_path=readme_path,
        export_template_path=export_template_path,
        checked_paths=checked_paths,
        status=status,
    )


def _load_gvhmr_result_object(source: Path) -> tuple[dict[str, Any], str]:
    if not source.exists():
        raise ValueError(f"GVHMR result does not exist: {source}")
    if source.suffix.lower() == ".json":
        return _load_json_object(source, "GVHMR result JSON"), "json"
    try:
        import torch
    except ModuleNotFoundError as exc:
        raise ValueError(
            "inspecting native GVHMR .pt results requires the optional torch "
            "dependency; run this command in the GVHMR/GPU environment or pass "
            "a JSON summary/export instead"
        ) from exc

    try:
        payload = torch.load(source, map_location="cpu")
    except Exception as exc:
        raise ValueError(f"failed to load GVHMR result with torch.load: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("GVHMR result must contain a dictionary")
    return payload, "torch_pt"


def _shape_of(value: Any) -> list[int] | None:
    shape = getattr(value, "shape", None)
    if shape is not None:
        try:
            return [int(dimension) for dimension in shape]
        except (TypeError, ValueError):
            return None
    if isinstance(value, list):
        shape_values = []
        current: Any = value
        while isinstance(current, list):
            shape_values.append(len(current))
            current = current[0] if current else None
        return shape_values
    return None


def _dtype_of(value: Any) -> str | None:
    dtype = getattr(value, "dtype", None)
    return str(dtype) if dtype is not None else None


def _summarize_value(value: Any, *, depth: int = 0) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "type": type(value).__name__,
        "shape": _shape_of(value),
        "dtype": _dtype_of(value),
    }
    if isinstance(value, dict):
        summary["key_count"] = len(value)
        summary["keys"] = sorted(str(key) for key in value.keys())
        if depth < 1:
            summary["children"] = {
                str(key): _summarize_value(child, depth=depth + 1)
                for key, child in sorted(value.items(), key=lambda item: str(item[0]))
            }
    elif isinstance(value, (list, tuple)):
        summary["length"] = len(value)
    return summary


def _candidate_smplx_parameter_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    for key, value in sorted(payload.items(), key=lambda item: str(item[0])):
        if not isinstance(value, dict):
            continue
        field_shapes = {
            field: _shape_of(field_value)
            for field, field_value in value.items()
            if _shape_of(field_value) is not None
        }
        required_present = [field for field in _SMPLX_REQUIRED_PARAMETER_FIELDS if field in value]
        if not required_present and not str(key).startswith("smpl_params"):
            continue
        frame_shapes = {
            field: shape
            for field, shape in field_shapes.items()
            if field in _SMPLX_FRAME_PARAMETER_FIELDS and shape
        }
        frame_counts = sorted({shape[0] for shape in frame_shapes.values() if shape})
        candidates.append(
            {
                "key": str(key),
                "required_fields_present": required_present,
                "missing_required_fields": [
                    field for field in _SMPLX_REQUIRED_PARAMETER_FIELDS if field not in value
                ],
                "field_shapes": field_shapes,
                "frame_count_candidates": frame_counts,
                "mesh_ready": set(_SMPLX_REQUIRED_PARAMETER_FIELDS).issubset(value.keys()),
            }
        )
    return candidates


def _candidate_joint_blocks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    for key, value in sorted(payload.items(), key=lambda item: str(item[0])):
        shape = _shape_of(value)
        if not shape or len(shape) < 3:
            continue
        key_text = str(key).lower()
        if "joint" not in key_text and key_text not in {"j3d", "kp3d"}:
            continue
        candidates.append(
            {
                "key": str(key),
                "shape": shape,
                "dtype": _dtype_of(value),
                "note": "candidate numeric joint tensor; a GPU-side adapter must map it to named teaching joints",
            }
        )
    return candidates


def inspect_gvhmr_result(
    out_dir: Path,
    *,
    source: Path,
) -> GvhmrResultInspectionWriteResult:
    validate_output_dir(out_dir)
    payload, source_format = _load_gvhmr_result_object(source)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"

    smplx_candidates = _candidate_smplx_parameter_blocks(payload)
    joint_candidates = _candidate_joint_blocks(payload)
    status = "inspectable"
    if payload.get("schema") == GVHMR_JOINT_EXPORT_SCHEMA and isinstance(
        payload.get("frames", payload.get("smplx_joints")),
        list,
    ):
        status = "already_neodojo_export"
    elif not smplx_candidates and not joint_candidates:
        status = "no_candidate_blocks"

    manifest = {
        "schema": GVHMR_RESULT_INSPECTION_SCHEMA,
        "status": status,
        "source": _as_posix(source),
        "source_resolved": _as_posix(source.resolve()),
        "source_sha256": sha256_file(source),
        "source_format": source_format,
        "top_level_keys": sorted(str(key) for key in payload.keys()),
        "top_level_summary": {
            str(key): _summarize_value(value)
            for key, value in sorted(payload.items(), key=lambda item: str(item[0]))
        },
        "candidate_smplx_parameter_blocks": smplx_candidates,
        "candidate_joint_blocks": joint_candidates,
        "export_guidance": {
            "expected_schema": GVHMR_JOINT_EXPORT_SCHEMA,
            "recommended_parameter_block": smplx_candidates[0]["key"] if smplx_candidates else None,
            "requires_gpu_side_named_teaching_joints": True,
            "notes": (
                "GVHMR demo results are native model outputs. To import them into "
                "neodojo, export named SMPL-X teaching joints plus provenance into "
                "neodojo.gvhmr_smplx_joints.v1. If only SMPL-X parameters are "
                "present, run the SMPL-X body model in the licensed GPU/GVHMR "
                "environment and map the resulting joints to the neodojo teaching "
                "joint names."
            ),
        },
    }
    _write_json(manifest_path, manifest)
    return GvhmrResultInspectionWriteResult(
        manifest_path=manifest_path,
        checked_paths=[source, manifest_path],
        status=status,
    )


def _comparison(
    *,
    name: str,
    expected: Any,
    actual: Any,
    required: bool = True,
    tolerance: float | None = None,
) -> dict[str, Any]:
    missing = actual is None
    delta = None
    if missing:
        status = "missing" if required else "skipped"
        passed = not required
    elif tolerance is not None and isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        delta = abs(float(expected) - float(actual))
        passed = delta <= tolerance
        status = "pass" if passed else "fail"
    else:
        passed = actual == expected
        status = "pass" if passed else "fail"
    return {
        "name": name,
        "required": required,
        "status": status,
        "passed": passed,
        "expected": expected,
        "actual": actual,
        "delta": round(delta, 6) if isinstance(delta, float) else None,
        "tolerance": tolerance,
    }


def _nested(payload: dict[str, Any], *keys: str) -> Any:
    value: Any = payload
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _motion_duration(payload: dict[str, Any]) -> tuple[int | None, float | None, float | None]:
    frames = payload.get("frames", payload.get("smplx_joints"))
    frame_count = len(frames) if isinstance(frames, list) else None
    fps = _as_float(payload.get("fps"))
    duration = round(frame_count / fps, 6) if frame_count is not None and fps else None
    return frame_count, fps, duration


def validate_gvhmr_source(
    out_dir: Path,
    *,
    source_materialization: Path,
    gvhmr_json: Path,
) -> SourceValidationWriteResult:
    validate_output_dir(out_dir)
    materialization = _load_json_object(source_materialization, "source materialization manifest")
    require_schema(materialization, SOURCE_MATERIALIZATION_SCHEMA, "source materialization manifest")
    export = _load_json_object(gvhmr_json, "GVHMR SMPL-X export")
    require_schema(export, GVHMR_JOINT_EXPORT_SCHEMA, "GVHMR SMPL-X export")

    provenance = export.get("provenance")
    provenance_missing = not isinstance(provenance, dict)
    provenance = provenance if isinstance(provenance, dict) else {}
    materialization_sha256 = sha256_file(source_materialization)
    trim = materialization.get("trim", {})
    trim = trim if isinstance(trim, dict) else {}
    output = materialization.get("outputs", {})
    output = output if isinstance(output, dict) else {}
    trimmed_video = output.get("trimmed_video")
    trimmed_video = trimmed_video if isinstance(trimmed_video, dict) else {}
    frame_count, fps, motion_duration = _motion_duration(export)
    expected_duration = _as_float(trim.get("duration_seconds"))
    duration_tolerance = max(0.35, min(1.0, expected_duration * 0.05)) if expected_duration else 0.35

    checks = [
        _comparison(
            name="source_materialization_manifest",
            expected=_as_posix(source_materialization),
            actual=provenance.get("source_materialization_manifest"),
        ),
        _comparison(
            name="source_materialization_sha256",
            expected=materialization_sha256,
            actual=provenance.get("source_materialization_sha256"),
        ),
        _comparison(
            name="source_id",
            expected=_nested(materialization, "source_prep", "source_id"),
            actual=provenance.get("source_id"),
        ),
        _comparison(
            name="trim_start_seconds",
            expected=_as_float(trim.get("start_seconds")),
            actual=_as_float(_nested(provenance, "trim", "start_seconds")),
            tolerance=0.001,
        ),
        _comparison(
            name="trim_end_seconds",
            expected=_as_float(trim.get("end_seconds")),
            actual=_as_float(_nested(provenance, "trim", "end_seconds")),
            tolerance=0.001,
        ),
        _comparison(
            name="trim_duration_seconds",
            expected=expected_duration,
            actual=_as_float(_nested(provenance, "trim", "duration_seconds")),
            tolerance=0.001,
        ),
        _comparison(
            name="input_video_path",
            expected=_nested(materialization, "gpu_handoff", "trimmed_video_argument"),
            actual=provenance.get("input_video"),
        ),
        _comparison(
            name="input_video_sha256",
            expected=trimmed_video.get("sha256"),
            actual=provenance.get("input_video_sha256"),
            required=trimmed_video.get("sha256") is not None,
        ),
        _comparison(
            name="motion_duration_matches_trim",
            expected=expected_duration,
            actual=motion_duration,
            tolerance=duration_tolerance,
        ),
    ]
    status = "missing_provenance" if provenance_missing else "validated"
    if any(check["required"] and not check["passed"] for check in checks):
        status = "failed" if not provenance_missing else "missing_provenance"

    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "source-validation.json"
    validated_export_path = out_dir / "gvhmr-smplx-joints.validated.json"
    report = {
        "schema": GVHMR_SOURCE_VALIDATION_SCHEMA,
        "status": status,
        "passed": status == "validated",
        "source_materialization": _as_posix(source_materialization),
        "source_materialization_sha256": materialization_sha256,
        "gvhmr_json": _as_posix(gvhmr_json),
        "motion": {
            "frame_count": frame_count,
            "fps": fps,
            "duration_seconds": motion_duration,
        },
        "checks": checks,
        "provenance": {
            "available": not provenance_missing,
            "gpu_command": provenance.get("gpu_command"),
            "runtime": provenance.get("runtime"),
            "upstream_version": provenance.get("upstream_version"),
        },
    }
    _write_json(report_path, report)
    validated_path: Path | None = None
    if status == "validated":
        validated_export = {
            **export,
            "source_validation": {
                "schema": GVHMR_SOURCE_VALIDATION_SCHEMA,
                "status": status,
                "report": _relative_path_for_validation(report_path, validated_export_path.parent),
                "source_materialization_sha256": materialization_sha256,
            },
        }
        _write_json(validated_export_path, validated_export)
        validated_path = validated_export_path

    return SourceValidationWriteResult(
        report_path=report_path,
        validated_export_path=validated_path,
        status=status,
    )


def _relative_path_for_validation(path: Path, start: Path) -> str:
    try:
        return str(path.relative_to(start)).replace("\\", "/")
    except ValueError:
        return _as_posix(path)


def _source_media_metadata(planned_video_path: Path, local_video: Path | None, trim: dict[str, Any]) -> dict[str, Any]:
    media: dict[str, Any] | None = None
    media_probe: dict[str, Any] | None = None
    validation = {
        "local_file_supplied": local_video is not None,
        "local_file_validated": False,
        "media_probe_succeeded": False,
        "media_committed_to_repo": False,
    }
    if local_video is not None:
        media = local_file_metadata(
            local_video,
            label="local source video",
            allowed_suffixes={".mp4", ".mov", ".m4v", ".webm"},
        )
        media_probe = _ffprobe_media(local_video)
        validation["local_file_validated"] = True
        validation["media_probe_succeeded"] = bool(media_probe.get("succeeded"))

    return {
        "schema": "neodojo.source_media.v1",
        "planned_local_path": _as_posix(planned_video_path),
        "local_file": media,
        "probe": media_probe,
        "validation": validation,
        "reference_video_sync": {
            "schema": "neodojo.reference_video_sync.v1",
            "local_only": True,
            "available": media is not None,
            "media": media,
            "trim_start_seconds": trim["start_seconds"],
            "trim_end_seconds": trim["end_seconds"],
            "frame_zero_offset_seconds": trim["start_seconds"],
            "sync_confidence": "trim metadata only" if media is not None else "missing local file",
        },
    }


def write_real_conversion_prep(
    out_dir: Path,
    *,
    source_index: Path = DEFAULT_SOURCE_INDEX,
    source_id: str = DEFAULT_SOURCE_ID,
    local_video: Path | None = None,
    start_seconds: float = 0.0,
    end_seconds: float = 12.0,
    rights_notes: str = "licensing unconfirmed; use local/user-supplied source before GPU run",
) -> RealConversionPrepWriteResult:
    validate_output_dir(out_dir)
    row = _load_source_row(source_index, source_id)
    source_duration = _require_float(row["duration_seconds"], "duration_seconds")
    trim = _validate_trim(start_seconds, end_seconds, source_duration)
    planned_video_path = local_video or Path(row["recommended_output_path"])
    source_media = _source_media_metadata(planned_video_path, local_video, trim)

    manifest_path = out_dir / "real-conversion-prep.json"
    export_json_path = out_dir / "gvhmr-smplx-joints.json"
    gpu_output_dir = out_dir / "gvhmr-output"
    manifest = {
        "schema": REAL_CONVERSION_PREP_SCHEMA,
        "status": "gpu_gate_pending",
        "source": {
            "id": source_id,
            "category": row["category_slug"],
            "category_chinese": row["category_chinese"],
            "article_title_chinese": row["article_title_chinese"],
            "title_english": row["title_english"],
            "article_url": row["article_url"],
            "source_mp4_url": row["source_mp4_url"],
            "selected_quality": row["selected_quality"],
            "resolution": row["resolution"],
            "duration_seconds": source_duration,
            "source_size_mib": _require_float(row["source_size_mib"], "source_size_mib"),
            "recommended_output_path": row["recommended_output_path"],
            "local_video_path": _as_posix(planned_video_path),
            "rights_notes": rights_notes,
        },
        "source_media": source_media,
        "trim": trim,
        "gpu_run": {
            "required": True,
            "blocked_locally": True,
            "expected_output_dir": _as_posix(gpu_output_dir),
            "expected_export_json": _as_posix(export_json_path),
            "gvhmr_command_template": (
                "python tools/demo/demo.py --video <trimmed-video> --output_root <gvhmr-output-dir>"
            ),
        },
        "next_commands": {
            "download_source_dry_run": f"./video/download_originals.py --id {source_id} --dry-run",
            "materialize_source": (
                "PYTHONPATH=src python -m neodojo real-conversion materialize-source "
                f"--prep {_as_posix(manifest_path)} --local-video <local-source-video> "
                "--dry-run --out outputs/real-conversion-source"
            ),
            "package_gpu_handoff": (
                "PYTHONPATH=src python -m neodojo real-conversion package-gpu-handoff "
                "--source-materialization outputs/real-conversion-source/source-materialization.json "
                "--out outputs/gvhmr-gpu-handoff"
            ),
            "inspect_gvhmr_result": (
                "PYTHONPATH=src python -m neodojo real-conversion inspect-gvhmr-result "
                "--source outputs/real-conversion-gate/hmr4d_results.pt "
                "--out outputs/gvhmr-result-inspection"
            ),
            "import_motion_record": (
                "PYTHONPATH=src python -m neodojo motion-record create "
                "--from-gvhmr-json outputs/real-conversion-validation/gvhmr-smplx-joints.validated.json "
                "--out outputs/real-motion-contract"
            ),
            "import_demo": (
                "PYTHONPATH=src python -m neodojo real-conversion import-demo "
                "--source-materialization outputs/real-conversion-source/source-materialization.json "
                f"--gvhmr-json {_as_posix(export_json_path)} "
                "--out outputs/real-demo"
            ),
            "validate_gvhmr_source": (
                "PYTHONPATH=src python -m neodojo real-conversion validate-source "
                "--source-materialization outputs/real-conversion-source/source-materialization.json "
                f"--gvhmr-json {_as_posix(export_json_path)} "
                "--out outputs/real-conversion-validation"
            ),
            "build_g1_track": (
                "PYTHONPATH=src python -m neodojo tracks build "
                "--motion-record outputs/real-motion-contract "
                "--robot unitree_g1 --out outputs/real-g1-visual"
            ),
            "play_demo": (
                "PYTHONPATH=src python -m neodojo demo play "
                "--motion-record outputs/real-motion-contract "
                "--g1-track outputs/real-g1-visual/tracks/g1/manifest.json "
                "--out outputs/real-teaching-demo"
            ),
        },
    }
    _write_json(manifest_path, manifest)
    return RealConversionPrepWriteResult(manifest_path=manifest_path)
