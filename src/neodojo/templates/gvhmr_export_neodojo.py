#!/usr/bin/env python3
"""Export GVHMR hmr4d_results.pt to neodojo.gvhmr_smplx_joints.v1.

Run this on the GPU/GVHMR machine after GVHMR writes hmr4d_results.pt. The
script intentionally depends only on the external GPU environment plus a
licensed local SMPL-X model path; it does not import neodojo.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCHEMA = "neodojo.gvhmr_smplx_joints.v1"
TEACHING_JOINTS = [
    "pelvis",
    "spine",
    "neck",
    "head",
    "left_hip",
    "left_knee",
    "left_ankle",
    "right_hip",
    "right_knee",
    "right_ankle",
    "left_shoulder",
    "left_elbow",
    "left_wrist",
    "right_shoulder",
    "right_elbow",
    "right_wrist",
]
JOINT_ALIASES = {
    "spine": ["spine3", "spine2", "spine1"],
}
SMPLX_PARAMETER_KEYS = {
    "global_orient",
    "body_pose",
    "betas",
    "transl",
    "left_hand_pose",
    "right_hand_pose",
    "jaw_pose",
    "leye_pose",
    "reye_pose",
    "expression",
}


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"failed to parse {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"{label} must be a JSON object")
    return payload


def _to_plain(value: Any) -> Any:
    if hasattr(value, "detach"):
        value = value.detach().cpu()
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, dict):
        return {str(key): _to_plain(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_plain(child) for child in value]
    return value


def _frame_count(params: dict[str, Any]) -> int:
    for key in ("global_orient", "body_pose", "transl"):
        value = params.get(key)
        shape = getattr(value, "shape", None)
        if shape is not None and len(shape) >= 1:
            return int(shape[0])
    raise SystemExit("selected SMPL-X parameter block does not expose a frame dimension")


def _slice_params(params: dict[str, Any], start: int, end: int, device: str) -> dict[str, Any]:
    sliced: dict[str, Any] = {}
    count = end - start
    for key, value in params.items():
        if key not in SMPLX_PARAMETER_KEYS or not hasattr(value, "to"):
            continue
        shape = getattr(value, "shape", ())
        if len(shape) == 1 and key == "betas":
            value = value[None, :].repeat(count, 1)
        else:
            value = value[start:end]
        if len(getattr(value, "shape", ())) > 2:
            value = value.reshape(count, -1)
        sliced[key] = value.to(device)
    missing = [key for key in ("global_orient", "body_pose", "betas") if key not in sliced]
    if missing:
        raise SystemExit(f"selected SMPL-X parameter block is missing: {', '.join(missing)}")
    return sliced


def _joint_name_index() -> dict[str, int]:
    try:
        from smplx.joint_names import JOINT_NAMES
    except Exception as exc:
        raise SystemExit(
            "failed to import smplx.joint_names.JOINT_NAMES; install the smplx "
            "package in the GPU environment"
        ) from exc
    return {name: index for index, name in enumerate(JOINT_NAMES)}


def _resolve_joint_mapping(name_to_index: dict[str, int]) -> dict[str, int]:
    mapping = {}
    missing = []
    for teaching_name in TEACHING_JOINTS:
        candidates = [teaching_name, *JOINT_ALIASES.get(teaching_name, [])]
        match = next((candidate for candidate in candidates if candidate in name_to_index), None)
        if match is None:
            missing.append(f"{teaching_name} ({'/'.join(candidates)})")
        else:
            mapping[teaching_name] = name_to_index[match]
    if missing:
        raise SystemExit("SMPL-X joint name table is missing teaching joints: " + ", ".join(missing))
    return mapping


def _normalize_root_floor(frames: list[dict[str, list[float]]]) -> None:
    if not frames:
        return
    first_pelvis = frames[0]["pelvis"]
    floor = min(frame[joint][1] for frame in frames for joint in ("left_ankle", "right_ankle"))
    for frame in frames:
        for point in frame.values():
            point[0] = round(point[0] - first_pelvis[0], 6)
            point[1] = round(point[1] - floor, 6)
            point[2] = round(point[2] - first_pelvis[2], 6)


def _resolve_smplx_model_path(path: Path, gender: str) -> Path:
    expected_file = f"SMPLX_{gender.upper()}.npz"
    if path.is_file():
        return path
    if not path.exists():
        raise SystemExit(f"SMPL-X model path does not exist: {path}")
    if path.name.lower() == "smplx" and (path / expected_file).exists():
        return path.parent
    if (path / "smplx" / expected_file).exists():
        return path
    if (path / expected_file).exists():
        return path / expected_file
    raise SystemExit(
        "SMPL-X model path must be the body_models root containing "
        f"smplx/{expected_file}, the smplx directory, or the model file itself: {path}"
    )


def _smplx_joints_from_params(
    params: dict[str, Any],
    *,
    smplx_model_path: Path,
    gender: str,
    batch_size: int,
    device: str,
) -> tuple[list[dict[str, list[float]]], dict[str, int]]:
    try:
        import smplx
        import torch
    except Exception as exc:
        raise SystemExit("install torch and smplx in the GPU environment before running this exporter") from exc

    frame_count = _frame_count(params)
    mapping = _resolve_joint_mapping(_joint_name_index())
    frames: list[dict[str, list[float]]] = []
    models: dict[int, Any] = {}

    with torch.no_grad():
        for start in range(0, frame_count, batch_size):
            end = min(start + batch_size, frame_count)
            count = end - start
            if count not in models:
                model = smplx.create(
                    str(smplx_model_path),
                    model_type="smplx",
                    gender=gender,
                    use_pca=False,
                    batch_size=count,
                )
                models[count] = model.to(device)
            model = models[count]
            output = model(**_slice_params(params, start, end, device), return_verts=False)
            joints = output.joints.detach().cpu()
            for batch_index in range(count):
                frame = {}
                for teaching_name, smplx_index in mapping.items():
                    point = joints[batch_index, smplx_index].tolist()
                    frame[teaching_name] = [round(float(component), 6) for component in point]
                frames.append(frame)
    return frames, mapping


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hmr4d-results", type=Path, required=True, help="GVHMR hmr4d_results.pt")
    parser.add_argument(
        "--smplx-model-dir",
        type=Path,
        required=True,
        help=(
            "local licensed SMPL-X body_models root, nested smplx directory, "
            "or direct SMPLX_NEUTRAL.npz path"
        ),
    )
    parser.add_argument("--template", type=Path, required=True, help="gvhmr-smplx-joints.template.json from handoff")
    parser.add_argument(
        "--source-materialization",
        type=Path,
        required=True,
        help="source-materialization.json used to create the handoff",
    )
    parser.add_argument("--out", type=Path, required=True, help="output neodojo.gvhmr_smplx_joints.v1 JSON")
    parser.add_argument("--parameter-block", default="smpl_params_global")
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument("--routine", default="Baduanjin")
    parser.add_argument("--form", default="imported GVHMR segment")
    parser.add_argument("--gender", default="neutral", choices=["neutral", "male", "female"])
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--runtime", default="<fill GPU runtime and hardware>")
    parser.add_argument("--upstream-version", default="<fill GVHMR commit or package version>")
    parser.add_argument("--gpu-command", default="<fill actual GVHMR command>")
    parser.add_argument("--no-root-floor-normalize", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.fps <= 0:
        raise SystemExit("--fps must be positive")
    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be positive")

    try:
        import torch
    except Exception as exc:
        raise SystemExit("install torch in the GPU environment before reading hmr4d_results.pt") from exc

    template = _load_json(args.template, "neodojo export template")
    source_materialization = _load_json(args.source_materialization, "source materialization manifest")
    payload = torch.load(args.hmr4d_results, map_location="cpu")
    if not isinstance(payload, dict):
        raise SystemExit("hmr4d_results.pt must contain a dictionary")
    params = payload.get(args.parameter_block)
    if not isinstance(params, dict):
        raise SystemExit(f"hmr4d_results.pt is missing parameter block {args.parameter_block!r}")
    smplx_model_path = _resolve_smplx_model_path(args.smplx_model_dir, args.gender)

    frames, joint_mapping = _smplx_joints_from_params(
        params,
        smplx_model_path=smplx_model_path,
        gender=args.gender,
        batch_size=args.batch_size,
        device=args.device,
    )
    if len(frames) < 8:
        raise SystemExit("neodojo GVHMR export requires at least 8 frames")
    if not args.no_root_floor_normalize:
        _normalize_root_floor(frames)

    provenance = dict(template.get("provenance") or {})
    provenance.update(
        {
            "source_materialization_manifest": str(args.source_materialization),
            "source_materialization_sha256": provenance.get("source_materialization_sha256"),
            "source_id": provenance.get("source_id")
            or (source_materialization.get("source_prep") or {}).get("source_id"),
            "trim": provenance.get("trim") or source_materialization.get("trim"),
            "input_video": provenance.get("input_video")
            or (source_materialization.get("gpu_handoff") or {}).get("trimmed_video_argument"),
            "input_video_sha256": provenance.get("input_video_sha256"),
            "gpu_command": args.gpu_command,
            "runtime": args.runtime,
            "upstream_version": args.upstream_version,
            "hmr4d_results": str(args.hmr4d_results),
            "parameter_block": args.parameter_block,
            "smplx_model_dir": str(args.smplx_model_dir),
            "smplx_model_path": str(smplx_model_path),
            "joint_mapping": {name: int(index) for name, index in joint_mapping.items()},
            "root_floor_normalized": not args.no_root_floor_normalize,
        }
    )

    export = {
        "schema": SCHEMA,
        "fixture_only": False,
        "routine": args.routine,
        "form": args.form,
        "fps": args.fps,
        "frames": frames,
        "smplx_parameters": _to_plain(params),
        "provenance": provenance,
        "export_notes": {
            "generated_by": "neodojo GVHMR GPU handoff exporter",
            "requires_local_licensed_smplx_assets": True,
            "source_materialization_schema": source_materialization.get("schema"),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(export, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")
    print(f"frames {len(frames)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
