from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import require_schema, sha256_file
from .fixtures import BONES
from .motion_contract import (
    _relative_path,
    _write_json,
    load_motion_record_frames,
    resolve_motion_record_manifest,
    SMPLX_PARAMETER_SCHEMA,
    validate_output_dir,
)

SMPLX_SURFACE_PROXY_SCHEMA = "neodojo.smplx_surface_proxy.v1"
SMPLX_ASSET_DESCRIPTOR_SCHEMA = "neodojo.smplx_asset_descriptor.v1"
SMPLX_MESH_FRAMES_SCHEMA = "neodojo.smplx_mesh_frames.v1"
SMPLX_MESH_SURFACE_SCHEMA = "neodojo.smplx_mesh_surface.v1"
SMPLX_MESH_VALIDATION_SCHEMA = "neodojo.smplx_mesh_validation.v1"

_SURFACE_RADII_M = {
    ("pelvis", "spine"): 0.105,
    ("spine", "neck"): 0.095,
    ("neck", "head"): 0.07,
    ("spine", "left_hip"): 0.085,
    ("spine", "right_hip"): 0.085,
    ("left_hip", "left_knee"): 0.06,
    ("right_hip", "right_knee"): 0.06,
    ("left_knee", "left_ankle"): 0.045,
    ("right_knee", "right_ankle"): 0.045,
    ("neck", "left_shoulder"): 0.055,
    ("neck", "right_shoulder"): 0.055,
    ("left_shoulder", "left_elbow"): 0.045,
    ("right_shoulder", "right_elbow"): 0.045,
    ("left_elbow", "left_wrist"): 0.035,
    ("right_elbow", "right_wrist"): 0.035,
}


@dataclass(frozen=True)
class SMPLXSurfaceProxyWriteResult:
    manifest_path: Path
    data_path: Path


@dataclass(frozen=True)
class SMPLXAssetDescriptorWriteResult:
    descriptor_path: Path


@dataclass(frozen=True)
class SMPLXMeshSurfaceWriteResult:
    manifest_path: Path
    data_path: Path
    validation_path: Path


def _radius_for_bone(start: str, end: str) -> float:
    return _SURFACE_RADII_M.get((start, end), _SURFACE_RADII_M.get((end, start), 0.04))


def _surface_frame(frame: dict[str, list[float]]) -> dict[str, Any]:
    capsules = []
    for start, end in BONES:
        if start not in frame or end not in frame:
            continue
        capsules.append(
            {
                "kind": "capsule",
                "start_joint": start,
                "end_joint": end,
                "start": frame[start],
                "end": frame[end],
                "radius_m": _radius_for_bone(start, end),
            }
        )
    return {"capsules": capsules}


def write_smplx_surface_proxy(out_dir: Path, motion_record: Path) -> SMPLXSurfaceProxyWriteResult:
    validate_output_dir(out_dir)
    motion_manifest_path = resolve_motion_record_manifest(motion_record)
    motion_manifest, smplx_frames = load_motion_record_frames(motion_manifest_path)

    surface_dir = out_dir / "surfaces" / "smplx"
    data_path = surface_dir / "surface-proxy.json"
    manifest_path = surface_dir / "manifest.json"
    frames = [_surface_frame(frame) for frame in smplx_frames]

    data = {
        "schema": SMPLX_SURFACE_PROXY_SCHEMA,
        "track_id": "smplx",
        "surface_kind": "joint_capsule_proxy",
        "frames": frames,
    }
    manifest = {
        "schema": SMPLX_SURFACE_PROXY_SCHEMA,
        "track_id": "smplx",
        "fixture_only": bool(motion_manifest.get("fixture_only", False)),
        "source_motion_record": _relative_path(motion_manifest_path, manifest_path.parent),
        "role": "SMPL-X body surface proxy for visual inspection",
        "derived_from": "smplx_joints",
        "surface_kind": "joint_capsule_proxy",
        "licensed_smplx_mesh": False,
        "scoring_allowed": False,
        "scoring_source": "smplx_joints",
        "fps": motion_manifest.get("fps"),
        "frame_count": len(frames),
        "timing": motion_manifest.get("timing"),
        "coordinates": motion_manifest.get("coordinates"),
        "contact": motion_manifest.get("contact"),
        "data_files": {
            "surface": _relative_path(data_path, manifest_path.parent),
        },
        "provenance": {
            "generator": "neodojo.smplx_surface.write_smplx_surface_proxy",
            "notes": (
                "Dependency-light capsule proxy derived from teaching joints. "
                "This is not a licensed SMPL-X mesh or body-model evaluation."
            ),
        },
    }
    _write_json(data_path, data)
    _write_json(manifest_path, manifest)
    return SMPLXSurfaceProxyWriteResult(manifest_path=manifest_path, data_path=data_path)


def register_smplx_asset_descriptor(
    out_dir: Path,
    *,
    model_path: Path,
    license_name: str,
    source_url: str | None = None,
    source_revision: str | None = None,
    variant: str | None = None,
) -> SMPLXAssetDescriptorWriteResult:
    validate_output_dir(out_dir)
    if not model_path.exists() or not model_path.is_file():
        raise ValueError(
            "licensed SMPL-X model asset does not exist; keep SMPL-X assets local "
            f"and pass an existing file path: {model_path}"
        )
    if not license_name.strip():
        raise ValueError("licensed SMPL-X asset descriptor requires a license note")

    descriptor_path = out_dir / "assets" / "smplx" / "manifest.json"
    descriptor = {
        "schema": SMPLX_ASSET_DESCRIPTOR_SCHEMA,
        "asset_kind": "licensed_smplx_body_model",
        "local_only": True,
        "licensed_smplx_mesh": True,
        "model_path": str(model_path),
        "resolved_model_path": str(model_path.resolve()),
        "sha256": sha256_file(model_path),
        "source_url": source_url,
        "source_revision": source_revision,
        "license": license_name,
        "variant": variant,
        "validation": {
            "file_exists": True,
            "load_attempted": False,
            "loadable": None,
            "notes": "Descriptor validates local file presence only; the asset is not copied or committed.",
        },
        "provenance": {
            "registered_by": "neodojo smplx-surface register-assets",
            "storage_policy": "local path only; do not commit SMPL-X model files",
        },
    }
    _write_json(descriptor_path, descriptor)
    return SMPLXAssetDescriptorWriteResult(descriptor_path=descriptor_path)


def resolve_smplx_asset_descriptor(path: Path) -> Path:
    if path.is_file():
        return path

    candidates = [
        path / "assets" / "smplx" / "manifest.json",
        path / "manifest.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise ValueError(f"could not find an SMPL-X asset descriptor under {path}")


def load_smplx_asset_descriptor(path: Path) -> dict[str, Any]:
    descriptor_path = resolve_smplx_asset_descriptor(path)
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    require_schema(descriptor, SMPLX_ASSET_DESCRIPTOR_SCHEMA, "SMPL-X asset descriptor")
    if not descriptor.get("local_only"):
        raise ValueError("SMPL-X asset descriptor must be local_only")
    if not descriptor.get("licensed_smplx_mesh"):
        raise ValueError("SMPL-X asset descriptor must describe licensed SMPL-X mesh assets")
    asset_path = Path(descriptor.get("resolved_model_path") or descriptor.get("model_path", ""))
    if not asset_path.exists() or not asset_path.is_file():
        raise ValueError(
            "licensed SMPL-X model asset is missing; keep assets local and update "
            f"the descriptor path: {asset_path}"
        )
    return descriptor


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload


def validate_smplx_mesh_generation_inputs(*, motion_record: Path, asset_descriptor: Path) -> dict[str, Any]:
    descriptor_path = resolve_smplx_asset_descriptor(asset_descriptor)
    descriptor = load_smplx_asset_descriptor(descriptor_path)
    motion_manifest_path = resolve_motion_record_manifest(motion_record)
    motion_manifest, _ = load_motion_record_frames(motion_manifest_path)

    smplx_parameters = motion_manifest.get("smplx_parameters")
    if not isinstance(smplx_parameters, dict):
        raise ValueError(
            "licensed SMPL-X mesh surface import requires a motion record with SMPL-X "
            "pose/shape parameter fields, but this record only exposes teaching joints. "
            "Use `neodojo smplx-surface proxy` until a real GVHMR export includes "
            f"mesh-ready parameters. Asset descriptor was valid for {descriptor.get('variant') or 'SMPL-X'}."
        )

    missing = smplx_parameters.get("missing_required_fields")
    if not isinstance(missing, list):
        fields = smplx_parameters.get("fields", {})
        missing = [field for field in ["global_orient", "body_pose", "betas"] if field not in fields]
    if missing:
        raise ValueError(
            "licensed SMPL-X mesh surface import requires SMPL-X parameter fields: "
            + ", ".join(missing)
        )

    data_file = smplx_parameters.get("data_file") or motion_manifest.get("data_files", {}).get("smplx_parameters")
    if not isinstance(data_file, str) or not data_file:
        raise ValueError("SMPL-X parameter metadata is missing data_file")
    data_path = motion_manifest_path.parent / data_file
    if not data_path.exists():
        raise ValueError(f"SMPL-X parameter data file is missing: {data_path}")
    parameter_data = _load_json_object(data_path, "SMPL-X parameter data")
    require_schema(parameter_data, SMPLX_PARAMETER_SCHEMA, "SMPL-X parameter data")
    if parameter_data.get("frame_count") != motion_manifest.get("frame_count"):
        raise ValueError("SMPL-X parameter data frame_count must match the motion record")
    data_fields = parameter_data.get("fields")
    if not isinstance(data_fields, dict):
        raise ValueError("SMPL-X parameter data must contain fields")
    missing_data = [field for field in ["global_orient", "body_pose", "betas"] if field not in data_fields]
    if missing_data:
        raise ValueError(
            "SMPL-X parameter data is missing required fields: "
            + ", ".join(missing_data)
        )

    return {
        "schema": SMPLX_MESH_VALIDATION_SCHEMA,
        "valid": True,
        "asset_descriptor": {
            "manifest": str(descriptor_path),
            "asset_kind": descriptor.get("asset_kind"),
            "local_only": True,
            "licensed_smplx_mesh": True,
            "sha256": descriptor.get("sha256"),
            "license": descriptor.get("license"),
            "variant": descriptor.get("variant"),
        },
        "motion_record": {
            "manifest": str(motion_manifest_path),
            "fixture_only": bool(motion_manifest.get("fixture_only", False)),
            "frame_count": motion_manifest.get("frame_count"),
            "fps": motion_manifest.get("fps"),
            "scoring_source": motion_manifest.get("scoring_source"),
        },
        "smplx_parameters": {
            "schema": SMPLX_PARAMETER_SCHEMA,
            "data_file": str(data_path),
            "parameterization": parameter_data.get("parameterization"),
            "fields": sorted(data_fields),
            "frame_count": parameter_data.get("frame_count"),
            "mesh_ready": True,
        },
        "renderer_boundary": {
            "backend": "external_licensed_smplx_mesh_frames.v1",
            "notes": (
                "The built-in command validates local licensed assets and imported "
                "SMPL-X parameters, then imports locally generated mesh frames. It "
                "does not bundle or execute the official SMPL-X body-model assets."
            ),
        },
    }


def _numeric_triplet(value: Any, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{label} must be a numeric [x, y, z] triplet")
    triplet = []
    for component in value:
        if isinstance(component, bool) or not isinstance(component, (int, float)):
            raise ValueError(f"{label} must contain only numbers")
        triplet.append(float(component))
    return triplet


def _validate_mesh_frame_data(mesh_frames_path: Path, *, expected_frame_count: int) -> dict[str, Any]:
    payload = _load_json_object(mesh_frames_path, "SMPL-X mesh frame input")
    require_schema(payload, SMPLX_MESH_FRAMES_SCHEMA, "SMPL-X mesh frame input")

    declared_frame_count = payload.get("frame_count")
    if declared_frame_count is not None and declared_frame_count != expected_frame_count:
        raise ValueError("SMPL-X mesh frame_count must match the motion record")

    frames = payload.get("frames")
    if not isinstance(frames, list) or len(frames) != expected_frame_count:
        raise ValueError("SMPL-X mesh frames must match the motion record frame count")

    normalized_frames = []
    vertex_count: int | None = None
    for frame_index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            raise ValueError("SMPL-X mesh frames must contain frame objects")
        vertices = frame.get("vertices")
        if not isinstance(vertices, list) or len(vertices) < 3:
            raise ValueError("SMPL-X mesh frame vertices must contain at least 3 vertices")
        normalized_vertices = [
            _numeric_triplet(vertex, f"SMPL-X mesh frame {frame_index} vertex {vertex_index}")
            for vertex_index, vertex in enumerate(vertices)
        ]
        if vertex_count is None:
            vertex_count = len(normalized_vertices)
        elif len(normalized_vertices) != vertex_count:
            raise ValueError("SMPL-X mesh vertex count must stay constant across frames")
        normalized_frames.append({"vertices": normalized_vertices})

    if vertex_count is None:
        raise ValueError("SMPL-X mesh frame input must contain vertices")

    faces = payload.get("faces")
    if not isinstance(faces, list) or not faces:
        raise ValueError("SMPL-X mesh frame input must contain mesh faces")
    normalized_faces = []
    for face_index, face in enumerate(faces):
        if (
            not isinstance(face, list)
            or len(face) != 3
            or any(isinstance(index, bool) or not isinstance(index, int) for index in face)
        ):
            raise ValueError(f"SMPL-X mesh face {face_index} must be an integer triangle")
        if any(index < 0 or index >= vertex_count for index in face):
            raise ValueError(f"SMPL-X mesh face {face_index} references a missing vertex")
        normalized_faces.append(list(face))

    return {
        "source_path": str(mesh_frames_path),
        "source_sha256": sha256_file(mesh_frames_path),
        "frame_count": expected_frame_count,
        "vertex_count": vertex_count,
        "face_count": len(normalized_faces),
        "faces": normalized_faces,
        "frames": normalized_frames,
        "source_provenance": payload.get("provenance"),
    }


def write_smplx_mesh_surface(
    out_dir: Path,
    *,
    motion_record: Path,
    asset_descriptor: Path,
    mesh_frames: Path,
) -> SMPLXMeshSurfaceWriteResult:
    validate_output_dir(out_dir)
    validation = validate_smplx_mesh_generation_inputs(
        motion_record=motion_record,
        asset_descriptor=asset_descriptor,
    )
    motion_manifest_path = Path(validation["motion_record"]["manifest"])
    motion_manifest = _load_json_object(motion_manifest_path, "motion-record manifest")
    frame_count = int(motion_manifest["frame_count"])
    mesh_data = _validate_mesh_frame_data(mesh_frames, expected_frame_count=frame_count)

    surface_dir = out_dir / "surfaces" / "smplx"
    data_path = surface_dir / "mesh-surface.json"
    validation_path = surface_dir / "validation.json"
    manifest_path = surface_dir / "manifest.json"

    validation_report = {
        **validation,
        "mesh_frames": {
            "schema": SMPLX_MESH_FRAMES_SCHEMA,
            "source_path": mesh_data["source_path"],
            "source_sha256": mesh_data["source_sha256"],
            "frame_count": mesh_data["frame_count"],
            "vertex_count": mesh_data["vertex_count"],
            "face_count": mesh_data["face_count"],
        },
    }
    data = {
        "schema": SMPLX_MESH_SURFACE_SCHEMA,
        "track_id": "smplx",
        "surface_kind": "licensed_smplx_mesh_external_frames",
        "faces": mesh_data["faces"],
        "frames": mesh_data["frames"],
        "frame_count": mesh_data["frame_count"],
        "vertex_count": mesh_data["vertex_count"],
        "face_count": mesh_data["face_count"],
    }
    manifest = {
        "schema": SMPLX_MESH_SURFACE_SCHEMA,
        "track_id": "smplx",
        "fixture_only": bool(motion_manifest.get("fixture_only", False)),
        "source_motion_record": _relative_path(motion_manifest_path, manifest_path.parent),
        "source_smplx_parameters": validation["smplx_parameters"],
        "role": "Local-only licensed SMPL-X mesh surface evidence for visual inspection",
        "derived_from": "external_licensed_smplx_mesh_frames",
        "surface_kind": "licensed_smplx_mesh_external_frames",
        "licensed_smplx_mesh": True,
        "scoring_allowed": False,
        "scoring_source": "smplx_joints",
        "fps": motion_manifest.get("fps"),
        "frame_count": mesh_data["frame_count"],
        "vertex_count": mesh_data["vertex_count"],
        "face_count": mesh_data["face_count"],
        "timing": motion_manifest.get("timing"),
        "coordinates": motion_manifest.get("coordinates"),
        "contact": motion_manifest.get("contact"),
        "asset_descriptor": validation["asset_descriptor"],
        "renderer": validation["renderer_boundary"],
        "data_files": {
            "surface": _relative_path(data_path, manifest_path.parent),
            "validation": _relative_path(validation_path, manifest_path.parent),
        },
        "provenance": {
            "generator": "neodojo.smplx_surface.write_smplx_mesh_surface",
            "mesh_frames_source_path": mesh_data["source_path"],
            "mesh_frames_source_sha256": mesh_data["source_sha256"],
            "mesh_frames_source_provenance": mesh_data["source_provenance"],
            "storage_policy": (
                "Generated mesh artifacts stay under ignored outputs/. Licensed "
                "SMPL-X model assets are referenced by descriptor and are never copied."
            ),
        },
    }
    _write_json(data_path, data)
    _write_json(validation_path, validation_report)
    _write_json(manifest_path, manifest)
    return SMPLXMeshSurfaceWriteResult(
        manifest_path=manifest_path,
        data_path=data_path,
        validation_path=validation_path,
    )


def resolve_smplx_surface_manifest(path: Path) -> Path:
    if path.is_file():
        return path

    candidates = [
        path / "surfaces" / "smplx" / "manifest.json",
        path / "manifest.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise ValueError(f"could not find an SMPL-X surface manifest under {path}")


def load_smplx_surface_layer(surface_manifest_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = json.loads(surface_manifest_path.read_text(encoding="utf-8"))
    schema = manifest.get("schema")
    if schema not in {SMPLX_SURFACE_PROXY_SCHEMA, SMPLX_MESH_SURFACE_SCHEMA}:
        raise ValueError("unsupported SMPL-X surface manifest schema")
    if manifest.get("track_id") != "smplx":
        raise ValueError("expected an SMPL-X surface manifest")
    if manifest.get("scoring_allowed"):
        raise ValueError("SMPL-X surface layer cannot be a scoring source")

    data_file = manifest.get("data_files", {}).get("surface")
    if not data_file:
        raise ValueError("SMPL-X surface manifest is missing data_files.surface")

    data_path = surface_manifest_path.parent / data_file
    data = _load_json_object(data_path, "SMPL-X surface data")
    require_schema(data, schema, "SMPL-X surface data")
    frames = data.get("frames")
    if not isinstance(frames, list) or len(frames) < 8:
        raise ValueError("SMPL-X surface data must contain at least 8 frames")
    if schema == SMPLX_MESH_SURFACE_SCHEMA:
        faces = data.get("faces")
        if not isinstance(faces, list) or not faces:
            raise ValueError("SMPL-X mesh surface data must contain faces")
    return manifest, data


def load_smplx_surface_proxy(surface_manifest_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest, data = load_smplx_surface_layer(surface_manifest_path)
    require_schema(manifest, SMPLX_SURFACE_PROXY_SCHEMA, "SMPL-X surface proxy manifest")
    return manifest, data["frames"]
