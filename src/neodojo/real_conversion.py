from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .contracts import local_file_metadata, require_schema, sha256_file
from .fixtures import (
    FIXTURE_FORM,
    FIXTURE_FPS,
    FIXTURE_ROUTINE,
    build_smplx_fixture_frames,
)
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
GVHMR_GPU_INPUT_BUNDLE_SCHEMA = "neodojo.gvhmr_gpu_input_bundle.v1"
GVHMR_GPU_INPUT_ARCHIVE_SCHEMA = "neodojo.gvhmr_gpu_input_archive.v1"
GVHMR_GPU_RUN_REQUEST_SCHEMA = "neodojo.gvhmr_gpu_run_request.v1"
GVHMR_COLAB_OPERATOR_NOTEBOOK_SCHEMA = "neodojo.gvhmr_colab_operator_notebook.v1"
GVHMR_OPERATOR_PACKAGE_SCHEMA = "neodojo.gvhmr_operator_package.v1"
GVHMR_OPERATOR_PACKAGE_ARCHIVE_SCHEMA = "neodojo.gvhmr_operator_package_archive.v1"
GVHMR_RESULT_INSPECTION_SCHEMA = "neodojo.gvhmr_result_inspection.v1"
GVHMR_GPU_EXECUTION_PROBE_SCHEMA = "neodojo.gvhmr_gpu_execution_probe.v1"
REAL_CONVERSION_AUDIT_SCHEMA = "neodojo.real_conversion_audit.v1"
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
    exporter_script_path: Path
    runner_script_path: Path
    source_materialization_copy_path: Path
    checked_paths: list[Path]
    status: str


@dataclass(frozen=True)
class GvhmrGpuInputBundleWriteResult:
    manifest_path: Path
    runbook_path: Path
    runner_script_path: Path
    checked_paths: list[Path]
    status: str


@dataclass(frozen=True)
class GvhmrGpuInputArchiveWriteResult:
    manifest_path: Path
    archive_path: Path
    checked_paths: list[Path]
    status: str


@dataclass(frozen=True)
class GvhmrGpuRunRequestWriteResult:
    manifest_path: Path
    readme_path: Path
    checked_paths: list[Path]
    status: str


@dataclass(frozen=True)
class GvhmrColabOperatorNotebookWriteResult:
    manifest_path: Path
    notebook_path: Path
    checked_paths: list[Path]
    status: str


@dataclass(frozen=True)
class GvhmrOperatorPackageWriteResult:
    manifest_path: Path
    readme_path: Path
    checked_paths: list[Path]
    status: str


@dataclass(frozen=True)
class GvhmrOperatorPackageValidationResult:
    manifest_path: Path
    checked_paths: list[Path]
    status: str


@dataclass(frozen=True)
class GvhmrOperatorPackageArchiveWriteResult:
    manifest_path: Path
    archive_path: Path
    checked_paths: list[Path]
    status: str


@dataclass(frozen=True)
class GvhmrOperatorPackageArchiveValidationResult:
    manifest_path: Path
    archive_path: Path
    checked_paths: list[Path]
    status: str


@dataclass(frozen=True)
class GvhmrResultInspectionWriteResult:
    manifest_path: Path
    checked_paths: list[Path]
    status: str


@dataclass(frozen=True)
class GvhmrGpuExecutionProbeWriteResult:
    manifest_path: Path
    status: str


@dataclass(frozen=True)
class RealArtifactIntakeSmokeInputWriteResult:
    source_materialization_path: Path
    gvhmr_json_path: Path


@dataclass(frozen=True)
class RealConversionCompletionAuditWriteResult:
    manifest_path: Path
    status: str
    complete: bool
    checked_paths: list[Path]


def _as_posix(path: Path) -> str:
    return str(path).replace("\\", "/")


_GPU_PROVIDER_ENV_PREFIXES: dict[str, tuple[str, ...]] = {
    "modal": ("MODAL_",),
    "runpod": ("RUNPOD",),
    "huggingface": ("HF_", "HUGGINGFACE"),
    "aws": ("AWS_",),
    "gcp": ("GCP", "GOOGLE"),
    "replicate": ("REPLICATE",),
    "vast": ("VAST",),
    "kaggle": ("KAGGLE",),
}

_GPU_PROVIDER_CLIS: dict[str, tuple[str, ...]] = {
    "modal": ("modal",),
    "runpod": ("runpodctl",),
    "huggingface": ("huggingface-cli",),
    "aws": ("aws",),
    "gcp": ("gcloud",),
    "replicate": ("replicate",),
    "vast": ("vastai",),
    "kaggle": ("kaggle",),
}

_GITHUB_GPU_SECRET_KEYWORDS = (
    "GPU",
    "CUDA",
    "GVHMR",
    "SMPL",
    "RUNPOD",
    "MODAL",
    "HF_",
    "HUGGINGFACE",
    "AWS",
    "GCP",
    "GOOGLE",
    "REPLICATE",
    "VAST",
    "KAGGLE",
)


def _env_keys_for_prefixes(env: Mapping[str, str], prefixes: tuple[str, ...]) -> list[str]:
    return sorted(key for key in env if any(key.startswith(prefix) for prefix in prefixes))


def _command_paths(
    command_lookup: Callable[[str], str | None],
    commands: tuple[str, ...],
) -> dict[str, str | None]:
    return {command: command_lookup(command) for command in commands}


def _probe_docker_gpu_runtime(docker_path: str | None) -> dict[str, Any]:
    if docker_path is None:
        return {"cli_found": False, "gpu_runtime_detected": False, "runtime_names": [], "error": None}
    try:
        completed = subprocess.run(
            [docker_path, "info", "--format", "{{json .Runtimes}}"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"cli_found": True, "gpu_runtime_detected": False, "runtimes": None, "error": str(exc)}
    output = completed.stdout.strip()
    runtimes = None
    if output and output != "null":
        try:
            runtimes = json.loads(output)
        except json.JSONDecodeError:
            runtimes = output
    runtime_names: list[str] = []
    if isinstance(runtimes, dict):
        runtime_names = sorted(str(name) for name in runtimes)
    elif isinstance(runtimes, str):
        runtime_names = [runtimes]
    gpu_runtime_detected = "nvidia" in runtime_names
    return {
        "cli_found": True,
        "gpu_runtime_detected": gpu_runtime_detected,
        "runtime_names": runtime_names,
        "error": completed.stderr.strip() or None if completed.returncode else None,
    }


def _run_probe_command(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )


def _probe_github_actions_gpu_route(
    *,
    github_repo: str | None,
    gh_path: str | None,
    command_runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]],
) -> dict[str, Any]:
    probe: dict[str, Any] = {
        "enabled": bool(github_repo),
        "repo": github_repo,
        "gh_cli_path": gh_path,
        "safe_for_git": True,
        "secret_values_recorded": False,
        "secret_names_recorded": False,
        "api_errors": [],
        "runner_count": None,
        "runner_summaries": [],
        "self_hosted_gpu_runner_available": False,
        "secret_count": None,
        "gpu_related_secret_count": None,
        "configured": False,
    }
    if not github_repo:
        return probe
    if gh_path is None:
        probe["api_errors"].append("gh CLI was not found")
        return probe

    def run_api(endpoint: str) -> dict[str, Any] | None:
        try:
            completed = command_runner([gh_path, "api", endpoint])
        except (OSError, subprocess.TimeoutExpired) as exc:
            probe["api_errors"].append(str(exc))
            return None
        if completed.returncode != 0:
            message = completed.stderr.strip() or completed.stdout.strip() or f"gh api {endpoint} failed"
            probe["api_errors"].append(message)
            return None
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            probe["api_errors"].append(f"gh api {endpoint} returned invalid JSON: {exc}")
            return None
        if not isinstance(payload, dict):
            probe["api_errors"].append(f"gh api {endpoint} returned non-object JSON")
            return None
        return payload

    runners_payload = run_api(f"repos/{github_repo}/actions/runners")
    if runners_payload is not None:
        runners = runners_payload.get("runners", [])
        if isinstance(runners, list):
            probe["runner_count"] = int(runners_payload.get("total_count", len(runners)) or 0)
            summaries: list[dict[str, Any]] = []
            for runner in runners:
                if not isinstance(runner, dict):
                    continue
                labels = runner.get("labels", [])
                label_names = sorted(
                    str(label.get("name"))
                    for label in labels
                    if isinstance(label, dict) and label.get("name") is not None
                )
                status = str(runner.get("status", "unknown"))
                summaries.append({"status": status, "labels": label_names})
                if status == "online" and {"self-hosted", "gpu"}.issubset(set(label_names)):
                    probe["self_hosted_gpu_runner_available"] = True
            probe["runner_summaries"] = summaries

    secrets_payload = run_api(f"repos/{github_repo}/actions/secrets")
    if secrets_payload is not None:
        secrets = secrets_payload.get("secrets", [])
        if isinstance(secrets, list):
            probe["secret_count"] = int(secrets_payload.get("total_count", len(secrets)) or 0)
            gpu_related_count = 0
            for secret in secrets:
                if not isinstance(secret, dict):
                    continue
                name = str(secret.get("name", "")).upper()
                if any(keyword in name for keyword in _GITHUB_GPU_SECRET_KEYWORDS):
                    gpu_related_count += 1
            probe["gpu_related_secret_count"] = gpu_related_count

    probe["configured"] = bool(probe["self_hosted_gpu_runner_available"])
    return probe


def probe_gpu_execution_environment(
    out_dir: Path,
    *,
    env: Mapping[str, str] | None = None,
    command_lookup: Callable[[str], str | None] | None = None,
    command_runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] | None = None,
    github_repo: str | None = None,
) -> GvhmrGpuExecutionProbeWriteResult:
    """Write a safe local/provider GPU execution readiness probe.

    The manifest records variable names and command presence only. It must not
    expose credential values or attempt to run GVHMR.
    """

    validate_output_dir(out_dir)
    current_env = os.environ if env is None else env
    lookup = shutil.which if command_lookup is None else command_lookup
    nvidia_smi = lookup("nvidia-smi")
    docker_path = lookup("docker")
    gh_path = lookup("gh")
    providers: dict[str, Any] = {}
    for provider, prefixes in _GPU_PROVIDER_ENV_PREFIXES.items():
        command_paths = _command_paths(lookup, _GPU_PROVIDER_CLIS[provider])
        env_keys = _env_keys_for_prefixes(current_env, prefixes)
        providers[provider] = {
            "env_keys_present": env_keys,
            "cli_paths": command_paths,
            "configured": bool(env_keys) and any(command_paths.values()),
        }

    local_cuda_available = nvidia_smi is not None
    provider_candidates = [name for name, data in providers.items() if data["configured"]]
    docker_probe = _probe_docker_gpu_runtime(docker_path)
    docker_gpu_runtime = bool(docker_probe["gpu_runtime_detected"])
    github_actions_probe = _probe_github_actions_gpu_route(
        github_repo=github_repo,
        gh_path=gh_path,
        command_runner=_run_probe_command if command_runner is None else command_runner,
    )
    github_actions_gpu_runner = bool(github_actions_probe["self_hosted_gpu_runner_available"])
    if local_cuda_available:
        status = "local_cuda_available"
    elif provider_candidates:
        status = "provider_candidate_available"
    elif docker_gpu_runtime:
        status = "docker_gpu_runtime_available"
    elif github_actions_gpu_runner:
        status = "github_actions_gpu_runner_available"
    else:
        status = "external_gpu_artifact_missing"
    route_visible = status != "external_gpu_artifact_missing"

    manifest_path = out_dir / "manifest.json"
    manifest = {
        "schema": GVHMR_GPU_EXECUTION_PROBE_SCHEMA,
        "status": status,
        "safe_for_git": True,
        "secret_values_recorded": False,
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "platform": platform.platform(),
        },
        "local_cuda": {
            "nvidia_smi_path": nvidia_smi,
            "available": local_cuda_available,
        },
        "docker": docker_probe,
        "providers": providers,
        "provider_candidates": provider_candidates,
        "github_actions": github_actions_probe,
        "classification": {
            "blocked_locally": not route_visible,
            "reason": (
                "No local CUDA runtime, Docker GPU runtime, configured GPU provider, "
                "or optional GitHub self-hosted GPU runner was detected."
                if not route_visible
                else "A possible GPU execution route is visible; validate it before running GVHMR."
            ),
            "next_action": (
                "Copy the ignored GPU input archive to a GPU-capable machine or configure a provider "
                "before running GVHMR, then return a neodojo.gvhmr_smplx_joints.v1 export."
            ),
        },
    }
    _write_json(manifest_path, manifest)
    return GvhmrGpuExecutionProbeWriteResult(manifest_path=manifest_path, status=status)


def write_real_artifact_intake_smoke_input(
    out_dir: Path,
    *,
    frame_count: int = 36,
) -> RealArtifactIntakeSmokeInputWriteResult:
    """Write fixture-only returned-artifact inputs for the import-demo lane."""

    validate_output_dir(out_dir)
    if frame_count <= 0:
        raise ValueError("frame count must be positive")

    out_dir.mkdir(parents=True, exist_ok=True)
    source_materialization_path = out_dir / "source-materialization.json"
    gvhmr_json_path = out_dir / "gvhmr-smplx-joints.json"
    duration_seconds = round(frame_count / FIXTURE_FPS, 6)
    trim = {
        "start_seconds": 0.25,
        "end_seconds": round(0.25 + duration_seconds, 6),
        "duration_seconds": duration_seconds,
    }
    source_id = "fixture-real-artifact-intake-smoke"
    trimmed_video_argument = _as_posix(out_dir / "source" / "trimmed-clip.mp4")
    source_materialization = {
        "schema": SOURCE_MATERIALIZATION_SCHEMA,
        "status": "fixture_smoke_input",
        "fixture_only": True,
        "media_committed_to_repo": False,
        "source_prep": {
            "manifest": None,
            "source_id": source_id,
            "source_kind": "fixture_smoke",
            "title_english": "Fixture real-artifact intake smoke segment",
            "source_schema": REAL_CONVERSION_PREP_SCHEMA,
        },
        "source_media": {
            "schema": "neodojo.source_media_materialized.v1",
            "local_file": None,
            "prep_probe": None,
            "rights_notes": "fixture-only smoke input; no source media exists or should be committed",
        },
        "trim": trim,
        "ffmpeg": {
            "available": False,
            "executable": None,
            "dry_run": True,
            "commands": [],
        },
        "outputs": {
            "trimmed_video_path": trimmed_video_argument,
            "trimmed_video": None,
            "frames_dir": _as_posix(out_dir / "source" / "frames"),
            "frame_pattern": _as_posix(out_dir / "source" / "frames" / "frame-%06d.jpg"),
            "extracted_frame_count": 0,
            "first_frame": None,
            "last_frame": None,
        },
        "validation": {
            "schema": "neodojo.source_materialization_validation.v1",
            "source_file_validated": False,
            "trimmed_video_written": False,
            "frames_extracted": False,
            "duration": {
                "checked": False,
                "succeeded": False,
                "expected_duration_seconds": duration_seconds,
                "actual_duration_seconds": None,
                "delta_seconds": None,
                "tolerance_seconds": None,
                "error": "fixture smoke input does not include source media",
            },
            "gvhmr_input_ready": False,
        },
        "gpu_handoff": {
            "schema": "neodojo.gvhmr_input_handoff.v1",
            "blocked_locally": True,
            "trimmed_video_argument": trimmed_video_argument,
            "expected_export_json": _as_posix(gvhmr_json_path),
            "command_template": "fixture smoke input; GVHMR was not run",
            "notes": (
                "This manifest exists only to exercise the local returned-artifact "
                "intake path. It is not evidence of a real GVHMR execution."
            ),
        },
    }
    _write_json(source_materialization_path, source_materialization)

    gvhmr_export = {
        "schema": GVHMR_JOINT_EXPORT_SCHEMA,
        "fixture_only": True,
        "routine": FIXTURE_ROUTINE,
        "form": FIXTURE_FORM,
        "fps": FIXTURE_FPS,
        "frames": build_smplx_fixture_frames(frame_count),
        "provenance": {
            "source_materialization_manifest": _as_posix(source_materialization_path),
            "source_materialization_sha256": sha256_file(source_materialization_path),
            "source_id": source_id,
            "trim": trim,
            "input_video": trimmed_video_argument,
            "input_video_sha256": None,
            "gpu_command": "fixture smoke input; GVHMR was not run",
            "runtime": "neodojo fixture smoke",
            "upstream_version": "fixture",
        },
    }
    _write_json(gvhmr_json_path, gvhmr_export)
    return RealArtifactIntakeSmokeInputWriteResult(
        source_materialization_path=source_materialization_path,
        gvhmr_json_path=gvhmr_json_path,
    )


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


def _title_from_path(path: Path) -> str:
    return path.stem.replace("_", " ").replace("-", " ").strip() or "Local source video"


def _probe_duration_seconds(probe: dict[str, Any], label: str) -> float:
    if not probe.get("succeeded"):
        raise ValueError(f"{label} requires ffprobe metadata: {probe.get('error') or 'probe failed'}")
    format_info = probe.get("format")
    duration = format_info.get("duration_seconds") if isinstance(format_info, dict) else None
    try:
        parsed = float(duration)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} probe did not include duration_seconds") from exc
    if parsed <= 0:
        raise ValueError(f"{label} probe duration_seconds must be positive")
    return parsed


def _local_source_row(
    *,
    local_video: Path,
    source_id: str,
    title_english: str | None,
    title_chinese: str | None,
    category: str,
    category_chinese: str,
    origin_url: str | None,
) -> tuple[dict[str, str], dict[str, Any]]:
    metadata = local_file_metadata(
        local_video,
        label="local source video",
        allowed_suffixes={".mp4", ".mov", ".m4v", ".webm"},
    )
    probe = _ffprobe_media(local_video)
    duration_seconds = _probe_duration_seconds(probe, "custom local source")
    video_stream = probe.get("video_stream") if isinstance(probe.get("video_stream"), dict) else {}
    width = video_stream.get("width")
    height = video_stream.get("height")
    resolution = f"{width}x{height}" if width and height else "unknown"
    display_title = title_english or _title_from_path(local_video)
    source_url = origin_url or ""
    row = {
        "category_slug": category,
        "category_chinese": category_chinese,
        "article_title_chinese": title_chinese or display_title,
        "title_english": display_title,
        "article_url": source_url,
        "source_mp4_url": source_url,
        "selected_quality": "local",
        "resolution": resolution,
        "duration_seconds": str(round(duration_seconds, 6)),
        "source_size_mib": f"{metadata['size_bytes'] / (1024 * 1024):.2f}",
        "recommended_output_path": _as_posix(local_video),
    }
    return row, {"id": source_id, "probe": probe, "source_kind": "local_user_supplied"}


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
            "source_kind": prep_payload.get("source", {}).get("source_kind")
            if isinstance(prep_payload.get("source"), dict)
            else None,
            "title_english": prep_payload.get("source", {}).get("title_english")
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


def _load_handoff_manifest(gpu_handoff: Path) -> tuple[Path, dict[str, Any]]:
    manifest_path = gpu_handoff / "manifest.json" if gpu_handoff.is_dir() else gpu_handoff
    manifest = _load_json_object(manifest_path, "GVHMR GPU handoff manifest")
    require_schema(manifest, GVHMR_GPU_HANDOFF_SCHEMA, "GVHMR GPU handoff manifest")
    return manifest_path, manifest


def _load_gpu_input_manifest(gpu_input: Path) -> tuple[Path, dict[str, Any]]:
    manifest_path = gpu_input / "manifest.json" if gpu_input.is_dir() else gpu_input
    manifest = _load_json_object(manifest_path, "GVHMR GPU input manifest")
    require_schema(manifest, GVHMR_GPU_INPUT_BUNDLE_SCHEMA, "GVHMR GPU input manifest")
    return manifest_path, manifest


def _load_gpu_input_archive_manifest(gpu_input_archive: Path) -> tuple[Path, dict[str, Any]]:
    manifest_path = gpu_input_archive / "manifest.json" if gpu_input_archive.is_dir() else gpu_input_archive
    manifest = _load_json_object(manifest_path, "GVHMR GPU input archive manifest")
    require_schema(manifest, GVHMR_GPU_INPUT_ARCHIVE_SCHEMA, "GVHMR GPU input archive manifest")
    return manifest_path, manifest


def _load_gpu_run_request_manifest(gpu_run_request: Path) -> tuple[Path, dict[str, Any]]:
    manifest_path = gpu_run_request / "manifest.json" if gpu_run_request.is_dir() else gpu_run_request
    manifest = _load_json_object(manifest_path, "GVHMR GPU run request manifest")
    require_schema(manifest, GVHMR_GPU_RUN_REQUEST_SCHEMA, "GVHMR GPU run request manifest")
    return manifest_path, manifest


def _load_colab_operator_notebook_manifest(colab_notebook: Path) -> tuple[Path, dict[str, Any]]:
    manifest_path = colab_notebook / "manifest.json" if colab_notebook.is_dir() else colab_notebook
    manifest = _load_json_object(manifest_path, "GVHMR Colab operator notebook manifest")
    require_schema(manifest, GVHMR_COLAB_OPERATOR_NOTEBOOK_SCHEMA, "GVHMR Colab operator notebook manifest")
    return manifest_path, manifest


def _load_operator_package_manifest(operator_package: Path) -> tuple[Path, dict[str, Any]]:
    manifest_path = operator_package / "manifest.json" if operator_package.is_dir() else operator_package
    manifest = _load_json_object(manifest_path, "GVHMR operator package manifest")
    require_schema(manifest, GVHMR_OPERATOR_PACKAGE_SCHEMA, "GVHMR operator package manifest")
    return manifest_path, manifest


def _load_operator_package_archive_manifest(operator_package_archive: Path) -> tuple[Path, dict[str, Any]]:
    if operator_package_archive.is_dir():
        manifest_path = operator_package_archive / "manifest.json"
    elif operator_package_archive.suffix == ".json":
        manifest_path = operator_package_archive
    else:
        manifest_path = operator_package_archive.parent / "manifest.json"
    manifest = _load_json_object(manifest_path, "GVHMR operator package archive manifest")
    require_schema(
        manifest,
        GVHMR_OPERATOR_PACKAGE_ARCHIVE_SCHEMA,
        "GVHMR operator package archive manifest",
    )
    return manifest_path, manifest


def _copy_handoff_file(
    *,
    handoff_dir: Path,
    source_name: str,
    output_dir: Path,
    output_name: str,
    required: bool = True,
) -> Path | None:
    source_path = handoff_dir / source_name
    if not source_path.exists():
        if required:
            raise ValueError(f"GPU handoff file is missing: {source_path}")
        return None
    destination = output_dir / output_name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination)
    return destination


def _iter_bundle_files(bundle_dir: Path, *, archive_output_dir: Path) -> list[tuple[Path, str]]:
    bundle_root = bundle_dir.resolve()
    archive_root = archive_output_dir.resolve()
    files: list[tuple[Path, str]] = []
    for path in sorted(bundle_dir.rglob("*")):
        if not path.is_file():
            continue
        resolved = path.resolve()
        if archive_root != bundle_root and archive_root in resolved.parents:
            continue
        if path.suffix in {".tar", ".gz", ".tgz"}:
            continue
        arcname = _as_posix(resolved.relative_to(bundle_root))
        files.append((path, arcname))
    if not files:
        raise ValueError(f"GPU input bundle has no files to archive: {bundle_dir}")
    return files


def _validate_gpu_input_archive_members(files: list[tuple[Path, str]], *, media_included: bool) -> None:
    member_names = {arcname for _, arcname in files}
    required = {
        "RUN_ON_GPU.md",
        "export_neodojo_gvhmr.py",
        "gpu-handoff-manifest.json",
        "gvhmr-smplx-joints.template.json",
        "manifest.json",
        "run_gvhmr_neodojo.sh",
        "source-materialization.json",
    }
    if media_included:
        required.add("source/trimmed-clip.mp4")
    missing = sorted(required - member_names)
    if missing:
        raise ValueError(
            "GPU input archive is missing required bundle files: " + ", ".join(missing)
        )


def _write_gpu_runner_script(path: Path) -> None:
    runner_script = resources.files("neodojo.templates").joinpath("run_gvhmr_neodojo.sh").read_text(
        encoding="utf-8"
    )
    path.write_text(runner_script, encoding="utf-8")
    path.chmod(0o755)


def _write_gpu_input_runbook(
    path: Path,
    *,
    manifest_path: Path,
    status: str,
    media_included: bool,
    bundle_video: Path | None,
    returned_export_filename: str,
    local_import_command: str,
) -> None:
    video_argument = _as_posix(bundle_video) if media_included and bundle_video is not None else "<copy trimmed clip>"
    upstream_command = f"python tools/demo/demo.py --video {video_argument} --output_root gvhmr-output"
    exporter_command = (
        "python export_neodojo_gvhmr.py "
        "--hmr4d-results gvhmr-output/trimmed-clip/hmr4d_results.pt "
        "--smplx-model-dir <path-to-licensed-smplx-model-dir> "
        "--template gvhmr-smplx-joints.template.json "
        "--source-materialization source-materialization.json "
        f"--out {returned_export_filename} "
        "--parameter-block smpl_params_global "
        "--fps 30 "
        "--routine Baduanjin "
        "--form \"Two Hands Hold Up the Heavens\" "
        "--runtime \"<GPU runtime and hardware>\" "
        "--upstream-version \"<GVHMR commit or package version>\" "
        "--gpu-command \"<actual GVHMR command>\""
    )
    body = "\n".join(
        [
            "# neodojo GVHMR GPU Input Bundle",
            "",
            f"Status: `{status}`",
            "",
            "This ignored local directory is meant to be copied to a GPU-capable GVHMR machine.",
            "It may contain a trimmed source clip when explicitly packaged with media; do not commit or publish that media.",
            "",
            "## Files",
            "",
            f"- `{manifest_path.name}`: machine-readable bundle manifest.",
            "- `gpu-handoff-manifest.json`: source handoff metadata.",
            "- `source-materialization.json`: source/trim metadata.",
            "- `gvhmr-smplx-joints.template.json`: returned export template.",
            "- `export_neodojo_gvhmr.py`: GPU-side neodojo exporter helper.",
            "- `run_gvhmr_neodojo.sh`: executable GPU-side runner that wraps GVHMR and the neodojo exporter.",
            "- `source/trimmed-clip.mp4`: local media for GVHMR, present only when `media_included` is true.",
            "",
            "## One-Command GPU Runner",
            "",
            "Place licensed GVHMR/SMPL-X checkpoints as required by upstream GVHMR, then run:",
            "",
            _markdown_command(
                "SMPLX_MODEL_DIR=<path-to-licensed-smplx-model-dir> ./run_gvhmr_neodojo.sh --install"
            ),
            "",
            "Set `GVHMR_REPO=/path/to/GVHMR` and omit `--install` if the GPU environment already has GVHMR installed.",
            "",
            "## Run GVHMR On The GPU Machine",
            "",
            _markdown_command(upstream_command),
            "",
            "## Export neodojo JSON On The GPU Machine",
            "",
            _markdown_command(exporter_command),
            "",
            "Return the generated JSON with the bundle. The local validation command is:",
            "",
            _markdown_command(local_import_command),
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _write_gpu_handoff_readme(
    path: Path,
    *,
    manifest_path: Path,
    status: str,
    input_video: str | None,
    expected_export_json: str,
    returned_export_filename: str,
    upstream_command: str,
    exporter_command: str,
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
            "- `source-materialization.json`: copy of the local source/trim handoff metadata for the GPU machine.",
            "- `gvhmr-smplx-joints.template.json`: JSON shape and provenance fields to preserve in the returned export.",
            "- `export_neodojo_gvhmr.py`: GPU-side helper for converting `hmr4d_results.pt` plus a licensed local SMPL-X model into the neodojo export schema.",
            "- `run_gvhmr_neodojo.sh`: executable GPU-side runner for the upstream GVHMR demo plus neodojo export.",
            "",
            "## GPU Input",
            "",
            f"- Trimmed video argument: `{input_video or '<missing>'}`",
            "",
            "## One-Command GPU Runner",
            "",
            "When this directory is copied together with the trimmed clip, the GPU operator can run:",
            "",
            _markdown_command(
                "SMPLX_MODEL_DIR=<path-to-licensed-smplx-model-dir> ./run_gvhmr_neodojo.sh --install"
            ),
            "",
            "Set `GVHMR_REPO=/path/to/GVHMR` and omit `--install` if the GPU environment already has GVHMR installed.",
            "",
            "## Upstream GVHMR Command Template",
            "",
            _markdown_command(upstream_command),
            "",
            "Fill in the concrete GVHMR environment, checkpoint, and output directory on the GPU machine.",
            "",
            "## GPU-Side neodojo Export Helper",
            "",
            _markdown_command(exporter_command),
            "",
            "Run this after GVHMR writes `hmr4d_results.pt`. It requires `torch`, `smplx`, and licensed local SMPL-X assets on the GPU machine.",
            "",
            "## Return Artifact",
            "",
            f"The GPU helper writes `{returned_export_filename}` in the handoff directory. Return that JSON with the handoff bundle, then keep or copy it to `{expected_export_json}` for local validation.",
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
    exporter_script_path = out_dir / "export_neodojo_gvhmr.py"
    runner_script_path = out_dir / "run_gvhmr_neodojo.sh"
    source_materialization_copy_path = out_dir / "source-materialization.json"

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
    input_declared = bool(trimmed_video)
    input_exists = bool(input_declared and input_video_path and input_video_path.exists())
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
        else _as_posix(out_dir / "gvhmr-smplx-joints.json")
    )
    suggested_export = gpu_handoff.get("expected_export_json")
    suggested_export = suggested_export if isinstance(suggested_export, str) else None
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
    exporter_command = (
        "python export_neodojo_gvhmr.py "
        f"--hmr4d-results <gvhmr-output-dir>/{Path(input_video).stem if input_video else '<video-stem>'}/hmr4d_results.pt "
        "--smplx-model-dir <path-to-licensed-smplx-model-dir> "
        f"--template {export_template_path.name} "
        f"--source-materialization {source_materialization_copy_path.name} "
        f"--out {Path(expected_export).name} "
        "--parameter-block smpl_params_global "
        "--fps 30 "
        "--routine Baduanjin "
        "--form \"Two Hands Hold Up the Heavens\" "
        "--runtime \"<GPU runtime and hardware>\" "
        "--upstream-version \"<GVHMR commit or package version>\" "
        "--gpu-command \"<actual GVHMR command>\""
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
    exporter_script = resources.files("neodojo.templates").joinpath("gvhmr_export_neodojo.py").read_text(
        encoding="utf-8"
    )
    exporter_script_path.write_text(exporter_script, encoding="utf-8")
    _write_gpu_runner_script(runner_script_path)
    _write_json(source_materialization_copy_path, materialization)

    manifest = {
        "schema": GVHMR_GPU_HANDOFF_SCHEMA,
        "status": status,
        "fixture_only": False,
        "media_committed_to_repo": False,
        "source_materialization": _as_posix(source_materialization),
        "source_materialization_copy": _as_posix(source_materialization_copy_path),
        "source_materialization_sha256": source_hash,
        "source": {
            "source_id": source_prep.get("source_id"),
            "source_kind": source_prep.get("source_kind"),
            "title_english": source_prep.get("title_english"),
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
            "suggested_path_from_source_prep": suggested_export,
            "template": _as_posix(export_template_path),
            "gpu_exporter_script": _as_posix(exporter_script_path),
            "gpu_bundle_output": Path(expected_export).name,
        },
        "gpu_bundle": {
            "copyable": True,
            "files": {
                "manifest": manifest_path.name,
                "readme": readme_path.name,
                "source_materialization": source_materialization_copy_path.name,
                "export_template": export_template_path.name,
                "exporter_script": exporter_script_path.name,
                "runner_script": runner_script_path.name,
                "returned_export": Path(expected_export).name,
            },
            "notes": "Copy this directory plus the materialized trimmed video to the GPU machine; the exporter command uses bundle-local filenames.",
        },
        "commands": {
            "upstream_gvhmr": upstream_command,
            "gpu_export_neodojo": exporter_command,
            "gpu_run_neodojo": (
                "SMPLX_MODEL_DIR=<path-to-licensed-smplx-model-dir> "
                "./run_gvhmr_neodojo.sh --install"
            ),
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
        returned_export_filename=Path(expected_export).name,
        upstream_command=upstream_command,
        exporter_command=exporter_command,
        local_import_command=local_import_command,
    )

    checked_paths = [
        manifest_path,
        readme_path,
        export_template_path,
        exporter_script_path,
        runner_script_path,
        source_materialization_copy_path,
        source_materialization,
    ]
    if input_exists and input_video_path is not None:
        checked_paths.append(input_video_path)
    return GvhmrGpuHandoffWriteResult(
        manifest_path=manifest_path,
        readme_path=readme_path,
        export_template_path=export_template_path,
        exporter_script_path=exporter_script_path,
        runner_script_path=runner_script_path,
        source_materialization_copy_path=source_materialization_copy_path,
        checked_paths=checked_paths,
        status=status,
    )


def package_gvhmr_gpu_input_bundle(
    out_dir: Path,
    *,
    gpu_handoff: Path,
    include_media: bool = False,
) -> GvhmrGpuInputBundleWriteResult:
    validate_output_dir(out_dir)
    handoff_manifest_path, handoff = _load_handoff_manifest(gpu_handoff)
    handoff_dir = handoff_manifest_path.parent
    bundle_files = handoff.get("gpu_bundle", {}).get("files")
    if not isinstance(bundle_files, dict):
        raise ValueError("GVHMR GPU handoff manifest is missing gpu_bundle.files")

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    runbook_path = out_dir / "RUN_ON_GPU.md"
    expected_export = handoff.get("expected_export") if isinstance(handoff.get("expected_export"), dict) else {}
    returned_export_filename = str(
        expected_export.get("gpu_bundle_output")
        or bundle_files.get("returned_export")
        or "gvhmr-smplx-joints.json"
    )

    copied_paths: list[Path] = []
    handoff_copy = _copy_handoff_file(
        handoff_dir=handoff_dir,
        source_name=str(bundle_files.get("manifest", "manifest.json")),
        output_dir=out_dir,
        output_name="gpu-handoff-manifest.json",
    )
    if handoff_copy is not None:
        copied_paths.append(handoff_copy)
    for file_key, default_name in [
        ("source_materialization", "source-materialization.json"),
        ("export_template", "gvhmr-smplx-joints.template.json"),
        ("exporter_script", "export_neodojo_gvhmr.py"),
    ]:
        copied = _copy_handoff_file(
            handoff_dir=handoff_dir,
            source_name=str(bundle_files.get(file_key, default_name)),
            output_dir=out_dir,
            output_name=default_name,
        )
        if copied is not None:
            copied_paths.append(copied)
    runner_script_path = _copy_handoff_file(
        handoff_dir=handoff_dir,
        source_name=str(bundle_files.get("runner_script", "run_gvhmr_neodojo.sh")),
        output_dir=out_dir,
        output_name="run_gvhmr_neodojo.sh",
        required=False,
    )
    if runner_script_path is None:
        runner_script_path = out_dir / "run_gvhmr_neodojo.sh"
        _write_gpu_runner_script(runner_script_path)
    else:
        runner_script_path.chmod(0o755)
    copied_paths.append(runner_script_path)

    gpu_input = handoff.get("gpu_input") if isinstance(handoff.get("gpu_input"), dict) else {}
    input_reference = gpu_input.get("local_path_checked") or gpu_input.get("trimmed_video_argument")
    input_path = _resolve_handoff_media_path(input_reference if isinstance(input_reference, str) else None, handoff_dir)
    expected_sha = gpu_input.get("sha256_expected") if isinstance(gpu_input.get("sha256_expected"), str) else None
    media_path: Path | None = None
    media_sha: str | None = None
    media_included = False

    if include_media:
        if input_path is None or not input_path.exists():
            raise ValueError("cannot include media because the handoff input video does not exist")
        media_sha = sha256_file(input_path)
        if expected_sha is not None and media_sha != expected_sha:
            raise ValueError("cannot include media because the handoff input video checksum does not match")
        media_path = out_dir / "source" / "trimmed-clip.mp4"
        media_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(input_path, media_path)
        copied_paths.append(media_path)
        media_included = True

    commands = handoff.get("commands") if isinstance(handoff.get("commands"), dict) else {}
    local_import_command = commands.get("local_import_demo")
    if not isinstance(local_import_command, str) or not local_import_command:
        local_import_command = (
            "PYTHONPATH=src python -m neodojo real-conversion import-demo "
            "--source-materialization source-materialization.json "
            f"--gvhmr-json {returned_export_filename} --out outputs/real-demo"
        )
    status = "ready_for_gpu_with_media" if media_included else "metadata_only"
    checksum_matches = (expected_sha is None or media_sha == expected_sha) if media_included else None
    _write_gpu_input_runbook(
        runbook_path,
        manifest_path=manifest_path,
        status=status,
        media_included=media_included,
        bundle_video=Path("source/trimmed-clip.mp4") if media_included else None,
        returned_export_filename=returned_export_filename,
        local_import_command=local_import_command,
    )
    copied_paths.append(runbook_path)

    manifest = {
        "schema": GVHMR_GPU_INPUT_BUNDLE_SCHEMA,
        "status": status,
        "fixture_only": False,
        "media_committed_to_repo": False,
        "media_included": media_included,
        "source": handoff.get("source"),
        "trim": handoff.get("trim"),
        "source_handoff": {
            "manifest": _as_posix(handoff_manifest_path),
            "schema": handoff.get("schema"),
            "status": handoff.get("status"),
            "sha256": sha256_file(handoff_manifest_path),
        },
        "gpu_input": {
            "source_path": _as_posix(input_path) if input_path is not None else None,
            "bundle_path": _as_posix(media_path) if media_path is not None else None,
            "sha256_expected": expected_sha,
            "sha256_actual": media_sha,
            "checksum_matches": checksum_matches,
        },
        "files": {
            "runbook": runbook_path.name,
            "gpu_handoff_manifest": "gpu-handoff-manifest.json",
            "source_materialization": "source-materialization.json",
            "export_template": "gvhmr-smplx-joints.template.json",
            "exporter_script": "export_neodojo_gvhmr.py",
            "runner_script": "run_gvhmr_neodojo.sh",
            "trimmed_video": _as_posix(media_path) if media_path is not None else None,
            "returned_export": returned_export_filename,
        },
        "commands": {
            "gpu_run_neodojo": (
                "SMPLX_MODEL_DIR=<path-to-licensed-smplx-model-dir> "
                "./run_gvhmr_neodojo.sh --install"
            ),
            "local_import_demo": local_import_command,
        },
        "policy": {
            "safe_for_git": False if media_included else True,
            "notes": (
                "Generated under ignored outputs. Do not commit media bundles; "
                "copy them only to the GPU machine selected for the GVHMR run."
            ),
        },
    }
    _write_json(manifest_path, manifest)
    checked_paths = [manifest_path, *copied_paths]
    return GvhmrGpuInputBundleWriteResult(
        manifest_path=manifest_path,
        runbook_path=runbook_path,
        runner_script_path=runner_script_path,
        checked_paths=checked_paths,
        status=status,
    )


def package_gvhmr_gpu_input_archive(
    out_dir: Path,
    *,
    gpu_input: Path,
    archive_name: str = "neodojo-gvhmr-gpu-input.tar.gz",
) -> GvhmrGpuInputArchiveWriteResult:
    if not archive_name.endswith((".tar.gz", ".tgz")):
        raise ValueError("GPU input archive name must end with .tar.gz or .tgz")
    validate_output_dir(out_dir)
    gpu_input_manifest_path, gpu_input_manifest = _load_gpu_input_manifest(gpu_input)
    bundle_dir = gpu_input_manifest_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    archive_path = out_dir / archive_name
    manifest_path = out_dir / "manifest.json"
    files = _iter_bundle_files(bundle_dir, archive_output_dir=out_dir)
    media_included = bool(gpu_input_manifest.get("media_included"))
    _validate_gpu_input_archive_members(files, media_included=media_included)

    with tarfile.open(archive_path, "w:gz") as archive:
        for source_path, arcname in files:
            archive.add(source_path, arcname=arcname, recursive=False)

    archive_members = [
        {
            "path": arcname,
            "source": _as_posix(source_path),
            "sha256": sha256_file(source_path),
            "size_bytes": source_path.stat().st_size,
        }
        for source_path, arcname in files
    ]
    status = "archive_with_media" if media_included else "metadata_only_archive"
    manifest = {
        "schema": GVHMR_GPU_INPUT_ARCHIVE_SCHEMA,
        "status": status,
        "fixture_only": False,
        "media_included": media_included,
        "source": gpu_input_manifest.get("source"),
        "trim": gpu_input_manifest.get("trim"),
        "source_gpu_input": {
            "manifest": _as_posix(gpu_input_manifest_path),
            "schema": gpu_input_manifest.get("schema"),
            "status": gpu_input_manifest.get("status"),
            "sha256": sha256_file(gpu_input_manifest_path),
        },
        "archive": {
            "path": _as_posix(archive_path),
            "filename": archive_path.name,
            "sha256": sha256_file(archive_path),
            "size_bytes": archive_path.stat().st_size,
            "member_count": len(archive_members),
        },
        "members": archive_members,
        "policy": {
            "safe_for_git": not media_included,
            "notes": (
                "Generated under ignored outputs. Metadata-only archives are CI-safe; "
                "archives with media must not be committed or published."
            ),
        },
    }
    _write_json(manifest_path, manifest)
    checked_paths = [manifest_path, archive_path, *(source_path for source_path, _ in files)]
    return GvhmrGpuInputArchiveWriteResult(
        manifest_path=manifest_path,
        archive_path=archive_path,
        checked_paths=checked_paths,
        status=status,
    )


def _archive_path_from_manifest(manifest_path: Path, manifest: dict[str, Any]) -> Path:
    archive = manifest.get("archive")
    if not isinstance(archive, dict):
        raise ValueError("GVHMR GPU input archive manifest is missing archive metadata")
    raw_path = archive.get("path")
    if isinstance(raw_path, str) and raw_path:
        candidate = Path(raw_path)
        if candidate.exists():
            return candidate
    filename = archive.get("filename")
    if isinstance(filename, str) and filename:
        candidate = manifest_path.parent / filename
        if candidate.exists():
            return candidate
    raise ValueError("GVHMR GPU input archive file does not exist")


def _member_source(manifest: dict[str, Any], member_name: str) -> str | None:
    members = manifest.get("members")
    if not isinstance(members, list):
        return None
    for member in members:
        if not isinstance(member, dict):
            continue
        if member.get("path") == member_name and isinstance(member.get("source"), str):
            return str(member["source"])
    return None


def _optional_existing_path(path: Path) -> Path | None:
    return path if path.exists() else None


def _write_gpu_run_request_readme(path: Path, manifest: dict[str, Any]) -> None:
    archive = manifest["archive"]
    source = manifest.get("source") or {}
    trim = manifest.get("trim") or {}
    commands = manifest["commands"]
    required_assets = manifest["required_gpu_assets"]
    lines = [
        "# GVHMR GPU Run Request",
        "",
        "This generated request is the handoff for producing the real neodojo GVHMR artifact.",
        "It does not include SMPL-X assets, checkpoints, raw GVHMR results, or returned motion artifacts.",
        "",
        "## Archive",
        "",
        f"- Path: `{archive['path']}`",
        f"- SHA-256: `{archive['sha256']}`",
        f"- Media included: `{str(manifest['media_included']).lower()}`",
        f"- Status: `{manifest['status']}`",
        "",
        "## Source",
        "",
        f"- Source ID: `{source.get('source_id')}`",
        f"- Title: `{source.get('title_english')}`",
        f"- Trim: `{trim.get('start_seconds')}` to `{trim.get('end_seconds')}` seconds",
        "",
        "## Required GPU Assets",
        "",
        *[f"- {item}" for item in required_assets],
        "",
        "## Manual GPU Steps",
        "",
        _markdown_command(commands["unpack_archive"]),
        _markdown_command(commands["run_gvhmr_wrapper"]),
        "",
        "Return `gvhmr-smplx-joints.json` to the local neodojo workspace, then run:",
        "",
        _markdown_command(commands["local_real_artifact_intake"]),
        _markdown_command(commands["local_strict_verify"]),
        "",
        "## Optional GitHub Workflow",
        "",
        "If a self-hosted GitHub Actions runner labeled `self-hosted` and `gpu` is registered,",
        "use `.github/workflows/gvhmr-self-hosted-gpu.yml` with this archive path or a",
        "GVHMR operator package path.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_gvhmr_gpu_run_request(
    out_dir: Path,
    *,
    gpu_input_archive: Path,
    runbook: Path = Path("docs/runbooks/gvhmr-external-gpu.md"),
    self_hosted_workflow: Path = Path(".github/workflows/gvhmr-self-hosted-gpu.yml"),
) -> GvhmrGpuRunRequestWriteResult:
    validate_output_dir(out_dir)
    archive_manifest_path, archive_manifest = _load_gpu_input_archive_manifest(gpu_input_archive)
    archive_path = _archive_path_from_manifest(archive_manifest_path, archive_manifest)
    expected_sha = archive_manifest.get("archive", {}).get("sha256")
    actual_sha = sha256_file(archive_path)
    if expected_sha != actual_sha:
        raise ValueError("GVHMR GPU input archive checksum does not match its manifest")

    media_included = bool(archive_manifest.get("media_included"))
    status = "ready_for_external_gpu" if media_included else "metadata_only_not_ready_for_gpu"
    source_materialization = _member_source(archive_manifest, "source-materialization.json")
    local_source_materialization = source_materialization or "outputs/real-conversion-source/source-materialization.json"
    local_return_json = "path/to/gvhmr-smplx-joints.json"
    archive_name = archive_manifest.get("archive", {}).get("filename", archive_path.name)
    request_manifest_path = out_dir / "manifest.json"
    request_readme_path = out_dir / "README.md"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema": GVHMR_GPU_RUN_REQUEST_SCHEMA,
        "status": status,
        "blocked_locally": True,
        "media_included": media_included,
        "source": archive_manifest.get("source"),
        "trim": archive_manifest.get("trim"),
        "archive_manifest": _as_posix(archive_manifest_path),
        "archive": {
            "path": _as_posix(archive_path),
            "filename": archive_name,
            "sha256": actual_sha,
            "size_bytes": archive_path.stat().st_size,
            "member_count": archive_manifest.get("archive", {}).get("member_count"),
            "safe_for_git": archive_manifest.get("policy", {}).get("safe_for_git"),
        },
        "runbook": {
            "path": _as_posix(runbook),
            "exists": runbook.exists(),
        },
        "self_hosted_workflow": {
            "path": _as_posix(self_hosted_workflow),
            "exists": self_hosted_workflow.exists(),
            "required_runner_labels": ["self-hosted", "gpu"],
        },
        "required_gpu_assets": [
            "CUDA-capable GPU machine or self-hosted GitHub Actions runner",
            "GVHMR checkout, dependencies, and checkpoints",
            "licensed local SMPL-X model assets",
            "rights approval for the selected source clip",
        ],
        "expected_return_artifact": {
            "filename": "gvhmr-smplx-joints.json",
            "schema": GVHMR_JOINT_EXPORT_SCHEMA,
            "must_not_commit": True,
        },
        "commands": {
            "unpack_archive": f"mkdir -p neodojo-gvhmr-run && tar -xzf {archive_name} -C neodojo-gvhmr-run",
            "run_gvhmr_wrapper": (
                "cd neodojo-gvhmr-run && "
                "SMPLX_MODEL_DIR=<path-to-licensed-smplx-model-dir> "
                "./run_gvhmr_neodojo.sh --install"
            ),
            "local_real_artifact_intake": (
                "make real-artifact-intake "
                f"REAL_ARTIFACT_SOURCE_MATERIALIZATION={local_source_materialization} "
                f"REAL_ARTIFACT_GVHMR_JSON={local_return_json}"
            ),
            "local_strict_verify": "make verify-real",
        },
        "policy": {
            "safe_for_git": not media_included,
            "notes": (
                "This request is safe to commit only when media_included is false. "
                "Media-containing archives and returned GVHMR artifacts stay ignored."
            ),
        },
        "notes": (
            "This request makes the remaining external GVHMR step explicit; it does not run GVHMR locally."
        ),
    }
    _write_json(request_manifest_path, manifest)
    _write_gpu_run_request_readme(request_readme_path, manifest)
    checked_paths = [
        request_manifest_path,
        request_readme_path,
        archive_manifest_path,
        archive_path,
        *[path for path in (_optional_existing_path(runbook), _optional_existing_path(self_hosted_workflow)) if path],
    ]
    return GvhmrGpuRunRequestWriteResult(
        manifest_path=request_manifest_path,
        readme_path=request_readme_path,
        checked_paths=checked_paths,
        status=status,
    )


def _notebook_source(text: str) -> list[str]:
    return [line if line.endswith("\n") else f"{line}\n" for line in text.strip("\n").splitlines()]


def _notebook_cell(cell_type: str, source: str) -> dict[str, Any]:
    cell: dict[str, Any] = {
        "cell_type": cell_type,
        "metadata": {},
        "source": _notebook_source(source),
    }
    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    return cell


def _write_colab_operator_notebook(path: Path, request: dict[str, Any]) -> None:
    archive = request["archive"]
    expected_return = request["expected_return_artifact"]
    commands = request["commands"]
    archive_filename = str(archive["filename"])
    notebook = {
        "cells": [
            _notebook_cell(
                "markdown",
                f"""
# neodojo GVHMR Colab Operator

Generated from a `{GVHMR_GPU_RUN_REQUEST_SCHEMA}` handoff.

This notebook is for producing `{expected_return["schema"]}` from a prepared
neodojo GPU input archive. It does not contain source media, SMPL-X assets,
checkpoints, raw GVHMR results, or returned motion artifacts.
""",
            ),
            _notebook_cell(
                "markdown",
                """
## 1. Provide The Archive And Assets

Upload or mount the prepared `neodojo-gvhmr-gpu-input.tar.gz` archive. Keep
licensed SMPL-X assets and GVHMR checkpoints in private storage. Do not commit
or publish media-containing archives, checkpoints, SMPL-X assets, `.pt` files,
logs, or returned motion artifacts.
""",
            ),
            _notebook_cell(
                "code",
                f"""
from pathlib import Path
import hashlib
import os
import shutil
import subprocess
import tarfile

ARCHIVE_FILENAME = {json.dumps(archive_filename)}
EXPECTED_SHA256 = {json.dumps(str(archive["sha256"]))}
RUN_DIR = Path("/content/neodojo-gvhmr-run")
SMPLX_MODEL_DIR = Path("/content/drive/MyDrive/smplx")
GVHMR_REPO = Path("/content/GVHMR")
RUN_GVHMR = False

print("Archive:", ARCHIVE_FILENAME)
print("Expected SHA-256:", EXPECTED_SHA256)
print("Expected return:", {json.dumps(expected_return["filename"])})
""",
            ),
            _notebook_cell(
                "code",
                """
try:
    from google.colab import drive, files
    IN_COLAB = True
except ModuleNotFoundError:
    IN_COLAB = False
    drive = None
    files = None

if IN_COLAB:
    print("Optional: drive.mount('/content/drive')")
    print("Optional: files.upload() to upload the archive into the current directory")
else:
    print("Not running inside Google Colab; execute these cells in a GPU notebook runtime.")
""",
            ),
            _notebook_cell(
                "code",
                """
archive_path = Path(ARCHIVE_FILENAME)
if not archive_path.exists():
    raise FileNotFoundError(f"Upload or copy the archive to: {archive_path}")

actual_sha256 = hashlib.sha256(archive_path.read_bytes()).hexdigest()
if actual_sha256 != EXPECTED_SHA256:
    raise ValueError(f"Archive checksum mismatch: {actual_sha256}")

if RUN_DIR.exists():
    shutil.rmtree(RUN_DIR)
RUN_DIR.mkdir(parents=True, exist_ok=True)

with tarfile.open(archive_path, "r:gz") as tar:
    destination = RUN_DIR.resolve()
    for member in tar.getmembers():
        member_path = (destination / member.name).resolve()
        if member_path != destination and destination not in member_path.parents:
            raise ValueError(f"Unsafe archive member path: {member.name}")
    tar.extractall(destination)

print("Unpacked to", RUN_DIR)
print("\\n".join(sorted(str(path.relative_to(RUN_DIR)) for path in RUN_DIR.rglob("*") if path.is_file())))
""",
            ),
            _notebook_cell(
                "code",
                """
os.chdir(RUN_DIR)
subprocess.run(["bash", "run_gvhmr_neodojo.sh", "--help"], check=True)

if RUN_GVHMR:
    env = {
        **os.environ,
        "SMPLX_MODEL_DIR": str(SMPLX_MODEL_DIR),
        "GVHMR_REPO": str(GVHMR_REPO),
    }
    subprocess.run(["bash", "run_gvhmr_neodojo.sh", "--install"], env=env, check=True)
else:
    print("Set RUN_GVHMR = True only after SMPL-X assets, GVHMR checkpoints, and rights review are ready.")
""",
            ),
            _notebook_cell(
                "code",
                """
result_path = RUN_DIR / "gvhmr-smplx-joints.json"
if result_path.exists():
    print("Return this file to the local neodojo workspace:", result_path)
    if IN_COLAB:
        files.download(str(result_path))
else:
    print("No returned export yet. Run GVHMR first, then re-run this cell.")
""",
            ),
            _notebook_cell(
                "markdown",
                f"""
## 2. Validate Locally After Download

After downloading `{expected_return["filename"]}` to the local neodojo
workspace, run:

```bash
{commands["local_real_artifact_intake"]}
{commands["local_strict_verify"]}
```
""",
            ),
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
            },
            "neodojo": {
                "schema": GVHMR_COLAB_OPERATOR_NOTEBOOK_SCHEMA,
                "source_schema": GVHMR_GPU_RUN_REQUEST_SCHEMA,
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    _write_json(path, notebook)


def write_gvhmr_colab_operator_notebook(
    out_dir: Path,
    *,
    gpu_run_request: Path,
) -> GvhmrColabOperatorNotebookWriteResult:
    validate_output_dir(out_dir)
    request_manifest_path, request = _load_gpu_run_request_manifest(gpu_run_request)
    archive = request.get("archive")
    if not isinstance(archive, dict):
        raise ValueError("GVHMR GPU run request manifest is missing archive metadata")
    expected_return = request.get("expected_return_artifact")
    if not isinstance(expected_return, dict):
        raise ValueError("GVHMR GPU run request manifest is missing expected return artifact metadata")

    media_included = bool(request.get("media_included"))
    status = "ready_for_colab_operator" if media_included else "metadata_only_not_ready_for_gpu"
    out_dir.mkdir(parents=True, exist_ok=True)
    notebook_path = out_dir / "gvhmr-colab-operator.ipynb"
    manifest_path = out_dir / "manifest.json"
    _write_colab_operator_notebook(notebook_path, request)

    manifest = {
        "schema": GVHMR_COLAB_OPERATOR_NOTEBOOK_SCHEMA,
        "status": status,
        "blocked_locally": True,
        "media_included": media_included,
        "gpu_run_request": {
            "manifest": _as_posix(request_manifest_path),
            "schema": request.get("schema"),
            "status": request.get("status"),
            "sha256": sha256_file(request_manifest_path),
        },
        "notebook": {
            "path": _as_posix(notebook_path),
            "filename": notebook_path.name,
            "sha256": sha256_file(notebook_path),
        },
        "archive": {
            "filename": archive.get("filename"),
            "sha256": archive.get("sha256"),
            "safe_for_git": archive.get("safe_for_git"),
        },
        "expected_return_artifact": expected_return,
        "policy": {
            "safe_for_git": not media_included,
            "notes": (
                "The notebook is a generated operator handoff. It is safe to commit only when "
                "the source run request is metadata-only; media-containing archives and returned "
                "GVHMR artifacts stay ignored."
            ),
        },
        "notes": (
            "This notebook makes the Colab operator path explicit; it does not run GVHMR locally."
        ),
    }
    _write_json(manifest_path, manifest)
    checked_paths = [manifest_path, notebook_path, request_manifest_path]
    return GvhmrColabOperatorNotebookWriteResult(
        manifest_path=manifest_path,
        notebook_path=notebook_path,
        checked_paths=checked_paths,
        status=status,
    )


def _copy_operator_package_file(source: Path, destination_dir: Path, *, filename: str | None = None) -> Path:
    if not source.exists():
        raise ValueError(f"GVHMR operator package source file does not exist: {source}")
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / (filename or source.name)
    if source.resolve() != destination.resolve():
        shutil.copy2(source, destination)
    return destination


def _colab_notebook_path_from_manifest(manifest_path: Path, manifest: dict[str, Any]) -> Path:
    notebook = manifest.get("notebook")
    if not isinstance(notebook, dict):
        raise ValueError("GVHMR Colab operator notebook manifest is missing notebook metadata")
    raw_path = notebook.get("path")
    if isinstance(raw_path, str) and raw_path:
        candidate = Path(raw_path)
        if candidate.exists():
            return candidate
    filename = notebook.get("filename")
    if isinstance(filename, str) and filename:
        candidate = manifest_path.parent / filename
        if candidate.exists():
            return candidate
    raise ValueError("GVHMR Colab operator notebook file does not exist")


def _write_operator_package_readme(path: Path, manifest: dict[str, Any]) -> None:
    archive = manifest["archive"]
    request = manifest["run_request"]
    notebook = manifest["colab_notebook"]
    lines = [
        "# neodojo GVHMR Operator Package",
        "",
        "This generated package collocates the files needed by an external GPU operator.",
        "It does not run GVHMR locally and does not include SMPL-X assets, checkpoints, raw GVHMR results, or returned motion artifacts.",
        "",
        "## Package Contents",
        "",
        f"- Archive: `{archive['package_path']}`",
        f"- Run request: `{request['package_manifest']}`",
        f"- Run request README: `{request['package_readme']}`",
        f"- Colab notebook: `{notebook['package_notebook']}`",
        f"- Colab manifest: `{notebook['package_manifest']}`",
        "",
        "## Status",
        "",
        f"- Status: `{manifest['status']}`",
        f"- Media included: `{str(manifest['media_included']).lower()}`",
        f"- Safe for git: `{str(manifest['policy']['safe_for_git']).lower()}`",
        f"- Expected return schema: `{manifest['expected_return_artifact']['schema']}`",
        "",
        "## Operator Steps",
        "",
        "1. Upload the archive and notebook to a private GPU notebook/runtime.",
        "2. Keep GVHMR checkpoints and licensed SMPL-X assets in private storage.",
        "3. Verify the archive checksum in the notebook before unpacking.",
        "4. Set `RUN_GVHMR = True` only after assets, checkpoints, and rights review are ready.",
        "5. Return `gvhmr-smplx-joints.json` to this local neodojo workspace.",
        "",
        "For a user-managed self-hosted GitHub Actions GPU runner, dispatch",
        "`.github/workflows/gvhmr-self-hosted-gpu.yml` with",
        "`gvhmr_operator_package_path` pointing at this package directory or `manifest.json`.",
        "",
        "After the returned JSON exists locally, run:",
        "",
        _markdown_command(manifest["commands"]["local_real_artifact_intake"]),
        _markdown_command(manifest["commands"]["local_strict_verify"]),
        "",
        "Media-containing operator packages are generated under ignored outputs and must not be committed or published.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_gvhmr_operator_package(
    out_dir: Path,
    *,
    gpu_input_archive: Path,
    gpu_run_request: Path,
    colab_notebook: Path,
) -> GvhmrOperatorPackageWriteResult:
    validate_output_dir(out_dir)
    archive_manifest_path, archive_manifest = _load_gpu_input_archive_manifest(gpu_input_archive)
    request_manifest_path, request_manifest = _load_gpu_run_request_manifest(gpu_run_request)
    colab_manifest_path, colab_manifest = _load_colab_operator_notebook_manifest(colab_notebook)

    archive_path = _archive_path_from_manifest(archive_manifest_path, archive_manifest)
    archive_sha = sha256_file(archive_path)
    expected_archive_sha = archive_manifest.get("archive", {}).get("sha256")
    if expected_archive_sha != archive_sha:
        raise ValueError("GVHMR GPU input archive checksum does not match its manifest")
    if request_manifest.get("archive", {}).get("sha256") != archive_sha:
        raise ValueError("GVHMR run request does not match the GPU input archive checksum")
    if colab_manifest.get("archive", {}).get("sha256") != archive_sha:
        raise ValueError("GVHMR Colab notebook does not match the GPU input archive checksum")
    if colab_manifest.get("gpu_run_request", {}).get("sha256") != sha256_file(request_manifest_path):
        raise ValueError("GVHMR Colab notebook does not match the GPU run request checksum")

    media_included = bool(archive_manifest.get("media_included"))
    if bool(request_manifest.get("media_included")) != media_included:
        raise ValueError("GVHMR run request media flag does not match the archive")
    if bool(colab_manifest.get("media_included")) != media_included:
        raise ValueError("GVHMR Colab notebook media flag does not match the archive")

    request_readme_path = request_manifest_path.parent / "README.md"
    if not request_readme_path.exists():
        raise ValueError(f"GVHMR run request README does not exist: {request_readme_path}")
    notebook_path = _colab_notebook_path_from_manifest(colab_manifest_path, colab_manifest)
    if colab_manifest.get("notebook", {}).get("sha256") != sha256_file(notebook_path):
        raise ValueError("GVHMR Colab notebook checksum does not match its manifest")

    out_dir.mkdir(parents=True, exist_ok=True)
    archive_copy = _copy_operator_package_file(archive_path, out_dir / "archive")
    request_manifest_copy = _copy_operator_package_file(request_manifest_path, out_dir / "request")
    request_readme_copy = _copy_operator_package_file(request_readme_path, out_dir / "request")
    colab_manifest_copy = _copy_operator_package_file(colab_manifest_path, out_dir / "colab")
    colab_notebook_copy = _copy_operator_package_file(notebook_path, out_dir / "colab")
    manifest_path = out_dir / "manifest.json"
    readme_path = out_dir / "README.md"

    status = "ready_for_external_gpu_operator_package" if media_included else "metadata_only_not_ready_for_gpu"
    manifest = {
        "schema": GVHMR_OPERATOR_PACKAGE_SCHEMA,
        "status": status,
        "blocked_locally": True,
        "media_included": media_included,
        "source": archive_manifest.get("source"),
        "trim": archive_manifest.get("trim"),
        "archive": {
            "source_manifest": _as_posix(archive_manifest_path),
            "source_path": _as_posix(archive_path),
            "package_path": _as_posix(archive_copy),
            "filename": archive_copy.name,
            "sha256": sha256_file(archive_copy),
            "size_bytes": archive_copy.stat().st_size,
            "safe_for_git": archive_manifest.get("policy", {}).get("safe_for_git"),
        },
        "run_request": {
            "source_manifest": _as_posix(request_manifest_path),
            "package_manifest": _as_posix(request_manifest_copy),
            "package_readme": _as_posix(request_readme_copy),
            "schema": request_manifest.get("schema"),
            "status": request_manifest.get("status"),
            "sha256": sha256_file(request_manifest_copy),
        },
        "colab_notebook": {
            "source_manifest": _as_posix(colab_manifest_path),
            "source_notebook": _as_posix(notebook_path),
            "package_manifest": _as_posix(colab_manifest_copy),
            "package_notebook": _as_posix(colab_notebook_copy),
            "schema": colab_manifest.get("schema"),
            "status": colab_manifest.get("status"),
            "sha256": sha256_file(colab_notebook_copy),
        },
        "expected_return_artifact": request_manifest.get("expected_return_artifact"),
        "commands": request_manifest.get("commands"),
        "policy": {
            "safe_for_git": not media_included,
            "notes": (
                "This package is safe to commit only when media_included is false. "
                "Media-containing archives, notebooks derived from them, checkpoints, "
                "SMPL-X assets, logs, and returned GVHMR artifacts stay ignored."
            ),
        },
        "notes": (
            "This package collocates the external GPU archive, run request, and Colab notebook; "
            "it does not run GVHMR locally."
        ),
    }
    _write_json(manifest_path, manifest)
    _write_operator_package_readme(readme_path, manifest)
    checked_paths = [
        manifest_path,
        readme_path,
        archive_copy,
        request_manifest_copy,
        request_readme_copy,
        colab_manifest_copy,
        colab_notebook_copy,
        archive_manifest_path,
        request_manifest_path,
        colab_manifest_path,
    ]
    return GvhmrOperatorPackageWriteResult(
        manifest_path=manifest_path,
        readme_path=readme_path,
        checked_paths=checked_paths,
        status=status,
    )


def validate_gvhmr_operator_package(operator_package: Path) -> GvhmrOperatorPackageValidationResult:
    manifest_path, package_manifest = _load_operator_package_manifest(operator_package)
    package_dir = manifest_path.parent
    archive_name = str(package_manifest.get("archive", {}).get("filename") or "neodojo-gvhmr-gpu-input.tar.gz")
    if Path(archive_name).name != archive_name:
        raise ValueError("GVHMR operator package archive filename must be a simple filename")
    archive_path = package_dir / "archive" / archive_name
    request_manifest_path = package_dir / "request" / "manifest.json"
    request_readme_path = package_dir / "request" / "README.md"
    colab_manifest_path = package_dir / "colab" / "manifest.json"
    colab_notebook_path = package_dir / "colab" / "gvhmr-colab-operator.ipynb"
    package_readme_path = package_dir / "README.md"

    required_files = [
        archive_path,
        request_manifest_path,
        request_readme_path,
        colab_manifest_path,
        colab_notebook_path,
        package_readme_path,
    ]
    for path in required_files:
        if not path.exists():
            raise ValueError(f"GVHMR operator package file is missing: {path}")

    request_manifest = _load_json_object(request_manifest_path, "GVHMR operator package run request manifest")
    colab_manifest = _load_json_object(colab_manifest_path, "GVHMR operator package Colab manifest")
    require_schema(request_manifest, GVHMR_GPU_RUN_REQUEST_SCHEMA, "GVHMR operator package run request manifest")
    require_schema(colab_manifest, GVHMR_COLAB_OPERATOR_NOTEBOOK_SCHEMA, "GVHMR operator package Colab manifest")

    archive_sha = sha256_file(archive_path)
    if package_manifest.get("archive", {}).get("sha256") != archive_sha:
        raise ValueError("GVHMR operator package archive checksum does not match manifest")
    if request_manifest.get("archive", {}).get("sha256") != archive_sha:
        raise ValueError("GVHMR operator package run request archive checksum does not match package archive")
    if colab_manifest.get("archive", {}).get("sha256") != archive_sha:
        raise ValueError("GVHMR operator package Colab archive checksum does not match package archive")
    if package_manifest.get("run_request", {}).get("sha256") != sha256_file(request_manifest_path):
        raise ValueError("GVHMR operator package run-request checksum does not match copied request manifest")
    if colab_manifest.get("gpu_run_request", {}).get("sha256") != sha256_file(request_manifest_path):
        raise ValueError("GVHMR operator package Colab manifest does not match copied request manifest")
    if package_manifest.get("colab_notebook", {}).get("sha256") != sha256_file(colab_notebook_path):
        raise ValueError("GVHMR operator package Colab notebook checksum does not match package manifest")
    if colab_manifest.get("notebook", {}).get("sha256") != sha256_file(colab_notebook_path):
        raise ValueError("GVHMR operator package Colab notebook checksum does not match Colab manifest")

    media_included = bool(package_manifest.get("media_included"))
    if bool(request_manifest.get("media_included")) != media_included:
        raise ValueError("GVHMR operator package run request media flag does not match package")
    if bool(colab_manifest.get("media_included")) != media_included:
        raise ValueError("GVHMR operator package Colab media flag does not match package")
    expected_return = package_manifest.get("expected_return_artifact") or {}
    expected_schema = expected_return.get("schema")
    if expected_schema != GVHMR_JOINT_EXPORT_SCHEMA:
        raise ValueError("GVHMR operator package expected return schema is not neodojo.gvhmr_smplx_joints.v1")

    checked_paths = [manifest_path, *required_files]
    return GvhmrOperatorPackageValidationResult(
        manifest_path=manifest_path,
        checked_paths=checked_paths,
        status=str(package_manifest.get("status", "unknown")),
    )


def _iter_operator_package_files(package_dir: Path, *, archive_output_dir: Path) -> list[tuple[Path, str]]:
    package_root = package_dir.resolve()
    archive_root = archive_output_dir.resolve()
    files: list[tuple[Path, str]] = []
    for path in sorted(package_dir.rglob("*")):
        if not path.is_file():
            continue
        resolved = path.resolve()
        if archive_root != package_root and archive_root in resolved.parents:
            continue
        arcname = _as_posix(resolved.relative_to(package_root))
        files.append((path, arcname))
    if not files:
        raise ValueError(f"GVHMR operator package has no files to archive: {package_dir}")
    return files


def archive_gvhmr_operator_package(
    out_dir: Path,
    *,
    operator_package: Path,
    archive_name: str = "neodojo-gvhmr-operator-package.tar.gz",
) -> GvhmrOperatorPackageArchiveWriteResult:
    validate_output_dir(out_dir)
    if not archive_name.endswith((".tar.gz", ".tgz")):
        raise ValueError("GVHMR operator package archive name must end with .tar.gz or .tgz")
    if Path(archive_name).name != archive_name:
        raise ValueError("GVHMR operator package archive name must be a simple filename")

    validation = validate_gvhmr_operator_package(operator_package)
    package_manifest_path, package_manifest = _load_operator_package_manifest(operator_package)
    package_dir = package_manifest_path.parent
    media_included = bool(package_manifest.get("media_included"))
    out_dir.mkdir(parents=True, exist_ok=True)
    archive_path = out_dir / archive_name
    files = _iter_operator_package_files(package_dir, archive_output_dir=out_dir)
    with tarfile.open(archive_path, "w:gz") as archive:
        for source_path, arcname in files:
            archive.add(source_path, arcname=arcname, recursive=False)
    members = [
        {
            "path": arcname,
            "sha256": sha256_file(source_path),
            "size_bytes": source_path.stat().st_size,
        }
        for source_path, arcname in files
    ]
    status = (
        "ready_for_external_gpu_operator_package_archive"
        if media_included
        else "metadata_only_not_ready_for_gpu"
    )
    manifest_path = out_dir / "manifest.json"
    manifest = {
        "schema": GVHMR_OPERATOR_PACKAGE_ARCHIVE_SCHEMA,
        "status": status,
        "blocked_locally": True,
        "media_included": media_included,
        "source": package_manifest.get("source"),
        "trim": package_manifest.get("trim"),
        "source_operator_package": {
            "manifest": _as_posix(package_manifest_path),
            "schema": package_manifest.get("schema"),
            "status": package_manifest.get("status"),
            "sha256": sha256_file(package_manifest_path),
        },
        "archive": {
            "path": _as_posix(archive_path),
            "filename": archive_path.name,
            "sha256": sha256_file(archive_path),
            "size_bytes": archive_path.stat().st_size,
            "member_count": len(members),
        },
        "members": members,
        "expected_return_artifact": package_manifest.get("expected_return_artifact"),
        "commands": package_manifest.get("commands"),
        "policy": {
            "safe_for_git": not media_included,
            "notes": (
                "Metadata-only operator package archives are CI-safe. Media-containing "
                "operator package archives must stay ignored and must not be committed or "
                "uploaded as public artifacts."
            ),
        },
        "notes": (
            "This archive wraps the validated GVHMR operator package directory as one "
            "copyable handoff file. It does not run GVHMR locally."
        ),
    }
    _write_json(manifest_path, manifest)
    checked_paths = [manifest_path, archive_path, *validation.checked_paths]
    return GvhmrOperatorPackageArchiveWriteResult(
        manifest_path=manifest_path,
        archive_path=archive_path,
        checked_paths=checked_paths,
        status=status,
    )


def _operator_package_archive_path_from_manifest(manifest_path: Path, manifest: dict[str, Any]) -> Path:
    archive = manifest.get("archive")
    if not isinstance(archive, dict):
        raise ValueError("GVHMR operator package archive manifest is missing archive metadata")
    filename = archive.get("filename")
    if not isinstance(filename, str) or not filename:
        raise ValueError("GVHMR operator package archive manifest is missing archive filename")
    if Path(filename).name != filename:
        raise ValueError("GVHMR operator package archive filename must be a simple filename")
    candidate = manifest_path.parent / filename
    if candidate.exists():
        return candidate
    raw_path = archive.get("path")
    if isinstance(raw_path, str) and raw_path:
        candidate = Path(raw_path)
        if candidate.exists():
            return candidate
    raise ValueError("GVHMR operator package archive file does not exist")


def _validate_archive_member_name(name: str, *, label: str) -> None:
    if not name:
        raise ValueError(f"{label} member path is empty")
    if "\\" in name:
        raise ValueError(f"{label} member path must use POSIX separators: {name}")
    if name.startswith("/"):
        raise ValueError(f"Unsafe archive member path: {name}")
    parts = name.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"Unsafe archive member path: {name}")


def _operator_package_archive_manifest_members(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    members = manifest.get("members")
    if not isinstance(members, list) or not members:
        raise ValueError("GVHMR operator package archive manifest is missing members")
    expected_members: dict[str, dict[str, Any]] = {}
    for member in members:
        if not isinstance(member, dict):
            raise ValueError("GVHMR operator package archive member metadata must be objects")
        name = member.get("path")
        if not isinstance(name, str):
            raise ValueError("GVHMR operator package archive member is missing a path")
        _validate_archive_member_name(name, label="GVHMR operator package archive")
        if name in expected_members:
            raise ValueError(f"GVHMR operator package archive manifest has duplicate member: {name}")
        sha256 = member.get("sha256")
        if not isinstance(sha256, str) or len(sha256) != 64:
            raise ValueError(f"GVHMR operator package archive member checksum is invalid: {name}")
        size_bytes = member.get("size_bytes")
        if not isinstance(size_bytes, int) or size_bytes < 0:
            raise ValueError(f"GVHMR operator package archive member size is invalid: {name}")
        expected_members[name] = member
    return expected_members


def _sha256_tar_member(archive: tarfile.TarFile, member: tarfile.TarInfo) -> str:
    extracted = archive.extractfile(member)
    if extracted is None:
        raise ValueError(f"GVHMR operator package archive member is not readable: {member.name}")
    digest = hashlib.sha256()
    with extracted:
        for chunk in iter(lambda: extracted.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_operator_package_archive_tar(archive_path: Path, manifest: dict[str, Any]) -> set[str]:
    expected_members = _operator_package_archive_manifest_members(manifest)
    seen: set[str] = set()
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            _validate_archive_member_name(member.name, label="GVHMR operator package archive")
            if member.name in seen:
                raise ValueError(f"GVHMR operator package archive has duplicate member: {member.name}")
            if not member.isfile():
                raise ValueError(f"GVHMR operator package archive member must be a regular file: {member.name}")
            expected = expected_members.get(member.name)
            if expected is None:
                raise ValueError(f"GVHMR operator package archive has unexpected member: {member.name}")
            expected_size = expected.get("size_bytes")
            if expected_size != member.size:
                raise ValueError(f"GVHMR operator package archive member size mismatch: {member.name}")
            expected_sha = expected.get("sha256")
            actual_sha = _sha256_tar_member(archive, member)
            if expected_sha != actual_sha:
                raise ValueError(f"GVHMR operator package archive member checksum mismatch: {member.name}")
            seen.add(member.name)

    missing = sorted(set(expected_members) - seen)
    if missing:
        raise ValueError("GVHMR operator package archive is missing manifest members: " + ", ".join(missing))

    archive = manifest.get("archive")
    expected_count = archive.get("member_count") if isinstance(archive, dict) else None
    if expected_count != len(seen):
        raise ValueError("GVHMR operator package archive member count does not match manifest")

    required = {
        "manifest.json",
        "README.md",
        "request/manifest.json",
        "request/README.md",
        "colab/manifest.json",
        "colab/gvhmr-colab-operator.ipynb",
    }
    missing_required = sorted(required - seen)
    if missing_required:
        raise ValueError(
            "GVHMR operator package archive is missing required package files: "
            + ", ".join(missing_required)
        )
    package_archive_members = sorted(
        name for name in seen if name.startswith("archive/") and name.endswith((".tar.gz", ".tgz"))
    )
    if len(package_archive_members) != 1:
        raise ValueError("GVHMR operator package archive must contain exactly one nested GPU input archive")

    source_package = manifest.get("source_operator_package")
    expected_package_manifest_sha = (
        source_package.get("sha256") if isinstance(source_package, dict) else None
    )
    if expected_package_manifest_sha != expected_members["manifest.json"].get("sha256"):
        raise ValueError("GVHMR operator package archive source package checksum does not match manifest member")
    return seen


def _extract_validated_operator_package_archive(archive_path: Path, destination: Path, members: set[str]) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    destination_root = destination.resolve()
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            if member.name not in members:
                raise ValueError(f"GVHMR operator package archive has unexpected member: {member.name}")
            member_path = (destination_root / member.name).resolve()
            if member_path != destination_root and destination_root not in member_path.parents:
                raise ValueError(f"Unsafe archive member path: {member.name}")
            archive.extract(member, path=destination_root)


def validate_gvhmr_operator_package_archive(
    operator_package_archive: Path,
) -> GvhmrOperatorPackageArchiveValidationResult:
    manifest_path, archive_manifest = _load_operator_package_archive_manifest(operator_package_archive)
    archive_path = _operator_package_archive_path_from_manifest(manifest_path, archive_manifest)
    archive_sha = sha256_file(archive_path)
    expected_archive_sha = archive_manifest.get("archive", {}).get("sha256")
    if expected_archive_sha != archive_sha:
        raise ValueError("GVHMR operator package archive checksum does not match manifest")
    expected_archive_size = archive_manifest.get("archive", {}).get("size_bytes")
    if expected_archive_size != archive_path.stat().st_size:
        raise ValueError("GVHMR operator package archive size does not match manifest")

    members = _validate_operator_package_archive_tar(archive_path, archive_manifest)
    with tempfile.TemporaryDirectory(prefix="neodojo-operator-package-archive-") as temp_dir:
        package_dir = Path(temp_dir) / "operator-package"
        _extract_validated_operator_package_archive(archive_path, package_dir, members)
        package_manifest_path, package_manifest = _load_operator_package_manifest(package_dir)
        package_validation = validate_gvhmr_operator_package(package_manifest_path)

        source_package = archive_manifest.get("source_operator_package")
        expected_source_status = source_package.get("status") if isinstance(source_package, dict) else None
        if expected_source_status != package_validation.status:
            raise ValueError("GVHMR operator package archive source package status does not match extracted package")
        if bool(archive_manifest.get("media_included")) != bool(package_manifest.get("media_included")):
            raise ValueError("GVHMR operator package archive media flag does not match extracted package")
        expected_return = archive_manifest.get("expected_return_artifact") or {}
        package_expected_return = package_manifest.get("expected_return_artifact") or {}
        if expected_return.get("schema") != package_expected_return.get("schema"):
            raise ValueError("GVHMR operator package archive expected return schema does not match extracted package")

    return GvhmrOperatorPackageArchiveValidationResult(
        manifest_path=manifest_path,
        archive_path=archive_path,
        checked_paths=[manifest_path, archive_path],
        status=str(archive_manifest.get("status", "unknown")),
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


def _relative_to_out_dir(path: Path | None, out_dir: Path) -> str | None:
    if path is None:
        return None
    try:
        return _as_posix(path.relative_to(out_dir))
    except ValueError:
        return _as_posix(path)


def _audit_json_schema(path: Path, schema: str, label: str) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, f"{label} does not exist"
    try:
        payload = _load_json_object(path, label)
        require_schema(payload, schema, label)
    except ValueError as exc:
        return None, str(exc)
    return payload, None


def _audit_add_check(
    checks: list[dict[str, Any]],
    *,
    name: str,
    passed: bool,
    message: str,
    required: bool = True,
    path: Path | None = None,
) -> None:
    checks.append(
        {
            "name": name,
            "passed": passed,
            "required": required,
            "message": message,
            "path": _as_posix(path) if path is not None else None,
        }
    )


def audit_real_conversion_completion(
    out_dir: Path,
    *,
    source_materialization: Path = Path("outputs/real-conversion-source/source-materialization.json"),
    gvhmr_json: Path = Path("outputs/real-conversion-gate/gvhmr-smplx-joints.json"),
    real_demo: Path = Path("outputs/real-demo"),
    env: Mapping[str, str] | None = None,
    command_lookup: Callable[[str], str | None] | None = None,
    command_runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] | None = None,
    github_repo: str | None = None,
) -> RealConversionCompletionAuditWriteResult:
    """Write an executable audit of the remaining real GVHMR conversion gate."""

    validate_output_dir(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    checks: list[dict[str, Any]] = []
    checked_paths: list[Path] = []

    probe = probe_gpu_execution_environment(
        out_dir / "gpu-execution-probe",
        env=env,
        command_lookup=command_lookup,
        command_runner=command_runner,
        github_repo=github_repo,
    )
    checked_paths.append(probe.manifest_path)
    gpu_route_visible = probe.status != "external_gpu_artifact_missing"
    _audit_add_check(
        checks,
        name="gpu_execution_route_visible",
        passed=gpu_route_visible,
        required=False,
        path=probe.manifest_path,
        message=(
            "A possible GPU execution route is visible."
            if gpu_route_visible
            else (
                "No local CUDA runtime, Docker GPU runtime, configured provider, "
                "or optional GitHub self-hosted GPU runner was detected."
            )
        ),
    )

    materialization, materialization_error = _audit_json_schema(
        source_materialization,
        SOURCE_MATERIALIZATION_SCHEMA,
        "source materialization manifest",
    )
    if materialization is not None:
        checked_paths.append(source_materialization)
    _audit_add_check(
        checks,
        name="source_materialization_available",
        passed=materialization is not None,
        path=source_materialization,
        message=materialization_error or "Source materialization manifest is present and schema-valid.",
    )
    source_materialization_fixture_only = bool(
        materialization.get("fixture_only") if materialization is not None else False
    )

    gvhmr_export, gvhmr_error = _audit_json_schema(
        gvhmr_json,
        GVHMR_JOINT_EXPORT_SCHEMA,
        "GVHMR SMPL-X export",
    )
    if gvhmr_export is not None:
        checked_paths.append(gvhmr_json)
    frames = gvhmr_export.get("frames", gvhmr_export.get("smplx_joints")) if gvhmr_export else None
    frame_count = len(frames) if isinstance(frames, list) else None
    gvhmr_export_fixture_only = bool(gvhmr_export.get("fixture_only") if gvhmr_export is not None else False)
    _audit_add_check(
        checks,
        name="gvhmr_export_available",
        passed=gvhmr_export is not None,
        path=gvhmr_json,
        message=gvhmr_error or "GVHMR export is present and schema-valid.",
    )
    _audit_add_check(
        checks,
        name="gvhmr_export_non_fixture",
        passed=gvhmr_export is not None and not gvhmr_export_fixture_only,
        path=gvhmr_json,
        message=(
            "GVHMR export is not marked fixture-only."
            if gvhmr_export is not None and not gvhmr_export_fixture_only
            else "No non-fixture returned GVHMR export is available."
        ),
    )

    validation_status = None
    validation_report_path = None
    if materialization is not None and gvhmr_export is not None:
        validation = validate_gvhmr_source(
            out_dir / "source-validation",
            source_materialization=source_materialization,
            gvhmr_json=gvhmr_json,
        )
        validation_status = validation.status
        validation_report_path = validation.report_path
        checked_paths.append(validation.report_path)
        if validation.validated_export_path is not None:
            checked_paths.append(validation.validated_export_path)
        _audit_add_check(
            checks,
            name="source_validation_passed",
            passed=validation.status == "validated",
            path=validation.report_path,
            message=f"GVHMR source validation status is {validation.status}.",
        )

    real_demo_manifest = real_demo if real_demo.suffix == ".json" else real_demo / "manifest.json"
    real_demo_payload, real_demo_error = _audit_json_schema(
        real_demo_manifest,
        "neodojo.real_conversion_demo.v1",
        "real conversion demo manifest",
    )
    if real_demo_payload is not None:
        checked_paths.append(real_demo_manifest)
    real_demo_imported = bool(real_demo_payload.get("real_gvhmr_artifact_imported")) if real_demo_payload else False
    public_demo_ref = real_demo_payload.get("public_demo") if real_demo_payload else None
    public_demo_manifest = (
        real_demo_manifest.parent / public_demo_ref
        if isinstance(public_demo_ref, str) and public_demo_ref
        else real_demo_manifest.parent / "public-demo" / "manifest.json"
    )
    public_demo_available = public_demo_manifest.exists()
    if public_demo_available:
        checked_paths.append(public_demo_manifest)
    _audit_add_check(
        checks,
        name="real_demo_manifest_imported_real_artifact",
        passed=real_demo_imported,
        path=real_demo_manifest,
        message=(
            "Real-demo manifest confirms a real non-fixture GVHMR artifact import."
            if real_demo_imported
            else real_demo_error or "Real-demo manifest does not confirm a real non-fixture GVHMR artifact import."
        ),
    )
    _audit_add_check(
        checks,
        name="real_demo_public_demo_available",
        passed=real_demo_imported and public_demo_available,
        path=public_demo_manifest,
        message=(
            "Real-demo public-demo manifest is available."
            if real_demo_imported and public_demo_available
            else "No verified public-demo manifest exists for a real GVHMR artifact."
        ),
    )

    complete = real_demo_imported and public_demo_available
    if complete:
        status = "real_demo_verified"
        next_action = "Inspect outputs/real-demo/public-demo and archive the real conversion evidence outside git."
    elif gvhmr_export is None:
        status = "external_gpu_artifact_missing" if not gpu_route_visible else "real_artifact_missing"
        next_action = (
            "Run GVHMR on a GPU-capable machine and return a neodojo.gvhmr_smplx_joints.v1 export."
        )
    elif materialization is None:
        status = "source_materialization_missing"
        next_action = "Create or point to the matching source-materialization.json for the returned GVHMR export."
    elif gvhmr_export_fixture_only or source_materialization_fixture_only:
        status = "fixture_artifact_only"
        next_action = "Use a non-fixture source materialization and returned GVHMR export for the real gate."
    elif validation_status != "validated":
        status = "real_artifact_validation_failed"
        next_action = "Inspect the source-validation report and classify the mismatch before changing contracts."
    else:
        status = "real_artifact_ready_for_import"
        next_action = "Run make real-artifact-intake or make demo-real with the validated returned export."

    manifest = {
        "schema": REAL_CONVERSION_AUDIT_SCHEMA,
        "status": status,
        "complete": complete,
        "blocked": not complete,
        "inputs": {
            "source_materialization": _as_posix(source_materialization),
            "gvhmr_json": _as_posix(gvhmr_json),
            "real_demo": _as_posix(real_demo),
        },
        "gpu_execution_probe": {
            "manifest": _relative_to_out_dir(probe.manifest_path, out_dir),
            "status": probe.status,
            "route_visible": gpu_route_visible,
        },
        "artifact": {
            "source_materialization_fixture_only": source_materialization_fixture_only,
            "gvhmr_export_fixture_only": gvhmr_export_fixture_only,
            "frame_count": frame_count,
            "validation_status": validation_status,
            "validation_report": _relative_to_out_dir(validation_report_path, out_dir),
        },
        "real_demo": {
            "manifest": _as_posix(real_demo_manifest),
            "exists": real_demo_payload is not None,
            "real_gvhmr_artifact_imported": real_demo_imported,
            "public_demo_manifest": _as_posix(public_demo_manifest),
            "public_demo_manifest_exists": public_demo_available,
        },
        "checks": checks,
        "next_action": next_action,
        "notes": (
            "This audit is a blocker classifier. It may pass local verification "
            "while status is not complete, because the remaining GVHMR run is "
            "external to the local CPU workspace."
        ),
    }
    _write_json(manifest_path, manifest)
    checked_paths.append(manifest_path)
    return RealConversionCompletionAuditWriteResult(
        manifest_path=manifest_path,
        status=status,
        complete=complete,
        checked_paths=list(dict.fromkeys(checked_paths)),
    )


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
    local_source_id: str | None = None,
    local_title_english: str | None = None,
    local_title_chinese: str | None = None,
    local_category: str = "local_user_supplied",
    local_category_chinese: str = "local/user-supplied",
    local_origin_url: str | None = None,
    start_seconds: float = 0.0,
    end_seconds: float = 12.0,
    rights_notes: str = "licensing unconfirmed; use local/user-supplied source before GPU run",
) -> RealConversionPrepWriteResult:
    validate_output_dir(out_dir)
    if local_source_id is not None:
        if local_video is None:
            raise ValueError("--local-source-id requires --local-video")
        row, local_source = _local_source_row(
            local_video=local_video,
            source_id=local_source_id,
            title_english=local_title_english,
            title_chinese=local_title_chinese,
            category=local_category,
            category_chinese=local_category_chinese,
            origin_url=local_origin_url,
        )
        manifest_source_id = local_source["id"]
        source_kind = local_source["source_kind"]
    else:
        row = _load_source_row(source_index, source_id)
        manifest_source_id = source_id
        source_kind = "official_source_index"
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
            "id": manifest_source_id,
            "source_kind": source_kind,
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
            "download_source_dry_run": None
            if local_source_id is not None
            else f"./video/download_originals.py --id {source_id} --dry-run",
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
