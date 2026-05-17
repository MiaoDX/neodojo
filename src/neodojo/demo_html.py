from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from .contracts import HTML_DEMO_SCHEMA
from .fixtures import build_fixture, build_fixture_from_smplx_frames, compute_feedback
from .motion_contract import load_track_frames, write_fixture_motion_contract


@dataclass(frozen=True)
class DemoWriteResult:
    html_path: Path
    manifest_path: Path
    motion_record_manifest_path: Path
    smplx_track_manifest_path: Path


def render_demo_html(fixture: dict[str, Any] | None = None) -> str:
    data = fixture if fixture is not None else build_fixture()
    template = resources.files("neodojo.templates").joinpath("teaching_demo.html").read_text(encoding="utf-8")
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return template.replace("__NEODOJO_DEMO_DATA__", payload)


def write_demo(out_dir: Path, frame_count: int = 96) -> DemoWriteResult:
    contract = write_fixture_motion_contract(out_dir, frame_count=frame_count)
    smplx_frames = load_track_frames(contract.smplx_track_manifest_path)
    fixture = build_fixture_from_smplx_frames(smplx_frames)
    out_dir.mkdir(parents=True, exist_ok=True)

    html_path = out_dir / "index.html"
    manifest_path = out_dir / "manifest.json"
    html_path.write_text(render_demo_html(fixture), encoding="utf-8")
    motion_manifest = json.loads(contract.motion_record_manifest_path.read_text(encoding="utf-8"))
    manifest_path.write_text(
        json.dumps(
            {
                "schema": HTML_DEMO_SCHEMA,
                "fixture_only": True,
                "html": "index.html",
                "motion_record": "motion-record/manifest.json",
                "frame_count": fixture["frame_count"],
                "timing": motion_manifest.get("timing"),
                "coordinates": motion_manifest.get("coordinates"),
                "contact": motion_manifest.get("contact"),
                "scoring_source": fixture["scoring_source"],
                "tracks": {
                    "smplx": {
                        "role": fixture["tracks"]["smplx"]["role"],
                        "manifest": "tracks/smplx/manifest.json",
                    },
                    "g1": {
                        "role": fixture["tracks"]["g1"]["role"],
                        "manifest": None,
                    },
                },
                "feedback": fixture["feedback"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return DemoWriteResult(
        html_path=html_path,
        manifest_path=manifest_path,
        motion_record_manifest_path=contract.motion_record_manifest_path,
        smplx_track_manifest_path=contract.smplx_track_manifest_path,
    )
