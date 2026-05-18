from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import PUBLIC_DEMO_SCHEMA, require_schema
from .motion_contract import validate_output_dir
from .public_demo import smoke_check_public_demo
from .real_conversion import REAL_CONVERSION_AUDIT_SCHEMA
from .real_demo import REAL_CONVERSION_DEMO_SCHEMA


REAL_DEMO_PAGES_PROMOTION_SCHEMA = "neodojo.real_demo_pages_promotion.v1"

FORBIDDEN_PROMOTION_PATH_FRAGMENTS = (
    ".mp4",
    ".mov",
    ".mkv",
    ".avi",
    ".webm",
    ".pt",
    ".pkl",
    ".npz",
    "checkpoints",
    "SMPLX_MODEL_DIR",
)


@dataclass(frozen=True)
class RealDemoPagesPromotionResult:
    manifest_path: Path
    public_demo_manifest_path: Path
    audit_manifest_path: Path
    staged_dir: Path
    checked_paths: list[Path]


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _relative_path(path: Path, start: Path) -> str:
    return str(path.relative_to(start)).replace("\\", "/")


def _require_inside(path: Path, root: Path, *, label: str) -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} escapes the downloaded artifact: {path}") from exc


def _reject_forbidden_paths(root: Path) -> None:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rendered = str(path)
        lowered = rendered.lower()
        for fragment in FORBIDDEN_PROMOTION_PATH_FRAGMENTS:
            if fragment.lower() in lowered:
                raise ValueError(f"forbidden generated artifact path in promotion input: {rendered}")


def _manifest_candidates(root: Path, schema: str) -> list[tuple[Path, dict[str, Any]]]:
    candidates = []
    for path in root.rglob("manifest.json"):
        payload = _load_json(path)
        if payload.get("schema") == schema:
            candidates.append((path, payload))
    return candidates


def _require_one_manifest(root: Path, schema: str, label: str) -> tuple[Path, dict[str, Any]]:
    candidates = _manifest_candidates(root, schema)
    if len(candidates) != 1:
        raise ValueError(f"expected exactly one {label} manifest, found {len(candidates)}")
    return candidates[0]


def validate_real_demo_pages_promotion(
    download_root: Path,
    out_dir: Path,
    *,
    source_run_id: str,
    artifact_name: str,
) -> RealDemoPagesPromotionResult:
    if not download_root.exists():
        raise ValueError(f"downloaded artifact root does not exist: {download_root}")
    if not download_root.is_dir():
        raise ValueError(f"downloaded artifact root is not a directory: {download_root}")

    validate_output_dir(out_dir)
    _reject_forbidden_paths(download_root)

    real_demo_manifest_path, real_demo = _require_one_manifest(
        download_root,
        REAL_CONVERSION_DEMO_SCHEMA,
        "real-demo",
    )
    require_schema(real_demo, REAL_CONVERSION_DEMO_SCHEMA, "real-demo manifest")
    if real_demo.get("status") != "generated":
        raise ValueError("real-demo manifest is not generated")
    if real_demo.get("real_gvhmr_artifact_imported") is not True:
        raise ValueError("real-demo manifest does not prove a real GVHMR artifact import")
    if real_demo.get("source_materialization_fixture_only") is not False:
        raise ValueError("source materialization is still fixture-only")
    if real_demo.get("gvhmr_export_fixture_only") is not False:
        raise ValueError("GVHMR export is still fixture-only")
    if real_demo.get("scoring_source") != "smplx":
        raise ValueError("real-demo manifest must keep SMPL-X as scoring source")
    if real_demo.get("g1_scoring_allowed") is not False:
        raise ValueError("real-demo manifest cannot allow G1 scoring")

    public_demo_ref = real_demo.get("public_demo")
    if not isinstance(public_demo_ref, str) or not public_demo_ref:
        raise ValueError("real-demo manifest is missing public_demo reference")
    public_demo_manifest_path = (real_demo_manifest_path.parent / public_demo_ref).resolve()
    _require_inside(public_demo_manifest_path, download_root, label="public-demo manifest")
    public_demo_dir = public_demo_manifest_path.parent
    public_demo = _load_json(public_demo_manifest_path)
    require_schema(public_demo, PUBLIC_DEMO_SCHEMA, "public-demo manifest")
    if public_demo.get("scoring_source") != "smplx":
        raise ValueError("public-demo must keep SMPL-X as scoring source")
    if public_demo.get("tracks", {}).get("g1", {}).get("scoring_allowed"):
        raise ValueError("public-demo cannot allow G1 scoring")

    required_public_files = [
        public_demo_manifest_path,
        public_demo_dir / str(public_demo.get("html", "index.html")),
        public_demo_dir / str(public_demo.get("scene", "scene.json")),
        public_demo_dir / str(public_demo.get("recording", "neodojo-demo.rrd")),
        public_demo_dir / str(public_demo.get("screenshot", "screenshot.svg")),
    ]
    for path in required_public_files:
        _require_inside(path, download_root, label="public-demo file")
        if not path.exists() or path.stat().st_size <= 0:
            raise ValueError(f"missing or blank public-demo file: {path}")

    audit_manifest_path, audit = _require_one_manifest(
        download_root,
        REAL_CONVERSION_AUDIT_SCHEMA,
        "real-conversion audit",
    )
    require_schema(audit, REAL_CONVERSION_AUDIT_SCHEMA, "real-conversion audit manifest")
    if audit.get("complete") is not True:
        raise ValueError("real-conversion audit is not complete")
    if audit.get("blocked") is not False:
        raise ValueError("real-conversion audit is still blocked")
    if audit.get("status") != "real_demo_verified":
        raise ValueError("real-conversion audit did not verify the real demo")

    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(public_demo_dir, out_dir)

    promotion_manifest_path = out_dir / "promotion-manifest.json"
    promotion = {
        "schema": REAL_DEMO_PAGES_PROMOTION_SCHEMA,
        "source_run_id": source_run_id,
        "artifact_name": artifact_name,
        "real_demo_manifest": _relative_path(real_demo_manifest_path.resolve(), download_root.resolve()),
        "audit_manifest": _relative_path(audit_manifest_path.resolve(), download_root.resolve()),
        "real_gvhmr_artifact_imported": True,
        "source_materialization_fixture_only": False,
        "gvhmr_export_fixture_only": False,
        "public_demo_fixture_only": bool(public_demo.get("fixture_only")),
        "scoring_source": "smplx",
        "g1_scoring_allowed": False,
        "notes": (
            "The promoted public-demo artifact has a real non-fixture GVHMR/SMPL-X import. "
            "The aggregate public_demo_fixture_only flag may remain true when the visual G1 "
            "companion still uses fixture-derived assets."
        ),
    }
    _write_json(promotion_manifest_path, promotion)

    smoke = smoke_check_public_demo(out_dir)
    checked_paths = list(
        dict.fromkeys(
            [
                real_demo_manifest_path,
                public_demo_manifest_path,
                audit_manifest_path,
                promotion_manifest_path,
                *required_public_files,
                *smoke.checked_paths,
            ]
        )
    )
    return RealDemoPagesPromotionResult(
        manifest_path=promotion_manifest_path,
        public_demo_manifest_path=public_demo_manifest_path,
        audit_manifest_path=audit_manifest_path,
        staged_dir=out_dir,
        checked_paths=checked_paths,
    )
