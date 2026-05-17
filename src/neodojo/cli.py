from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .demo_html import write_demo


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

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "demo-html":
        result = write_demo(args.out, frame_count=args.frames)
        print(f"wrote {result.html_path}")
        print(f"wrote {result.manifest_path}")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2
