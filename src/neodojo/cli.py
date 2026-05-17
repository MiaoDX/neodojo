from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .demo_html import write_demo
from .g1_visual import build_g1_visual_track, register_g1_model, write_fixture_g1_model_descriptor
from .g1_render import write_g1_render
from .motion_contract import write_fixture_motion_contract, write_gvhmr_json_motion_contract
from .public_demo import write_public_demo
from .real_conversion import DEFAULT_SOURCE_ID, DEFAULT_SOURCE_INDEX, write_real_conversion_prep
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
        help="write an SMPL-X motion-record contract",
    )
    motion_source = motion_create.add_mutually_exclusive_group()
    motion_source.add_argument(
        "--fixture",
        choices=["synthetic"],
        default="synthetic",
        help="fixture source to import into the local motion-record contract",
    )
    motion_source.add_argument(
        "--from-gvhmr-json",
        type=Path,
        help="import an external GVHMR SMPL-X teaching-joints JSON export",
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
    demo_play.add_argument("--reference-video", type=Path, help="optional local-only original video reference")
    demo_play.add_argument(
        "--reference-trim-start",
        type=float,
        default=0.0,
        help="trim start offset, in seconds, for optional reference video sync",
    )
    demo_play.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/teaching-demo"),
        help="output directory for the teaching playback HTML and manifest",
    )
    demo_export = demo_subparsers.add_parser(
        "export-rerun",
        help="write the public fixture demo scene and Rerun-target artifact",
    )
    demo_export.add_argument(
        "--playback",
        type=Path,
        required=True,
        help="teaching playback manifest path",
    )
    demo_export.add_argument(
        "--g1-render",
        type=Path,
        help="optional G1 render manifest path",
    )
    demo_export.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/public-demo/neodojo-demo.rrd"),
        help="output .rrd artifact path; sibling public-demo files are written next to it",
    )

    render = subparsers.add_parser(
        "render",
        help="write local render evidence artifacts",
    )
    render_subparsers = render.add_subparsers(dest="render_command", required=True)
    render_g1 = render_subparsers.add_parser(
        "g1",
        help="write Unitree G1 render evidence from a model descriptor and visual track",
    )
    render_g1.add_argument(
        "--model-descriptor",
        type=Path,
        required=True,
        help="Unitree G1 robot-model descriptor manifest",
    )
    render_g1.add_argument(
        "--g1-track",
        type=Path,
        required=True,
        help="G1 visual-track root directory or manifest path",
    )
    render_g1.add_argument(
        "--allow-fixture-model",
        action="store_true",
        help="allow fixture model descriptors for CI/demo smoke paths",
    )
    render_g1.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/g1-render"),
        help="output directory for G1 render evidence",
    )

    real_conversion = subparsers.add_parser(
        "real-conversion",
        help="prepare metadata for the later real GVHMR conversion gate",
    )
    real_subparsers = real_conversion.add_subparsers(dest="real_command", required=True)
    real_prepare = real_subparsers.add_parser(
        "prepare",
        help="write source and trim metadata for a later GPU GVHMR run",
    )
    real_prepare.add_argument(
        "--source-index",
        type=Path,
        default=DEFAULT_SOURCE_INDEX,
        help="CSV source index to select from",
    )
    real_prepare.add_argument(
        "--id",
        default=DEFAULT_SOURCE_ID,
        help="source id in category-item form, for example 03-006",
    )
    real_prepare.add_argument("--local-video", type=Path, help="local/user-supplied source clip path")
    real_prepare.add_argument(
        "--start",
        type=float,
        default=0.0,
        help="trim start in seconds",
    )
    real_prepare.add_argument(
        "--end",
        type=float,
        default=12.0,
        help="trim end in seconds",
    )
    real_prepare.add_argument(
        "--rights-notes",
        default="licensing unconfirmed; use local/user-supplied source before GPU run",
        help="licensing or source-rights note to preserve in the prep manifest",
    )
    real_prepare.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/real-conversion-gate"),
        help="output directory for the real conversion prep manifest",
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
            if args.from_gvhmr_json:
                result = write_gvhmr_json_motion_contract(args.out, args.from_gvhmr_json)
            else:
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
                reference_video=args.reference_video,
                reference_trim_start_seconds=args.reference_trim_start,
            )
            print(f"wrote {result.html_path}")
            print(f"wrote {result.manifest_path}")
            return 0

        if args.command == "demo" and args.demo_command == "export-rerun":
            result = write_public_demo(
                playback_manifest_path=args.playback,
                recording_path=args.out,
                g1_render_manifest_path=args.g1_render,
            )
            print(f"wrote {result.html_path}")
            print(f"wrote {result.manifest_path}")
            print(f"wrote {result.scene_path}")
            print(f"wrote {result.recording_path}")
            print(f"wrote {result.screenshot_path}")
            return 0

        if args.command == "render" and args.render_command == "g1":
            result = write_g1_render(
                args.out,
                model_descriptor_path=args.model_descriptor,
                g1_track=args.g1_track,
                allow_fixture_model=args.allow_fixture_model,
            )
            print(f"wrote {result.html_path}")
            print(f"wrote {result.manifest_path}")
            for path in result.frame_paths.values():
                print(f"wrote {path}")
            return 0

        if args.command == "real-conversion" and args.real_command == "prepare":
            result = write_real_conversion_prep(
                args.out,
                source_index=args.source_index,
                source_id=args.id,
                local_video=args.local_video,
                start_seconds=args.start,
                end_seconds=args.end,
                rights_notes=args.rights_notes,
            )
            print(f"wrote {result.manifest_path}")
            return 0
    except ValueError as exc:
        parser.error(str(exc))

    parser.error(f"unknown command: {args.command}")
    return 2
