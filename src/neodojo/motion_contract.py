from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .fixtures import (
    FIXTURE_FORM,
    FIXTURE_FPS,
    FIXTURE_JOINT_SET,
    FIXTURE_ROUTINE,
    build_smplx_fixture_frames,
)

MOTION_RECORD_SCHEMA = "neodojo.motion_record.v1"
TRACK_SCHEMA = "neodojo.track.v1"


@dataclass(frozen=True)
class MotionContractWriteResult:
    out_dir: Path
    motion_record_manifest_path: Path
    motion_record_data_path: Path
    smplx_track_manifest_path: Path
    smplx_track_data_path: Path


def _write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _relative_path(path: Path, start: Path) -> str:
    return os.path.relpath(path, start).replace(os.sep, "/")


def validate_output_dir(out_dir: Path, repo_root: Path | None = None) -> None:
    repo = (repo_root or Path.cwd()).resolve()
    resolved = out_dir.resolve(strict=False)
    if not _is_relative_to(resolved, repo):
        return

    relative = resolved.relative_to(repo)
    if relative.parts and relative.parts[0] == "outputs":
        return

    raise ValueError("output path inside this repo must be under outputs/")


def validate_scoring_source(track_manifests: dict[str, dict[str, Any]], scoring_source: str = "smplx") -> None:
    if scoring_source != "smplx":
        raise ValueError("SMPL-X is the only allowed scoring source")

    scoring_track = track_manifests.get(scoring_source)
    if not scoring_track:
        raise ValueError("missing SMPL-X scoring track")
    if not scoring_track.get("scoring_allowed"):
        raise ValueError("SMPL-X track must allow scoring")

    for track_id, manifest in track_manifests.items():
        if track_id != "smplx" and manifest.get("scoring_allowed"):
            raise ValueError("derived visual tracks cannot allow scoring")


def write_fixture_motion_contract(out_dir: Path, frame_count: int = 96) -> MotionContractWriteResult:
    validate_output_dir(out_dir)

    frames = build_smplx_fixture_frames(frame_count)
    motion_dir = out_dir / "motion-record"
    track_dir = out_dir / "tracks" / "smplx"
    motion_data_path = motion_dir / "smplx-joints.json"
    motion_manifest_path = motion_dir / "manifest.json"
    track_data_path = track_dir / "joints.json"
    track_manifest_path = track_dir / "manifest.json"

    motion_data = {
        "frames": frames,
        "joint_set": FIXTURE_JOINT_SET,
        "track_id": "smplx",
    }
    track_data = {
        "frames": frames,
        "joint_set": FIXTURE_JOINT_SET,
        "track_id": "smplx",
    }

    motion_manifest = {
        "schema": MOTION_RECORD_SCHEMA,
        "fixture_only": True,
        "source_type": "synthetic_fixture",
        "routine": FIXTURE_ROUTINE,
        "form": FIXTURE_FORM,
        "fps": FIXTURE_FPS,
        "frame_count": len(frames),
        "joint_set": FIXTURE_JOINT_SET,
        "scoring_source": "smplx",
        "provenance": {
            "generator": "neodojo.fixtures.build_smplx_fixture_frames",
            "accuracy_role": "plumbing fixture only; not qigong teaching evidence",
        },
        "data_files": {
            "smplx_frames": _relative_path(motion_data_path, motion_manifest_path.parent),
        },
    }
    track_manifest = {
        "schema": TRACK_SCHEMA,
        "track_id": "smplx",
        "fixture_only": True,
        "source_motion_record": _relative_path(motion_manifest_path, track_manifest_path.parent),
        "role": "teaching accuracy source",
        "scoring_allowed": True,
        "fps": FIXTURE_FPS,
        "frame_count": len(frames),
        "joint_set": FIXTURE_JOINT_SET,
        "data_files": {
            "frames": _relative_path(track_data_path, track_manifest_path.parent),
        },
    }

    validate_scoring_source({"smplx": track_manifest}, scoring_source=motion_manifest["scoring_source"])

    _write_json(motion_data_path, motion_data)
    _write_json(motion_manifest_path, motion_manifest)
    _write_json(track_data_path, track_data)
    _write_json(track_manifest_path, track_manifest)

    return MotionContractWriteResult(
        out_dir=out_dir,
        motion_record_manifest_path=motion_manifest_path,
        motion_record_data_path=motion_data_path,
        smplx_track_manifest_path=track_manifest_path,
        smplx_track_data_path=track_data_path,
    )


def resolve_motion_record_manifest(motion_record: Path) -> Path:
    if motion_record.is_file():
        return motion_record

    candidates = [
        motion_record / "motion-record" / "manifest.json",
        motion_record / "manifest.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise ValueError(f"could not find a motion-record manifest under {motion_record}")


def load_motion_record_frames(motion_manifest_path: Path) -> tuple[dict[str, Any], list[dict[str, list[float]]]]:
    manifest = json.loads(motion_manifest_path.read_text(encoding="utf-8"))
    if manifest.get("scoring_source") != "smplx":
        raise ValueError("motion record must keep SMPL-X as scoring_source")

    data_file = manifest.get("data_files", {}).get("smplx_frames")
    if not data_file:
        raise ValueError("motion-record manifest is missing data_files.smplx_frames")

    data_path = motion_manifest_path.parent / data_file
    data = json.loads(data_path.read_text(encoding="utf-8"))
    frames = data.get("frames")
    if not isinstance(frames, list) or len(frames) < 8:
        raise ValueError("motion-record data must contain at least 8 SMPL-X frames")
    return manifest, frames


def load_track_frames(track_manifest_path: Path) -> list[dict[str, list[float]]]:
    manifest = json.loads(track_manifest_path.read_text(encoding="utf-8"))
    if manifest.get("track_id") != "smplx":
        raise ValueError("only SMPL-X teaching tracks are supported in the local motion contract")
    if not manifest.get("scoring_allowed"):
        raise ValueError("SMPL-X teaching track must allow scoring")

    data_file = manifest.get("data_files", {}).get("frames")
    if not data_file:
        raise ValueError("track manifest is missing data_files.frames")

    data_path = track_manifest_path.parent / data_file
    data = json.loads(data_path.read_text(encoding="utf-8"))
    frames = data.get("frames")
    if not isinstance(frames, list) or len(frames) < 8:
        raise ValueError("track data must contain at least 8 frames")
    return frames
