from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .demo_html import write_demo
from .g1_visual import build_g1_visual_track, register_g1_model, write_fixture_g1_model_descriptor
from .motion_contract import write_fixture_motion_contract
from .teaching_playback import write_teaching_playback_demo


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

    robot_model = subparsers.add_parser(
        "robot-model",
        help="register local robot model assets for visual tracks",
    )
    robot_subparsers = robot_model.add_subparsers(dest="robot_command", required=True)
    robot_register = robot_subparsers.add_parser(
        "register",
        help="write a Unitree G1 model descriptor",
    )
    robot_register.add_argument("--robot", choices=["unitree_g1"], default="unitree_g1")
    robot_register.add_argument("--model", type=Path, help="local URDF or MJCF/XML model path")
    robot_register.add_argument(
        "--mesh-root",
        type=Path,
        action="append",
        default=[],
        help="local directory for mesh references; may be repeated",
    )
    robot_register.add_argument(
        "--fixture",
        action="store_true",
        help="write a G1-like fixture descriptor instead of registering real assets",
    )
    robot_register.add_argument("--source-url", help="upstream model source URL")
    robot_register.add_argument("--source-revision", help="upstream commit, tag, or version")
    robot_register.add_argument("--license", dest="license_name", help="upstream asset license")
    robot_register.add_argument("--variant", help="model variant notes")
    robot_register.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/g1-visual"),
        help="output directory for the G1 model descriptor",
    )

    tracks = subparsers.add_parser(
        "tracks",
        help="build derived visual track manifests",
    )
    tracks_subparsers = tracks.add_subparsers(dest="tracks_command", required=True)
    tracks_build = tracks_subparsers.add_parser(
        "build",
        help="build a fixture-derived Unitree G1 visual track from a motion record",
    )
    tracks_build.add_argument(
        "--motion-record",
        type=Path,
        required=True,
        help="motion-record root directory or manifest path",
    )
    tracks_build.add_argument("--robot", choices=["unitree_g1"], default="unitree_g1")
    tracks_build.add_argument(
        "--model-descriptor",
        type=Path,
        help="optional Unitree G1 model descriptor manifest",
    )
    tracks_build.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/g1-visual"),
        help="output directory for the G1 visual-track manifest and report",
    )

    demo = subparsers.add_parser(
        "demo",
        help="write local teaching playback artifacts from track manifests",
    )
    demo_subparsers = demo.add_subparsers(dest="demo_command", required=True)
    demo_play = demo_subparsers.add_parser(
        "play",
        help="write a self-contained teaching playback HTML demo from SMPL-X and G1 tracks",
    )
    demo_play.add_argument(
        "--motion-record",
        type=Path,
        required=True,
        help="motion-record root directory or manifest path",
    )
    demo_play.add_argument(
        "--g1-track",
        type=Path,
        required=True,
        help="G1 visual-track root directory or manifest path",
    )
    demo_play.add_argument("--annotations", type=Path, help="optional manual key-frame annotation JSON")
    demo_play.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/teaching-demo"),
        help="output directory for the teaching playback HTML and manifest",
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

        if args.command == "robot-model" and args.robot_command == "register":
            if args.fixture:
                result = write_fixture_g1_model_descriptor(args.out)
            else:
                if args.model is None:
                    parser.error("--model is required unless --fixture is used")
                result = register_g1_model(
                    args.out,
                    args.model,
                    mesh_roots=args.mesh_root,
                    source_url=args.source_url,
                    source_revision=args.source_revision,
                    license_name=args.license_name,
                    variant=args.variant,
                )
            print(f"wrote {result.descriptor_path}")
            return 0

        if args.command == "tracks" and args.tracks_command == "build":
            result = build_g1_visual_track(
                args.motion_record,
                args.out,
                model_descriptor_path=args.model_descriptor,
            )
            print(f"wrote {result.track_manifest_path}")
            print(f"wrote {result.comparison_report_path}")
            return 0

        if args.command == "demo" and args.demo_command == "play":
            result = write_teaching_playback_demo(
                args.out,
                motion_record=args.motion_record,
                g1_track=args.g1_track,
                annotations_path=args.annotations,
            )
            print(f"wrote {result.html_path}")
            print(f"wrote {result.manifest_path}")
            return 0
    except ValueError as exc:
        parser.error(str(exc))

    parser.error(f"unknown command: {args.command}")
    return 2
