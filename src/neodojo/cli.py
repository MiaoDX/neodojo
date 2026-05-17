from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .demo_html import write_demo
from .motion_contract import write_fixture_motion_contract


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="neodojo",
        description="Local fixture tools for the neodojo bootstrap demo.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo_html = subparsers.add_parser(
        "demo-html",
        help="write a self-contained fixture-only teaching playback HTML demo",
    )
    demo_html.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/html-demo"),
        help="output directory for index.html and manifest.json",
    )
    demo_html.add_argument(
        "--frames",
        type=int,
        default=96,
        help="number of synthetic fixture frames to generate",
    )

    motion_record = subparsers.add_parser(
        "motion-record",
        help="create and validate local motion-record artifacts",
    )
    motion_subparsers = motion_record.add_subparsers(dest="motion_command", required=True)
    motion_create = motion_subparsers.add_parser(
        "create",
        help="write a fixture-backed SMPL-X motion-record contract",
    )
    motion_create.add_argument(
        "--fixture",
        choices=["synthetic"],
        default="synthetic",
        help="fixture source to import into the local motion-record contract",
    )
    motion_create.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/motion-contract"),
        help="output directory for the motion-record and SMPL-X track manifests",
    )
    motion_create.add_argument(
        "--frames",
        type=int,
        default=96,
        help="number of synthetic fixture frames to generate",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "demo-html":
            result = write_demo(args.out, frame_count=args.frames)
            print(f"wrote {result.html_path}")
            print(f"wrote {result.manifest_path}")
            print(f"wrote {result.motion_record_manifest_path}")
            print(f"wrote {result.smplx_track_manifest_path}")
            return 0

        if args.command == "motion-record" and args.motion_command == "create":
            result = write_fixture_motion_contract(args.out, frame_count=args.frames)
            print(f"wrote {result.motion_record_manifest_path}")
            print(f"wrote {result.smplx_track_manifest_path}")
            return 0
    except ValueError as exc:
        parser.error(str(exc))

    parser.error(f"unknown command: {args.command}")
    return 2
