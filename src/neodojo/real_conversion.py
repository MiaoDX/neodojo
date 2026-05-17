from __future__ import annotations

import csv
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import local_file_metadata
from .motion_contract import _write_json, validate_output_dir

REAL_CONVERSION_PREP_SCHEMA = "neodojo.real_conversion_prep.v1"
DEFAULT_SOURCE_INDEX = Path("video/original_videos.csv")
DEFAULT_SOURCE_ID = "03-006"


@dataclass(frozen=True)
class RealConversionPrepWriteResult:
    manifest_path: Path


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
            "import_motion_record": (
                "PYTHONPATH=src python -m neodojo motion-record create "
                f"--from-gvhmr-json {_as_posix(export_json_path)} --out outputs/real-motion-contract"
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
