from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .annotations import write_detected_annotations
from .demo_html import write_demo
from .g1_visual import (
    build_g1_visual_track,
    import_gmr_json_track,
    register_g1_model,
    write_fixture_g1_model_descriptor,
)
from .gmr_native import normalize_gmr_pickle
from .g1_render import write_g1_render
from .motion_contract import write_fixture_motion_contract, write_gvhmr_json_motion_contract
from .public_demo import smoke_check_public_demo, write_public_demo
from .quality import check_quality_surface
from .real_conversion import (
    DEFAULT_SOURCE_ID,
    DEFAULT_SOURCE_INDEX,
    materialize_real_conversion_source,
    validate_gvhmr_source,
    write_real_conversion_prep,
)
from .smplx_surface import write_smplx_surface_proxy
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

    annotations = subparsers.add_parser(
        "annotations",
        help="create annotation manifests from motion artifacts",
    )
    annotation_subparsers = annotations.add_subparsers(dest="annotation_command", required=True)
    annotation_detect = annotation_subparsers.add_parser(
        "detect",
        help="write deterministic SMPL-X key-frame annotations from a motion record",
    )
    annotation_detect.add_argument(
        "--motion-record",
        type=Path,
        required=True,
        help="motion-record root directory or manifest path",
    )
    annotation_detect.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/annotations"),
        help="output directory for the annotation manifest",
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

    smplx_surface = subparsers.add_parser(
        "smplx-surface",
        help="create optional SMPL-X visual surface layers",
    )
    surface_subparsers = smplx_surface.add_subparsers(dest="surface_command", required=True)
    surface_proxy = surface_subparsers.add_parser(
        "proxy",
        help="write a dependency-light SMPL-X capsule surface proxy from teaching joints",
    )
    surface_proxy.add_argument(
        "--motion-record",
        type=Path,
        required=True,
        help="motion-record root directory or manifest path",
    )
    surface_proxy.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/smplx-surface"),
        help="output directory for the SMPL-X surface proxy manifest",
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
    tracks_import = tracks_subparsers.add_parser(
        "import-gmr-json",
        help="import an external GMR Unitree G1 JSON export into the visual-track contract",
    )
    tracks_import.add_argument(
        "--source",
        type=Path,
        required=True,
        help="external neodojo.gmr_unitree_g1_track.v1 JSON export",
    )
    tracks_import.add_argument(
        "--motion-record",
        type=Path,
        help="optional source motion-record root directory or manifest path for frame/timing validation",
    )
    tracks_import.add_argument(
        "--model-descriptor",
        type=Path,
        help="optional Unitree G1 model descriptor manifest",
    )
    tracks_import.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/g1-visual"),
        help="output directory for the imported G1 visual-track manifest and report",
    )
    tracks_normalize_pkl = tracks_subparsers.add_parser(
        "normalize-gmr-pkl",
        help="normalize a native GMR robot-motion pickle into the imported-GMR JSON contract",
    )
    tracks_normalize_pkl.add_argument(
        "--source",
        type=Path,
        required=True,
        help="native GMR robot-motion pickle written by scripts/*_to_robot.py --save_path",
    )
    tracks_normalize_pkl.add_argument(
        "--motion-record",
        type=Path,
        required=True,
        help="source motion-record root directory or manifest path for display joints and timing validation",
    )
    tracks_normalize_pkl.add_argument("--robot", choices=["unitree_g1"], default="unitree_g1")
    tracks_normalize_pkl.add_argument(
        "--joint-names",
        help="optional comma-separated joint names when the pickle does not embed them and is not Unitree G1 29-DOF",
    )
    tracks_normalize_pkl.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/gmr-native"),
        help="output directory for normalized GMR JSON and adapter report",
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
    demo_play.add_argument("--smplx-surface", type=Path, help="optional SMPL-X surface proxy manifest")
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
    demo_smoke = demo_subparsers.add_parser(
        "smoke",
        help="validate generated public demo artifacts for CI",
    )
    demo_smoke.add_argument(
        "--public-demo",
        type=Path,
        default=Path("outputs/public-demo"),
        help="public-demo directory or manifest path",
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

    quality = subparsers.add_parser(
        "quality",
        help="run project-owned static quality checks",
    )
    quality_subparsers = quality.add_subparsers(dest="quality_command", required=True)
    quality_check = quality_subparsers.add_parser(
        "check",
        help="validate MVP planning links and plan scaffolding",
    )
    quality_check.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="repository root containing docs/plans",
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
    real_materialize = real_subparsers.add_parser(
        "materialize-source",
        help="trim a local source clip and extract reference frames for a later GPU GVHMR run",
    )
    real_materialize.add_argument(
        "--prep",
        type=Path,
        default=Path("outputs/real-conversion-gate/real-conversion-prep.json"),
        help="real-conversion prep manifest path or directory",
    )
    real_materialize.add_argument(
        "--local-video",
        type=Path,
        help="local/user-supplied source clip path; overrides the prep manifest local file",
    )
    real_materialize.add_argument(
        "--frame-rate",
        type=float,
        default=1.0,
        help="reference frame extraction rate in frames per second",
    )
    real_materialize.add_argument(
        "--dry-run",
        action="store_true",
        help="write the handoff manifest and ffmpeg commands without processing media",
    )
    real_materialize.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/real-conversion-source"),
        help="output directory for trimmed source and frame-reference artifacts",
    )
    real_validate = real_subparsers.add_parser(
        "validate-source",
        help="validate a GVHMR SMPL-X export against the materialized source handoff",
    )
    real_validate.add_argument(
        "--source-materialization",
        type=Path,
        required=True,
        help="source-materialization.json from real-conversion materialize-source",
    )
    real_validate.add_argument(
        "--gvhmr-json",
        type=Path,
        required=True,
        help="external neodojo.gvhmr_smplx_joints.v1 JSON export",
    )
    real_validate.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/real-conversion-validation"),
        help="output directory for source validation report and validated export copy",
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

        if args.command == "annotations" and args.annotation_command == "detect":
            result = write_detected_annotations(args.out, args.motion_record)
            print(f"wrote {result.manifest_path}")
            print(f"wrote {result.feedback_report_path}")
            return 0

        if args.command == "smplx-surface" and args.surface_command == "proxy":
            result = write_smplx_surface_proxy(args.out, args.motion_record)
            print(f"wrote {result.manifest_path}")
            print(f"wrote {result.data_path}")
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

        if args.command == "tracks" and args.tracks_command == "import-gmr-json":
            result = import_gmr_json_track(
                args.out,
                args.source,
                motion_record=args.motion_record,
                model_descriptor_path=args.model_descriptor,
            )
            print(f"wrote {result.track_manifest_path}")
            print(f"wrote {result.comparison_report_path}")
            return 0

        if args.command == "tracks" and args.tracks_command == "normalize-gmr-pkl":
            joint_names = None
            if args.joint_names:
                joint_names = [name.strip() for name in args.joint_names.split(",") if name.strip()]
            result = normalize_gmr_pickle(
                args.out,
                args.source,
                motion_record=args.motion_record,
                robot=args.robot,
                joint_names=joint_names,
            )
            print(f"wrote {result.normalized_export_path}")
            print(f"wrote {result.report_path}")
            return 0

        if args.command == "demo" and args.demo_command == "play":
            result = write_teaching_playback_demo(
                args.out,
                motion_record=args.motion_record,
                g1_track=args.g1_track,
                annotations_path=args.annotations,
                smplx_surface=args.smplx_surface,
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

        if args.command == "demo" and args.demo_command == "smoke":
            result = smoke_check_public_demo(args.public_demo)
            print(f"validated {result.manifest_path}")
            for path in result.checked_paths:
                print(f"validated {path}")
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

        if args.command == "quality" and args.quality_command == "check":
            result = check_quality_surface(args.repo_root)
            print(f"checked {result.checked_plan_count} MVP plan files")
            print(f"checked {len(result.checked_links)} MVP index links")
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

        if args.command == "real-conversion" and args.real_command == "materialize-source":
            result = materialize_real_conversion_source(
                args.out,
                prep_manifest=args.prep,
                local_video=args.local_video,
                frame_rate=args.frame_rate,
                dry_run=args.dry_run,
            )
            print(f"wrote {result.manifest_path}")
            print(f"prepared {result.trimmed_video_path}")
            print(f"prepared {result.frames_dir}")
            return 0

        if args.command == "real-conversion" and args.real_command == "validate-source":
            result = validate_gvhmr_source(
                args.out,
                source_materialization=args.source_materialization,
                gvhmr_json=args.gvhmr_json,
            )
            print(f"wrote {result.report_path}")
            if result.validated_export_path is not None:
                print(f"wrote {result.validated_export_path}")
            if result.status != "validated":
                raise ValueError(f"GVHMR source validation status is {result.status}; see {result.report_path}")
            return 0
    except ValueError as exc:
        parser.error(str(exc))

    parser.error(f"unknown command: {args.command}")
    return 2
