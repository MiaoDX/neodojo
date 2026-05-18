from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .annotations import write_detected_annotations
from .browser_capture import write_public_demo_browser_capture
from .capture_bundle import write_capture_bundle
from .demo_html import write_demo
from .g1_visual import (
    build_g1_visual_track,
    import_gmr_json_track,
    register_g1_model,
    write_fixture_g1_model_descriptor,
)
from .gmr_native import normalize_gmr_pickle
from .g1_render import write_g1_mujoco_render, write_g1_render
from .motion_contract import write_fixture_motion_contract, write_gvhmr_json_motion_contract
from .public_demo import smoke_check_public_demo, write_public_demo
from .quality import check_quality_surface
from .recorder_capture import write_simulator_recorder_capture
from .real_conversion import (
    DEFAULT_SOURCE_ID,
    DEFAULT_SOURCE_INDEX,
    archive_gvhmr_operator_package,
    audit_real_conversion_completion,
    inspect_gvhmr_result,
    materialize_real_conversion_source,
    package_gvhmr_gpu_handoff,
    package_gvhmr_gpu_input_archive,
    package_gvhmr_gpu_input_bundle,
    probe_gpu_execution_environment,
    validate_gvhmr_operator_package_archive,
    validate_gvhmr_operator_package,
    validate_gvhmr_source,
    write_gvhmr_colab_operator_notebook,
    write_gvhmr_gpu_run_request,
    write_gvhmr_operator_package,
    write_real_gvhmr_artifact_acquisition_status,
    write_real_artifact_intake_smoke_input,
    write_real_conversion_prep,
)
from .real_demo import write_real_conversion_demo
from .real_demo_promotion import validate_real_demo_pages_promotion
from .smplx_surface import (
    register_smplx_asset_descriptor,
    write_smplx_mesh_surface,
    write_smplx_surface_proxy,
)
from .teaching_playback import write_teaching_playback_demo
from .viser_runtime import serve_viser_runtime, write_viser_runtime_contract


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
    surface_register = surface_subparsers.add_parser(
        "register-assets",
        help="write a local-only descriptor for licensed SMPL-X model assets",
    )
    surface_register.add_argument(
        "--model",
        type=Path,
        required=True,
        help="local licensed SMPL-X model file path; the file is not copied",
    )
    surface_register.add_argument(
        "--license",
        dest="license_name",
        required=True,
        help="license/provenance note for the local SMPL-X asset",
    )
    surface_register.add_argument("--source-url", help="upstream asset source URL")
    surface_register.add_argument("--source-revision", help="upstream version, release, or checksum note")
    surface_register.add_argument("--variant", help="SMPL-X model variant notes")
    surface_register.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/smplx-assets"),
        help="output directory for the local-only SMPL-X asset descriptor",
    )
    surface_mesh = surface_subparsers.add_parser(
        "mesh",
        help="import local licensed SMPL-X mesh-frame evidence into the surface contract",
    )
    surface_mesh.add_argument(
        "--motion-record",
        type=Path,
        required=True,
        help="motion-record root directory or manifest path",
    )
    surface_mesh.add_argument(
        "--asset-descriptor",
        type=Path,
        required=True,
        help="local-only SMPL-X asset descriptor manifest or root directory",
    )
    surface_mesh.add_argument(
        "--mesh-frames",
        type=Path,
        required=True,
        help="local neodojo.smplx_mesh_frames.v1 JSON from an external licensed SMPL-X renderer",
    )
    surface_mesh.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/smplx-mesh"),
        help="output directory for local-only SMPL-X mesh surface artifacts",
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
    demo_play.add_argument("--smplx-surface", type=Path, help="optional SMPL-X surface proxy or mesh manifest")
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
    demo_export.add_argument(
        "--use-rerun-sdk",
        action="store_true",
        help="write a true Rerun SDK .rrd instead of the JSON fallback artifact",
    )
    demo_viser = demo_subparsers.add_parser(
        "serve-viser",
        help="start an optional local Viser teaching runtime from playback artifacts",
    )
    demo_viser.add_argument(
        "--playback",
        type=Path,
        required=True,
        help="teaching playback manifest path",
    )
    demo_viser.add_argument(
        "--g1-render",
        type=Path,
        help="optional G1 render manifest path",
    )
    demo_viser.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/viser-runtime"),
        help="output directory for the Viser runtime manifest and scene contract",
    )
    demo_viser.add_argument("--host", default="127.0.0.1", help="host for the local Viser server")
    demo_viser.add_argument("--port", type=int, default=8080, help="port for the local Viser server")
    demo_viser.add_argument(
        "--write-contract-only",
        action="store_true",
        help="write the Viser runtime contract without importing or starting Viser",
    )
    demo_viser.add_argument(
        "--smoke-start",
        action="store_true",
        help="start Viser, populate the scene, then stop immediately for local smoke tests",
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
    demo_browser = demo_subparsers.add_parser(
        "browser-smoke",
        help="render the public demo in headless Chromium and capture a screenshot",
    )
    demo_browser.add_argument(
        "--public-demo",
        type=Path,
        default=Path("outputs/public-demo"),
        help="public-demo directory or manifest path",
    )
    demo_browser.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/browser-capture"),
        help="output directory for browser screenshot evidence",
    )
    demo_browser.add_argument("--width", type=int, default=1280, help="browser viewport width")
    demo_browser.add_argument("--height", type=int, default=720, help="browser viewport height")
    demo_browser.add_argument(
        "--timeout-ms",
        type=int,
        default=10_000,
        help="browser navigation and assertion timeout in milliseconds",
    )

    capture = subparsers.add_parser(
        "capture",
        help="build generated multi-camera evidence bundle manifests",
    )
    capture_subparsers = capture.add_subparsers(dest="capture_command", required=True)
    capture_bundle = capture_subparsers.add_parser(
        "bundle",
        help="write a roboharness-style capture evidence bundle from generated artifacts",
    )
    capture_bundle.add_argument(
        "--public-demo",
        type=Path,
        default=Path("outputs/public-demo"),
        help="public-demo directory or manifest path",
    )
    capture_bundle.add_argument(
        "--viser-runtime",
        type=Path,
        default=Path("outputs/viser-runtime"),
        help="Viser runtime directory or viser-runtime.json path",
    )
    capture_bundle.add_argument(
        "--g1-render",
        type=Path,
        default=Path("outputs/g1-render"),
        help="G1 render evidence directory or manifest path",
    )
    capture_bundle.add_argument(
        "--browser-capture",
        type=Path,
        help="optional browser-capture directory or manifest from `neodojo demo browser-smoke`",
    )
    capture_bundle.add_argument(
        "--recorder-capture",
        type=Path,
        help="optional recorder-capture directory or manifest from `neodojo capture recorder`",
    )
    capture_bundle.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/capture"),
        help="output directory for the capture bundle manifest",
    )
    capture_recorder = capture_subparsers.add_parser(
        "recorder",
        help="write a direct simulator recorder manifest from MuJoCo offscreen render evidence",
    )
    capture_recorder.add_argument(
        "--simulator-render",
        type=Path,
        default=Path("outputs/g1-mujoco-render"),
        help="MuJoCo render evidence directory or manifest path",
    )
    capture_recorder.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/recorder-capture"),
        help="output directory for the recorder-capture manifest",
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
    render_mujoco_g1 = render_subparsers.add_parser(
        "mujoco-g1",
        help="write MuJoCo offscreen mesh render evidence from a registered G1 descriptor",
    )
    render_mujoco_g1.add_argument(
        "--model-descriptor",
        type=Path,
        required=True,
        help="Unitree G1 robot-model descriptor manifest",
    )
    render_mujoco_g1.add_argument(
        "--g1-track",
        type=Path,
        required=True,
        help="G1 visual-track root directory or manifest path",
    )
    render_mujoco_g1.add_argument(
        "--allow-fixture-model",
        action="store_true",
        help="accepted for CLI symmetry, but MuJoCo rendering still requires registered assets",
    )
    render_mujoco_g1.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/g1-mujoco-render"),
        help="output directory for MuJoCo render evidence",
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
        "--local-source-id",
        help="custom source id for a local/user-supplied clip; bypasses --source-index lookup",
    )
    real_prepare.add_argument(
        "--local-title",
        help="English/display title for --local-source-id; defaults to the local video filename",
    )
    real_prepare.add_argument(
        "--local-title-chinese",
        help="Chinese/source title for --local-source-id; defaults to --local-title",
    )
    real_prepare.add_argument(
        "--local-category",
        default="local_user_supplied",
        help="category slug for --local-source-id",
    )
    real_prepare.add_argument(
        "--local-category-chinese",
        default="local/user-supplied",
        help="category label for --local-source-id",
    )
    real_prepare.add_argument(
        "--local-origin-url",
        help="optional stable origin URL for --local-source-id provenance",
    )
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
    real_gpu_handoff = real_subparsers.add_parser(
        "package-gpu-handoff",
        help="write a metadata bundle for running GVHMR on an external GPU machine",
    )
    real_gpu_handoff.add_argument(
        "--source-materialization",
        type=Path,
        required=True,
        help="source-materialization.json from real-conversion materialize-source",
    )
    real_gpu_handoff.add_argument(
        "--expected-export-json",
        type=Path,
        help="expected returned neodojo.gvhmr_smplx_joints.v1 export path",
    )
    real_gpu_handoff.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/gvhmr-gpu-handoff"),
        help="output directory for the GPU handoff manifest and README",
    )
    real_gpu_input = real_subparsers.add_parser(
        "package-gpu-input",
        help="write a copyable GPU input bundle from a GPU handoff, optionally including media",
    )
    real_gpu_input.add_argument(
        "--gpu-handoff",
        type=Path,
        required=True,
        help="GVHMR GPU handoff manifest path or directory",
    )
    real_gpu_input.add_argument(
        "--include-media",
        action="store_true",
        help="copy the materialized trimmed clip into the ignored bundle for transfer",
    )
    real_gpu_input.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/gvhmr-gpu-input"),
        help="output directory for the copyable GPU input bundle",
    )
    real_gpu_archive = real_subparsers.add_parser(
        "archive-gpu-input",
        help="write a tar.gz archive from a GPU input bundle for transfer",
    )
    real_gpu_archive.add_argument(
        "--gpu-input",
        type=Path,
        required=True,
        help="GVHMR GPU input bundle manifest path or directory",
    )
    real_gpu_archive.add_argument(
        "--archive-name",
        default="neodojo-gvhmr-gpu-input.tar.gz",
        help="archive filename ending in .tar.gz or .tgz",
    )
    real_gpu_archive.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/gvhmr-gpu-input-archive"),
        help="output directory for the transfer archive and archive manifest",
    )
    real_gpu_probe = real_subparsers.add_parser(
        "probe-gpu-execution",
        help="write a safe local/provider GPU execution readiness probe without running GVHMR",
    )
    real_gpu_probe.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/gvhmr-gpu-execution-probe"),
        help="output directory for the GPU execution probe manifest",
    )
    real_gpu_probe.add_argument(
        "--github-repo",
        help="optional OWNER/REPO to probe for self-hosted GitHub GPU runners via gh",
    )
    real_gpu_request = real_subparsers.add_parser(
        "write-gpu-run-request",
        help="write a concise external-GPU operator request from a GPU input archive manifest",
    )
    real_gpu_request.add_argument(
        "--gpu-input-archive",
        type=Path,
        required=True,
        help="GVHMR GPU input archive manifest path or directory",
    )
    real_gpu_request.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/gvhmr-gpu-run-request"),
        help="output directory for the GPU run request manifest and README",
    )
    real_colab_notebook = real_subparsers.add_parser(
        "write-colab-notebook",
        help="write a Colab operator notebook from a GPU run request manifest",
    )
    real_colab_notebook.add_argument(
        "--gpu-run-request",
        type=Path,
        required=True,
        help="GVHMR GPU run request manifest path or directory",
    )
    real_colab_notebook.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/gvhmr-colab-operator"),
        help="output directory for the Colab operator notebook and manifest",
    )
    real_operator_package = real_subparsers.add_parser(
        "package-operator",
        help="collocate a GPU archive, run request, and Colab notebook for an external operator",
    )
    real_operator_package.add_argument(
        "--gpu-input-archive",
        type=Path,
        required=True,
        help="GVHMR GPU input archive manifest path or directory",
    )
    real_operator_package.add_argument(
        "--gpu-run-request",
        type=Path,
        required=True,
        help="GVHMR GPU run request manifest path or directory",
    )
    real_operator_package.add_argument(
        "--colab-notebook",
        type=Path,
        required=True,
        help="GVHMR Colab operator notebook manifest path or directory",
    )
    real_operator_package.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/gvhmr-operator-package"),
        help="output directory for the collocated operator package",
    )
    real_operator_validate = real_subparsers.add_parser(
        "validate-operator-package",
        help="validate a collocated GVHMR operator package before external GPU transfer",
    )
    real_operator_validate.add_argument(
        "--package",
        type=Path,
        required=True,
        help="GVHMR operator package directory or manifest.json",
    )
    real_operator_archive = real_subparsers.add_parser(
        "archive-operator-package",
        help="archive a validated GVHMR operator package directory as one transfer file",
    )
    real_operator_archive.add_argument(
        "--package",
        type=Path,
        required=True,
        help="GVHMR operator package directory or manifest.json",
    )
    real_operator_archive.add_argument(
        "--archive-name",
        default="neodojo-gvhmr-operator-package.tar.gz",
        help="archive filename ending in .tar.gz or .tgz",
    )
    real_operator_archive.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/gvhmr-operator-package-archive"),
        help="output directory for the package archive and manifest",
    )
    real_operator_archive_validate = real_subparsers.add_parser(
        "validate-operator-package-archive",
        help="validate a GVHMR operator package archive and its nested package checksums",
    )
    real_operator_archive_validate.add_argument(
        "--archive",
        type=Path,
        required=True,
        help="GVHMR operator package archive directory, manifest.json, or tar.gz with sibling manifest.json",
    )
    real_artifact_acquisition_status = real_subparsers.add_parser(
        "artifact-acquisition-status",
        help="write a non-failing status manifest for the external GVHMR artifact handoff",
    )
    real_artifact_acquisition_status.add_argument(
        "--operator-package-archive",
        type=Path,
        default=Path("outputs/gvhmr-operator-package-archive"),
        help="GVHMR operator package archive directory, manifest.json, or tar.gz",
    )
    real_artifact_acquisition_status.add_argument(
        "--source-materialization",
        type=Path,
        default=Path("outputs/real-conversion-source/source-materialization.json"),
        help="source-materialization.json expected to match the returned GVHMR export",
    )
    real_artifact_acquisition_status.add_argument(
        "--gvhmr-json",
        type=Path,
        default=Path("outputs/real-conversion-gate/gvhmr-smplx-joints.json"),
        help="returned neodojo.gvhmr_smplx_joints.v1 JSON export to audit",
    )
    real_artifact_acquisition_status.add_argument(
        "--real-demo",
        type=Path,
        default=Path("outputs/real-demo"),
        help="real-demo output directory or manifest to verify",
    )
    real_artifact_acquisition_status.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/real-gvhmr-artifact-acquisition-status"),
        help="output directory for the acquisition status manifest",
    )
    real_artifact_acquisition_status.add_argument(
        "--github-repo",
        help="optional OWNER/REPO to probe for self-hosted GitHub GPU runners via gh",
    )
    real_intake_smoke = real_subparsers.add_parser(
        "write-intake-smoke-input",
        help="write fixture-only inputs for smoke-testing returned-artifact intake",
    )
    real_intake_smoke.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/real-artifact-intake-smoke-input"),
        help="output directory for fixture-only source materialization and GVHMR JSON inputs",
    )
    real_intake_smoke.add_argument(
        "--frames",
        type=int,
        default=36,
        help="number of synthetic SMPL-X frames to write",
    )
    real_audit = real_subparsers.add_parser(
        "audit-completion",
        help="write a non-failing audit of whether the real GVHMR conversion gate is complete",
    )
    real_audit.add_argument(
        "--source-materialization",
        type=Path,
        default=Path("outputs/real-conversion-source/source-materialization.json"),
        help="source-materialization.json expected to match the returned GVHMR export",
    )
    real_audit.add_argument(
        "--gvhmr-json",
        type=Path,
        default=Path("outputs/real-conversion-gate/gvhmr-smplx-joints.json"),
        help="returned neodojo.gvhmr_smplx_joints.v1 JSON export to audit",
    )
    real_audit.add_argument(
        "--real-demo",
        type=Path,
        default=Path("outputs/real-demo"),
        help="real-demo output directory or manifest to verify",
    )
    real_audit.add_argument(
        "--require-complete",
        action="store_true",
        help="exit with an error unless the audit proves a real non-fixture demo exists",
    )
    real_audit.add_argument(
        "--github-repo",
        help="optional OWNER/REPO to include self-hosted GitHub GPU runner evidence via gh",
    )
    real_audit.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/real-conversion-audit"),
        help="output directory for the audit manifest",
    )
    real_pages_promotion = real_subparsers.add_parser(
        "validate-pages-promotion",
        help="validate and stage a downloaded real-demo artifact for guarded Pages promotion",
    )
    real_pages_promotion.add_argument(
        "--download-root",
        type=Path,
        required=True,
        help="downloaded neodojo-self-hosted-real-demo artifact directory",
    )
    real_pages_promotion.add_argument(
        "--source-run-id",
        required=True,
        help="GitHub Actions run ID that produced the downloaded artifact",
    )
    real_pages_promotion.add_argument(
        "--artifact-name",
        default="neodojo-self-hosted-real-demo",
        help="downloaded artifact name",
    )
    real_pages_promotion.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/promoted-real-demo-pages"),
        help="staged public-demo directory for Pages upload",
    )
    real_inspect_gvhmr = real_subparsers.add_parser(
        "inspect-gvhmr-result",
        help="inspect a returned GVHMR hmr4d_results.pt or JSON summary for export readiness",
    )
    real_inspect_gvhmr.add_argument(
        "--source",
        type=Path,
        required=True,
        help="GVHMR hmr4d_results.pt, or a JSON summary/export with the same top-level shape",
    )
    real_inspect_gvhmr.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/gvhmr-result-inspection"),
        help="output directory for the result inspection manifest",
    )
    real_import_demo = real_subparsers.add_parser(
        "import-demo",
        help="validate an external GVHMR export and regenerate the local demo lane",
    )
    real_import_demo.add_argument(
        "--source-materialization",
        type=Path,
        required=True,
        help="source-materialization.json from real-conversion materialize-source",
    )
    real_import_demo.add_argument(
        "--gvhmr-json",
        type=Path,
        required=True,
        help="external neodojo.gvhmr_smplx_joints.v1 JSON export",
    )
    real_import_demo.add_argument(
        "--g1-track",
        type=Path,
        help="optional existing G1 visual-track manifest; otherwise a derived fixture G1 visual track is generated",
    )
    real_import_demo.add_argument(
        "--model-descriptor",
        type=Path,
        help="optional existing Unitree G1 model descriptor for G1 visual rendering",
    )
    real_import_demo.add_argument(
        "--use-rerun-sdk",
        action="store_true",
        help="write a true Rerun SDK .rrd instead of the JSON fallback artifact",
    )
    real_import_demo.add_argument(
        "--out",
        type=Path,
        default=Path("outputs/real-demo"),
        help="output directory for the validated real-artifact demo lane",
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

        if args.command == "smplx-surface" and args.surface_command == "register-assets":
            result = register_smplx_asset_descriptor(
                args.out,
                model_path=args.model,
                license_name=args.license_name,
                source_url=args.source_url,
                source_revision=args.source_revision,
                variant=args.variant,
            )
            print(f"wrote {result.descriptor_path}")
            return 0

        if args.command == "smplx-surface" and args.surface_command == "mesh":
            result = write_smplx_mesh_surface(
                args.out,
                motion_record=args.motion_record,
                asset_descriptor=args.asset_descriptor,
                mesh_frames=args.mesh_frames,
            )
            print(f"wrote {result.manifest_path}")
            print(f"wrote {result.data_path}")
            print(f"wrote {result.validation_path}")
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
                use_rerun_sdk=args.use_rerun_sdk,
            )
            print(f"wrote {result.html_path}")
            print(f"wrote {result.manifest_path}")
            print(f"wrote {result.scene_path}")
            print(f"wrote {result.recording_path}")
            print(f"wrote {result.screenshot_path}")
            return 0

        if args.command == "demo" and args.demo_command == "serve-viser":
            if args.write_contract_only:
                result = write_viser_runtime_contract(
                    args.out,
                    playback_manifest_path=args.playback,
                    g1_render_manifest_path=args.g1_render,
                )
                print(f"wrote {result.manifest_path}")
                print(f"wrote {result.scene_path}")
                for path in result.screenshot_paths.values():
                    print(f"wrote {path}")
                return 0
            result = serve_viser_runtime(
                playback_manifest_path=args.playback,
                g1_render_manifest_path=args.g1_render,
                out_dir=args.out,
                host=args.host,
                port=args.port,
                stop_after_start=args.smoke_start,
            )
            print(f"wrote {result.manifest_path}")
            print(f"wrote {result.scene_path}")
            for path in result.screenshot_paths.values():
                print(f"wrote {path}")
            print(f"serving {result.url}")
            return 0

        if args.command == "demo" and args.demo_command == "smoke":
            result = smoke_check_public_demo(args.public_demo)
            print(f"validated {result.manifest_path}")
            for path in result.checked_paths:
                print(f"validated {path}")
            return 0

        if args.command == "demo" and args.demo_command == "browser-smoke":
            result = write_public_demo_browser_capture(
                public_demo=args.public_demo,
                out_dir=args.out,
                width=args.width,
                height=args.height,
                timeout_ms=args.timeout_ms,
            )
            print(f"wrote {result.manifest_path}")
            print(f"wrote {result.screenshot_path}")
            print(f"captured {result.url}")
            return 0

        if args.command == "capture" and args.capture_command == "bundle":
            result = write_capture_bundle(
                args.out,
                public_demo=args.public_demo,
                viser_runtime=args.viser_runtime,
                g1_render=args.g1_render,
                browser_capture=args.browser_capture,
                recorder_capture=args.recorder_capture,
            )
            print(f"wrote {result.manifest_path}")
            for path in result.checked_paths:
                print(f"validated {path}")
            return 0

        if args.command == "capture" and args.capture_command == "recorder":
            result = write_simulator_recorder_capture(
                args.out,
                simulator_render=args.simulator_render,
            )
            print(f"wrote {result.manifest_path}")
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

        if args.command == "render" and args.render_command == "mujoco-g1":
            result = write_g1_mujoco_render(
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
                local_source_id=args.local_source_id,
                local_title_english=args.local_title,
                local_title_chinese=args.local_title_chinese,
                local_category=args.local_category,
                local_category_chinese=args.local_category_chinese,
                local_origin_url=args.local_origin_url,
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

        if args.command == "real-conversion" and args.real_command == "package-gpu-input":
            result = package_gvhmr_gpu_input_bundle(
                args.out,
                gpu_handoff=args.gpu_handoff,
                include_media=args.include_media,
            )
            print(f"wrote {result.manifest_path}")
            print(f"wrote {result.runbook_path}")
            print(f"status {result.status}")
            for path in result.checked_paths:
                print(f"checked {path}")
            return 0

        if args.command == "real-conversion" and args.real_command == "archive-gpu-input":
            result = package_gvhmr_gpu_input_archive(
                args.out,
                gpu_input=args.gpu_input,
                archive_name=args.archive_name,
            )
            print(f"wrote {result.manifest_path}")
            print(f"wrote {result.archive_path}")
            print(f"status {result.status}")
            for path in result.checked_paths:
                print(f"checked {path}")
            return 0

        if args.command == "real-conversion" and args.real_command == "probe-gpu-execution":
            result = probe_gpu_execution_environment(args.out, github_repo=args.github_repo)
            print(f"wrote {result.manifest_path}")
            print(f"status {result.status}")
            return 0

        if args.command == "real-conversion" and args.real_command == "write-gpu-run-request":
            result = write_gvhmr_gpu_run_request(
                args.out,
                gpu_input_archive=args.gpu_input_archive,
            )
            print(f"wrote {result.manifest_path}")
            print(f"wrote {result.readme_path}")
            print(f"status {result.status}")
            for path in result.checked_paths:
                print(f"checked {path}")
            return 0

        if args.command == "real-conversion" and args.real_command == "write-colab-notebook":
            result = write_gvhmr_colab_operator_notebook(
                args.out,
                gpu_run_request=args.gpu_run_request,
            )
            print(f"wrote {result.manifest_path}")
            print(f"wrote {result.notebook_path}")
            print(f"status {result.status}")
            for path in result.checked_paths:
                print(f"checked {path}")
            return 0

        if args.command == "real-conversion" and args.real_command == "package-operator":
            result = write_gvhmr_operator_package(
                args.out,
                gpu_input_archive=args.gpu_input_archive,
                gpu_run_request=args.gpu_run_request,
                colab_notebook=args.colab_notebook,
            )
            print(f"wrote {result.manifest_path}")
            print(f"wrote {result.readme_path}")
            print(f"status {result.status}")
            for path in result.checked_paths:
                print(f"checked {path}")
            return 0

        if args.command == "real-conversion" and args.real_command == "validate-operator-package":
            result = validate_gvhmr_operator_package(args.package)
            print(f"validated {result.manifest_path}")
            print(f"status {result.status}")
            for path in result.checked_paths:
                print(f"checked {path}")
            return 0

        if args.command == "real-conversion" and args.real_command == "archive-operator-package":
            result = archive_gvhmr_operator_package(
                args.out,
                operator_package=args.package,
                archive_name=args.archive_name,
            )
            print(f"wrote {result.manifest_path}")
            print(f"wrote {result.archive_path}")
            print(f"status {result.status}")
            for path in result.checked_paths:
                print(f"checked {path}")
            return 0

        if args.command == "real-conversion" and args.real_command == "validate-operator-package-archive":
            result = validate_gvhmr_operator_package_archive(args.archive)
            print(f"validated {result.manifest_path}")
            print(f"validated {result.archive_path}")
            print(f"status {result.status}")
            for path in result.checked_paths:
                print(f"checked {path}")
            return 0

        if args.command == "real-conversion" and args.real_command == "artifact-acquisition-status":
            result = write_real_gvhmr_artifact_acquisition_status(
                args.out,
                operator_package_archive=args.operator_package_archive,
                source_materialization=args.source_materialization,
                gvhmr_json=args.gvhmr_json,
                real_demo=args.real_demo,
                github_repo=args.github_repo,
            )
            print(f"wrote {result.manifest_path}")
            print(f"status {result.status}")
            print(f"blocked {str(result.blocked).lower()}")
            for path in result.checked_paths:
                print(f"checked {path}")
            return 0

        if args.command == "real-conversion" and args.real_command == "write-intake-smoke-input":
            result = write_real_artifact_intake_smoke_input(args.out, frame_count=args.frames)
            print(f"wrote {result.source_materialization_path}")
            print(f"wrote {result.gvhmr_json_path}")
            return 0

        if args.command == "real-conversion" and args.real_command == "audit-completion":
            result = audit_real_conversion_completion(
                args.out,
                source_materialization=args.source_materialization,
                gvhmr_json=args.gvhmr_json,
                real_demo=args.real_demo,
                github_repo=args.github_repo,
            )
            print(f"wrote {result.manifest_path}")
            print(f"status {result.status}")
            print(f"complete {str(result.complete).lower()}")
            if args.require_complete and not result.complete:
                raise ValueError(f"real conversion gate is not complete; status is {result.status}")
            return 0

        if args.command == "real-conversion" and args.real_command == "validate-pages-promotion":
            result = validate_real_demo_pages_promotion(
                args.download_root,
                args.out,
                source_run_id=args.source_run_id,
                artifact_name=args.artifact_name,
            )
            print(f"wrote {result.manifest_path}")
            print(f"staged {result.staged_dir}")
            for path in result.checked_paths:
                print(f"validated {path}")
            return 0

        if args.command == "real-conversion" and args.real_command == "package-gpu-handoff":
            result = package_gvhmr_gpu_handoff(
                args.out,
                source_materialization=args.source_materialization,
                expected_export_json=args.expected_export_json,
            )
            print(f"wrote {result.manifest_path}")
            print(f"wrote {result.readme_path}")
            print(f"wrote {result.export_template_path}")
            print(f"wrote {result.exporter_script_path}")
            print(f"wrote {result.source_materialization_copy_path}")
            print(f"status {result.status}")
            for path in result.checked_paths:
                print(f"checked {path}")
            return 0

        if args.command == "real-conversion" and args.real_command == "inspect-gvhmr-result":
            result = inspect_gvhmr_result(args.out, source=args.source)
            print(f"wrote {result.manifest_path}")
            print(f"status {result.status}")
            for path in result.checked_paths:
                print(f"checked {path}")
            return 0

        if args.command == "real-conversion" and args.real_command == "import-demo":
            result = write_real_conversion_demo(
                args.out,
                source_materialization=args.source_materialization,
                gvhmr_json=args.gvhmr_json,
                g1_track=args.g1_track,
                model_descriptor=args.model_descriptor,
                use_rerun_sdk=args.use_rerun_sdk,
            )
            print(f"wrote {result.manifest_path}")
            for path in result.checked_paths:
                print(f"validated {path}")
            return 0
    except ValueError as exc:
        parser.error(str(exc))

    parser.error(f"unknown command: {args.command}")
    return 2
