#!/usr/bin/env python3
"""Download original remote MP4s listed in original_videos.json.

The index intentionally stores URLs and metadata without keeping the large
source MP4 files locally. This helper rehydrates selected originals when needed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = Path(__file__).resolve().with_name("original_videos.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download original video sources from the saved index.")
    parser.add_argument("--id", action="append", default=[], help="Video id like 01-001. Can be repeated.")
    parser.add_argument("--category", action="append", default=[], help="Category slug, for example 01_dawu.")
    parser.add_argument("--all", action="store_true", help="Download every indexed original source.")
    parser.add_argument("--max-total-mib", type=float, default=None, help="Stop selecting once this total source size is reached.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be downloaded without downloading.")
    return parser.parse_args()


def video_id(entry: dict) -> str:
    return f"{int(entry['category_order']):02d}-{int(entry['item_order']):03d}"


def select_entries(entries: list[dict], args: argparse.Namespace) -> list[dict]:
    wanted_ids = set(args.id)
    wanted_categories = set(args.category)
    if not args.all and not wanted_ids and not wanted_categories:
        raise SystemExit("Refusing to download without --id, --category, or --all. Use --dry-run to inspect.")

    selected = []
    total = 0
    max_bytes = None if args.max_total_mib is None else int(args.max_total_mib * 1024 * 1024)
    for entry in entries:
        matches = args.all or video_id(entry) in wanted_ids or entry["category_slug"] in wanted_categories
        if not matches:
            continue
        size = int(entry.get("source_size_bytes") or 0)
        if max_bytes is not None and selected and total + size > max_bytes:
            continue
        selected.append(entry)
        total += size
    return selected


def download(entry: dict) -> int:
    output = ROOT / entry["recommended_output_path"]
    expected_size = int(entry.get("source_size_bytes") or 0)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and expected_size and output.stat().st_size == expected_size:
        print(f"skip existing {video_id(entry)} {output}")
        return 0

    part = output.with_suffix(output.suffix + ".part")
    cmd = [
        "curl",
        "-L",
        "--retry",
        "4",
        "--retry-all-errors",
        "--connect-timeout",
        "25",
        "-C",
        "-",
        "-o",
        str(part),
        entry["source_mp4_url"],
    ]
    print(f"download {video_id(entry)} {entry['source_size_mib']} MiB -> {output}")
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        print(f"curl failed for {video_id(entry)}", file=sys.stderr)
        return proc.returncode
    if expected_size and part.stat().st_size != expected_size:
        print(
            f"size mismatch for {video_id(entry)}: expected {expected_size}, got {part.stat().st_size}",
            file=sys.stderr,
        )
        return 1
    part.replace(output)
    return 0


def main() -> int:
    args = parse_args()
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    selected = select_entries(index["entries"], args)
    total_mib = sum(float(entry["source_size_mib"]) for entry in selected)
    print(f"selected {len(selected)} files, {total_mib:.2f} MiB")
    for entry in selected:
        print(f"{video_id(entry)} {entry['source_size_mib']:>8} MiB {entry['resolution']:>9} {entry['category_slug']} {entry['article_title_chinese']}")
    if args.dry_run:
        return 0

    rc = 0
    for entry in selected:
        rc = download(entry) or rc
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
