from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .browser_capture import BROWSER_CAPTURE_SCHEMA
from .contracts import PUBLIC_DEMO_SCHEMA, require_schema
from .g1_render import G1_RENDER_SCHEMA
from .motion_contract import _relative_path, _write_json, validate_output_dir
from .public_demo import smoke_check_public_demo
from .viser_runtime import VISER_RUNTIME_SCHEMA

CAPTURE_BUNDLE_SCHEMA = "neodojo.capture_bundle.v1"
CAPTURE_BUNDLE_STYLE = "roboharness_multi_camera_evidence_manifest"
REQUIRED_CAPTURE_VIEWS = ("front", "side", "top")


@dataclass(frozen=True)
class CaptureBundleWriteResult:
    manifest_path: Path
    checked_paths: list[Path]


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _resolve_manifest_path(path: Path, default_name: str) -> Path:
    return path if path.is_file() else path / default_name


def _resolve_artifact(manifest_path: Path, reference: str) -> Path:
    path = Path(reference)
    if path.is_absolute():
        return path
    return manifest_path.parent / path


def _require_nonblank(path: Path, label: str) -> bytes:
    if not path.exists():
        raise ValueError(f"{label} artifact is missing: {path}")
    payload = path.read_bytes()
    if not payload:
        raise ValueError(f"{label} artifact is blank: {path}")
    return payload


def _require_text_labels(path: Path, label: str, required_labels: list[str]) -> None:
    text = _require_nonblank(path, label).decode("utf-8")
    missing = [required for required in required_labels if required not in text]
    if missing:
        raise ValueError(f"{label} is missing expected labels: {', '.join(missing)}")


def _unique_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    unique = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _load_public_demo(public_demo: Path) -> tuple[Path, dict[str, Any], dict[str, Path], list[Path]]:
    smoke = smoke_check_public_demo(public_demo)
    manifest_path = smoke.manifest_path
    manifest = _load_json(manifest_path)
    require_schema(manifest, PUBLIC_DEMO_SCHEMA, "public-demo manifest")
    if manifest.get("scoring_source") != "smplx":
        raise ValueError("public demo capture input must keep SMPL-X as scoring_source")
    if manifest.get("tracks", {}).get("g1", {}).get("scoring_allowed"):
        raise ValueError("public demo capture input cannot allow G1 scoring")

    artifacts = {
        "html": _resolve_artifact(manifest_path, manifest["html"]),
        "scene": _resolve_artifact(manifest_path, manifest["scene"]),
        "recording": _resolve_artifact(manifest_path, manifest["recording"]),
        "screenshot": _resolve_artifact(manifest_path, manifest["screenshot"]),
    }
    return manifest_path, manifest, artifacts, smoke.checked_paths


def _load_viser_runtime(viser_runtime: Path) -> tuple[Path, dict[str, Any], dict[str, Path]]:
    manifest_path = _resolve_manifest_path(viser_runtime, "viser-runtime.json")
    manifest = _load_json(manifest_path)
    require_schema(manifest, VISER_RUNTIME_SCHEMA, "Viser runtime manifest")
    if manifest.get("scoring_source") != "smplx":
        raise ValueError("Viser runtime capture input must keep SMPL-X as scoring_source")
    if manifest.get("g1_scoring_allowed"):
        raise ValueError("Viser runtime capture input cannot allow G1 scoring")

    visual_smoke = manifest.get("visual_smoke")
    if not isinstance(visual_smoke, dict):
        raise ValueError("Viser runtime manifest must include visual_smoke metadata")
    screenshot_refs = visual_smoke.get("screenshot_paths")
    if not isinstance(screenshot_refs, dict):
        raise ValueError("Viser runtime manifest must include visual_smoke.screenshot_paths")
    missing_views = [view for view in REQUIRED_CAPTURE_VIEWS if view not in screenshot_refs]
    if missing_views:
        raise ValueError(f"Viser runtime preview screenshots are missing views: {', '.join(missing_views)}")

    required_labels = visual_smoke.get("required_labels", [])
    if not isinstance(required_labels, list) or not all(isinstance(label, str) for label in required_labels):
        raise ValueError("Viser runtime visual_smoke.required_labels must be a list of strings")

    paths = {
        view: _resolve_artifact(manifest_path, str(screenshot_refs[view]))
        for view in REQUIRED_CAPTURE_VIEWS
    }
    for view, path in paths.items():
        _require_text_labels(path, f"viser {view} preview", required_labels)
    return manifest_path, manifest, paths


def _load_g1_render(g1_render: Path) -> tuple[Path, dict[str, Any], dict[str, Path]]:
    manifest_path = _resolve_manifest_path(g1_render, "manifest.json")
    manifest = _load_json(manifest_path)
    require_schema(manifest, G1_RENDER_SCHEMA, "G1 render manifest")
    if manifest.get("scoring_source") != "smplx":
        raise ValueError("G1 render capture input must keep SMPL-X as scoring_source")
    if manifest.get("g1_scoring_allowed"):
        raise ValueError("G1 render capture input cannot allow G1 scoring")

    frame_refs = manifest.get("frame_paths")
    if not isinstance(frame_refs, dict):
        raise ValueError("G1 render manifest must include frame_paths")
    missing_views = [view for view in REQUIRED_CAPTURE_VIEWS if view not in frame_refs]
    if missing_views:
        raise ValueError(f"G1 render frame evidence is missing views: {', '.join(missing_views)}")

    nonblank_views = manifest.get("nonblank_views")
    if isinstance(nonblank_views, dict):
        blank_views = [view for view in REQUIRED_CAPTURE_VIEWS if not nonblank_views.get(view)]
        if blank_views:
            raise ValueError(f"G1 render manifest reports blank views: {', '.join(blank_views)}")

    paths = {
        view: _resolve_artifact(manifest_path, str(frame_refs[view]))
        for view in REQUIRED_CAPTURE_VIEWS
    }
    for view, path in paths.items():
        _require_nonblank(path, f"g1 render {view} frame")
    return manifest_path, manifest, paths


def _load_browser_capture(browser_capture: Path) -> tuple[Path, dict[str, Any], Path]:
    manifest_path = _resolve_manifest_path(browser_capture, "manifest.json")
    manifest = _load_json(manifest_path)
    require_schema(manifest, BROWSER_CAPTURE_SCHEMA, "browser-capture manifest")
    if not manifest.get("real_browser_capture"):
        raise ValueError("browser-capture manifest must set real_browser_capture")
    if manifest.get("scoring_source") != "smplx":
        raise ValueError("browser-capture input must keep SMPL-X as scoring_source")
    if manifest.get("g1_scoring_allowed"):
        raise ValueError("browser-capture input cannot allow G1 scoring")

    screenshot_ref = manifest.get("screenshot")
    if not isinstance(screenshot_ref, str) or not screenshot_ref:
        raise ValueError("browser-capture manifest must include screenshot")
    screenshot_path = _resolve_artifact(manifest_path, screenshot_ref)
    _require_nonblank(screenshot_path, "browser-capture screenshot")
    return manifest_path, manifest, screenshot_path


def write_capture_bundle(
    out_dir: Path,
    *,
    public_demo: Path,
    viser_runtime: Path,
    g1_render: Path,
    browser_capture: Path | None = None,
) -> CaptureBundleWriteResult:
    validate_output_dir(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"

    public_manifest_path, public_manifest, public_artifacts, public_checked = _load_public_demo(public_demo)
    viser_manifest_path, viser_manifest, viser_paths = _load_viser_runtime(viser_runtime)
    g1_render_manifest_path, g1_render_manifest, g1_render_paths = _load_g1_render(g1_render)
    browser_manifest_path = None
    browser_manifest = None
    browser_screenshot_path = None
    if browser_capture is not None:
        browser_manifest_path, browser_manifest, browser_screenshot_path = _load_browser_capture(browser_capture)

    checked_candidates = [
        *public_checked,
        *viser_paths.values(),
        *g1_render_paths.values(),
    ]
    if browser_screenshot_path is not None:
        checked_candidates.append(browser_screenshot_path)
    checked_paths = _unique_paths(checked_candidates)

    def rel(path: Path) -> str:
        return _relative_path(path, manifest_path.parent)

    manifest = {
        "schema": CAPTURE_BUNDLE_SCHEMA,
        "style": CAPTURE_BUNDLE_STYLE,
        "fixture_only": bool(
            public_manifest.get("fixture_only")
            or viser_manifest.get("fixture_only")
            or g1_render_manifest.get("fixture_only")
        ),
        "source": {
            "kind": "generated_evidence_plus_browser_capture"
            if browser_manifest
            else "generated_evidence_only",
            "real_browser_capture": bool(browser_manifest),
            "real_offscreen_recorder": bool(browser_manifest),
            "real_simulator_recorder": False,
            "real_roboharness_integration": False,
            "notes": (
                "This bundle validates existing generated artifacts in a "
                "roboharness-style multi-camera evidence shape. Browser capture "
                "is included only when an optional browser-capture manifest is "
                "provided; simulator/video recorder integration remains follow-on."
            ),
        },
        "inputs": {
            "public_demo": rel(public_manifest_path),
            "viser_runtime": rel(viser_manifest_path),
            "g1_render": rel(g1_render_manifest_path),
            "browser_capture": rel(browser_manifest_path) if browser_manifest_path else None,
        },
        "artifact_groups": {
            "public_demo": {
                "html": rel(public_artifacts["html"]),
                "scene": rel(public_artifacts["scene"]),
                "recording": rel(public_artifacts["recording"]),
                "screenshot": rel(public_artifacts["screenshot"]),
                "role": "static public artifact and fixture-only overview screenshot",
            },
            "viser_runtime": {
                "scene": rel(_resolve_artifact(viser_manifest_path, str(viser_manifest["scene"]))),
                "preview_kind": viser_manifest.get("visual_smoke", {}).get("kind"),
                "views": {
                    view: rel(path)
                    for view, path in viser_paths.items()
                },
            },
            "g1_render": {
                "renderer": g1_render_manifest.get("renderer"),
                "views": {
                    view: rel(path)
                    for view, path in g1_render_paths.items()
                },
            },
            **(
                {
                    "browser_capture": {
                        "kind": browser_manifest.get("capture_kind"),
                        "screenshot": rel(browser_screenshot_path),
                        "viewport": browser_manifest.get("viewport"),
                        "real_browser_capture": True,
                    }
                }
                if browser_manifest is not None and browser_screenshot_path is not None
                else {}
            ),
        },
        "views": {
            view: {
                "camera_role": f"{view}_multi_camera_evidence",
                "artifacts": {
                    "viser_preview": rel(viser_paths[view]),
                    "g1_render_frame": rel(g1_render_paths[view]),
                },
                "nonblank_artifacts": True,
            }
            for view in REQUIRED_CAPTURE_VIEWS
        },
        "verification": {
            "required_views": list(REQUIRED_CAPTURE_VIEWS),
            "nonblank_artifact_count": len(checked_paths),
            "required_labels": sorted(
                set(
                    [
                        "SMPL-X teacher",
                        "Unitree G1 visual",
                        "G1 scoring allowed: false",
                        "fixture-only",
                    ]
                )
            ),
            "public_demo_smoke_checked": True,
            "viser_preview_smoke_checked": True,
            "g1_render_frame_smoke_checked": True,
            "browser_capture_smoke_checked": bool(browser_manifest),
        },
        "scoring_source": "smplx",
        "g1_scoring_allowed": False,
        "follow_on": {
            "real_roboharness_integration": "replace generated SVG/HTML evidence with a direct roboharness or simulator camera recorder when selected",
            "production_viser_capture": "capture live-client Viser screenshots after browser automation targets the runtime client, not only the static public demo",
        },
    }
    _write_json(manifest_path, manifest)
    return CaptureBundleWriteResult(manifest_path=manifest_path, checked_paths=checked_paths)
