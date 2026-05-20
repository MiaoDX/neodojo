from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import local_file_metadata
from .motion_contract import _write_json, validate_output_dir
from .real_conversion import _ffprobe_media

BILIBILI_DOWNLOAD_SCHEMA = "neodojo.bilibili_download.v1"
BILIBILI_MANIFEST_SCHEMA = "neodojo.bilibili_source_manifest.v1"
DEFAULT_BILIBILI_MANIFEST = Path("video/bilibili/manifest.json")
DEFAULT_BILIBILI_DOWNLOAD_OUT = Path("outputs/bilibili-download")

ROUTINE_BY_BVID = {
    "BV1gT4y1m7ec": "baduanjin",
    "BV1sF411F7Tg": "yijinjing",
    "BV1J3411s7Ph": "wuqinxi",
}


@dataclass(frozen=True)
class BilibiliDownloadWriteResult:
    manifest_path: Path
    checked_paths: list[Path]
    status: str


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


def _load_bilibili_entries(manifest_path: Path) -> list[dict[str, Any]]:
    payload = _load_json_object(manifest_path, "Bilibili manifest")
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Bilibili manifest must contain non-empty entries")
    normalized = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Bilibili manifest entry {index} must be an object")
        bvid = entry.get("bvid")
        page_url = entry.get("page_url")
        output_path = entry.get("output_path")
        if not isinstance(bvid, str) or not bvid:
            raise ValueError(f"Bilibili manifest entry {index} is missing bvid")
        if not isinstance(page_url, str) or not page_url:
            raise ValueError(f"Bilibili manifest entry {bvid} is missing page_url")
        if not isinstance(output_path, str) or not output_path:
            raise ValueError(f"Bilibili manifest entry {bvid} is missing output_path")
        normalized.append(entry)
    return normalized


def _quality_format(quality: str) -> str:
    if quality == "480p":
        return "bv*[height<=480]+ba/b[height<=480]/best[height<=480]/best"
    if quality == "best":
        return "bv*+ba/best"
    raise ValueError("quality must be either 480p or best")


def build_ytdlp_command(
    entry: dict[str, Any],
    *,
    output_path: Path,
    quality: str = "480p",
    cookies: Path | None = None,
    cookies_from_browser: str | None = None,
) -> list[str]:
    """Build the stable yt-dlp command for one tracked Bilibili source."""

    if cookies is not None and cookies_from_browser is not None:
        raise ValueError("use either --cookies or --cookies-from-browser, not both")

    command = [
        "yt-dlp",
        "--no-playlist",
        "--merge-output-format",
        "mp4",
        "--remux-video",
        "mp4",
        "--format",
        _quality_format(quality),
        "--output",
        str(output_path),
    ]
    if cookies is not None:
        command.extend(["--cookies", str(cookies)])
    if cookies_from_browser is not None:
        command.extend(["--cookies-from-browser", cookies_from_browser])
    command.append(str(entry["page_url"]))
    return command


def _decode_smoke(path: Path) -> dict[str, Any]:
    ffmpeg = shutil.which("ffmpeg")
    result: dict[str, Any] = {
        "schema": "neodojo.media_decode_smoke.v1",
        "tool": "ffmpeg",
        "available": ffmpeg is not None,
        "succeeded": False,
        "error": None,
    }
    if ffmpeg is None:
        result["error"] = "ffmpeg not found on PATH"
        return result

    completed = subprocess.run(
        [ffmpeg, "-v", "error", "-xerror", "-i", str(path), "-f", "null", "-"],
        capture_output=True,
        encoding="utf-8",
        timeout=300,
        check=False,
    )
    result["succeeded"] = completed.returncode == 0
    if completed.returncode != 0:
        result["error"] = completed.stderr.strip() or f"ffmpeg exited with {completed.returncode}"
    return result


def _selected_entries(entries: list[dict[str, Any]], routines: list[str] | None) -> list[dict[str, Any]]:
    if not routines:
        return entries
    requested = set(routines)
    unknown = requested - set(ROUTINE_BY_BVID.values())
    if unknown:
        raise ValueError(f"unknown routine for Bilibili download: {', '.join(sorted(unknown))}")
    selected = [entry for entry in entries if ROUTINE_BY_BVID.get(str(entry.get("bvid"))) in requested]
    if not selected:
        raise ValueError("no Bilibili manifest entries matched the requested routines")
    return selected


def write_bilibili_download_manifest(
    out_dir: Path,
    *,
    manifest_path: Path = DEFAULT_BILIBILI_MANIFEST,
    routines: list[str] | None = None,
    media_dir: Path | None = None,
    quality: str = "480p",
    cookies: Path | None = None,
    cookies_from_browser: str | None = None,
    dry_run: bool = True,
) -> BilibiliDownloadWriteResult:
    validate_output_dir(out_dir)
    entries = _selected_entries(_load_bilibili_entries(manifest_path), routines)
    if cookies is not None:
        local_file_metadata(cookies, label="yt-dlp cookies file")
    if cookies is not None and cookies_from_browser is not None:
        raise ValueError("use either --cookies or --cookies-from-browser, not both")

    out_dir.mkdir(parents=True, exist_ok=True)
    ytdlp = shutil.which("yt-dlp")
    results = []
    checked_paths: list[Path] = []
    status = "dry_run" if dry_run else "downloaded"

    for entry in entries:
        source_output = Path(str(entry["output_path"]))
        output_path = (media_dir / source_output.name) if media_dir is not None else source_output
        command = build_ytdlp_command(
            entry,
            output_path=output_path,
            quality=quality,
            cookies=cookies,
            cookies_from_browser=cookies_from_browser,
        )
        run_result: dict[str, Any] = {
            "routine": ROUTINE_BY_BVID.get(str(entry.get("bvid"))),
            "bvid": entry["bvid"],
            "aid": entry.get("aid"),
            "cid": entry.get("cid"),
            "title": entry.get("title"),
            "page_url": entry.get("page_url"),
            "quality": quality,
            "output_path": _as_posix(output_path),
            "command": command,
            "dry_run": dry_run,
            "yt_dlp_available": ytdlp is not None,
            "completed_process": None,
            "output_file": None,
            "ffprobe": None,
            "decode_smoke": None,
            "status": "planned" if dry_run else "pending",
        }

        if not dry_run:
            if ytdlp is None:
                raise ValueError("yt-dlp not found on PATH; install yt-dlp or rerun with --dry-run")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            completed = subprocess.run(
                command,
                capture_output=True,
                encoding="utf-8",
                timeout=1800,
                check=False,
            )
            run_result["completed_process"] = {
                "returncode": completed.returncode,
                "stdout_tail": completed.stdout[-4000:],
                "stderr_tail": completed.stderr[-4000:],
            }
            if completed.returncode != 0:
                run_result["status"] = "download_failed"
                status = "failed"
                results.append(run_result)
                continue
            output_file = local_file_metadata(output_path, label="downloaded Bilibili video", allowed_suffixes={".mp4"})
            probe = _ffprobe_media(output_path)
            decode = _decode_smoke(output_path)
            run_result["output_file"] = output_file
            run_result["ffprobe"] = probe
            run_result["decode_smoke"] = decode
            run_result["status"] = "validated" if probe.get("succeeded") and decode.get("succeeded") else "validation_failed"
            checked_paths.append(output_path)
            if run_result["status"] != "validated":
                status = "failed"
        else:
            if output_path.exists() and output_path.is_file():
                run_result["output_file"] = local_file_metadata(
                    output_path,
                    label="existing Bilibili video",
                    allowed_suffixes={".mp4"},
                )
        results.append(run_result)

    manifest = {
        "schema": BILIBILI_DOWNLOAD_SCHEMA,
        "status": status,
        "dry_run": dry_run,
        "source_manifest": _as_posix(manifest_path),
        "media_dir": _as_posix(media_dir) if media_dir is not None else None,
        "quality": quality,
        "cookies": _as_posix(cookies) if cookies is not None else None,
        "cookies_from_browser": cookies_from_browser,
        "stable_identifiers_only": True,
        "transient_play_urls_recorded": False,
        "entries": results,
        "notes": (
            "Bilibili media URLs expire. This manifest stores stable BVID/AID/CID "
            "metadata and yt-dlp commands, not transient playurl responses."
        ),
    }
    manifest_path_out = out_dir / "manifest.json"
    _write_json(manifest_path_out, manifest)

    if status == "failed":
        raise ValueError(f"one or more Bilibili downloads failed; inspect {manifest_path_out}")

    return BilibiliDownloadWriteResult(
        manifest_path=manifest_path_out,
        checked_paths=checked_paths,
        status=status,
    )
