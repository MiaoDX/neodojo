from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from neodojo.bilibili import build_ytdlp_command, write_bilibili_download_manifest
from neodojo.contracts import sha256_file
from neodojo.fixtures import build_smplx_fixture_frames
from neodojo.routine import (
    ROUTINE_MANIFEST_SCHEMA,
    get_routine_definition,
    smoke_check_routine_html,
    validate_routine_manifest,
    write_routine_gpu_handoffs,
    write_routine_html,
    write_routine_split,
)


def _minimal_routine_manifest(phases: list[dict]) -> dict:
    return {
        "schema": ROUTINE_MANIFEST_SCHEMA,
        "selection_rule": "first_demo_only",
        "routines": {
            "test": {
                "routine": "test",
                "name_zh": "测试",
                "name_en": "Test",
                "bilibili_bvid": "BVTEST",
                "source_video": "video/bilibili/test.mp4",
                "phases": phases,
            }
        },
    }


def _phase(
    phase_id: str = "phase_a",
    *,
    name_zh: str = "第一势",
    name_en: str = "Phase A",
    start: float = 1.0,
    end: float = 4.0,
) -> dict:
    return {
        "phase_id": phase_id,
        "name_zh": name_zh,
        "name_en": name_en,
        "start_seconds": start,
        "end_seconds": end,
        "selection_rule": "first_demo_only",
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class RoutinePipelineTests(unittest.TestCase):
    def test_committed_routine_manifest_validates_expected_phase_counts(self) -> None:
        manifest = validate_routine_manifest()

        self.assertEqual(len(manifest["routines"]["baduanjin"]["phases"]), 8)
        self.assertEqual(len(manifest["routines"]["wuqinxi"]["phases"]), 10)
        self.assertEqual(len(manifest["routines"]["yijinjing"]["phases"]), 12)
        self.assertEqual(manifest["routines"]["baduanjin"]["phases"][0]["selection_rule"], "first_demo_only")

    def test_unknown_routine_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown routine"):
            get_routine_definition("does-not-exist")

    def test_routine_manifest_rejects_invalid_phase_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = root / "routines.json"
            payload = _minimal_routine_manifest([_phase(), _phase("phase_b", start=3.5, end=5.0)])
            _write_json(manifest_path, payload)

            with self.assertRaisesRegex(ValueError, "overlapping"):
                validate_routine_manifest(manifest_path, bilibili_manifest=root / "missing-bilibili.json")

            payload = _minimal_routine_manifest([_phase(name_zh="")])
            _write_json(manifest_path, payload)
            with self.assertRaisesRegex(ValueError, "name_zh"):
                validate_routine_manifest(manifest_path, bilibili_manifest=root / "missing-bilibili.json")

            payload = _minimal_routine_manifest([_phase(start=4.0, end=4.0)])
            _write_json(manifest_path, payload)
            with self.assertRaisesRegex(ValueError, "greater than"):
                validate_routine_manifest(manifest_path, bilibili_manifest=root / "missing-bilibili.json")

    def test_routine_split_rejects_missing_source_video(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaisesRegex(ValueError, "source video does not exist"):
                write_routine_split(
                    root / "source",
                    routine="baduanjin",
                    source_video=root / "missing.mp4",
                    dry_run=True,
                )

    def test_routine_split_prepare_assemble_and_smoke_fail_closed_without_returned_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.mp4"
            source.write_bytes(b"placeholder local Bilibili MP4 bytes")

            split = write_routine_split(
                root / "source-out",
                routine="baduanjin",
                source_video=source,
                dry_run=True,
            )
            split_manifest = json.loads(split.manifest_path.read_text(encoding="utf-8"))
            gpu = write_routine_gpu_handoffs(
                root / "gpu-runs",
                routine="baduanjin",
                clips=split.manifest_path,
            )
            html = write_routine_html(
                root / "html",
                routine="baduanjin",
                source_materializations=split.manifest_path,
            )
            smoke = smoke_check_routine_html(html.manifest_path)
            page = html.html_path.read_text(encoding="utf-8")
            gpu_manifest_exists = gpu.manifest_path.exists()

        self.assertEqual(split.phase_count, 8)
        self.assertEqual(split_manifest["phases"][0]["source_materialization_status"], "dry_run")
        self.assertTrue(gpu_manifest_exists)
        self.assertEqual(smoke.manifest_path, html.manifest_path)
        self.assertIn("SMPL-X skeleton teaching track", page)
        self.assertIn("missing gvhmr json", page)
        self.assertIn("G1 non-scoring", page)

    def test_routine_assemble_imports_matching_gvhmr_phase_and_labels_missing_gmr(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.mp4"
            source.write_bytes(b"placeholder local Bilibili MP4 bytes")
            split = write_routine_split(
                root / "source-out",
                routine="baduanjin",
                source_video=source,
                dry_run=True,
            )
            split_manifest = json.loads(split.manifest_path.read_text(encoding="utf-8"))
            first = split_manifest["phases"][0]
            materialization_path = split.manifest_path.parent / first["source_materialization"]
            materialization = json.loads(materialization_path.read_text(encoding="utf-8"))
            gvhmr_path = root / "gvhmr" / first["phase_id"] / "gvhmr-smplx-joints.json"
            _write_json(
                gvhmr_path,
                {
                    "schema": "neodojo.gvhmr_smplx_joints.v1",
                    "fixture_only": True,
                    "routine": "Baduanjin",
                    "form": first["name_en"],
                    "fps": 1,
                    "frames": build_smplx_fixture_frames(int(first["duration_seconds"])),
                    "provenance": {
                        "source_materialization_manifest": str(materialization_path),
                        "source_materialization_sha256": sha256_file(materialization_path),
                        "source_id": materialization["source_prep"]["source_id"],
                        "trim": materialization["trim"],
                        "input_video": materialization["gpu_handoff"]["trimmed_video_argument"],
                        "input_video_sha256": None,
                        "gpu_command": "fixture GVHMR export for routine assemble test",
                        "runtime": "unit test",
                        "upstream_version": "fixture",
                    },
                },
            )

            result = write_routine_html(
                root / "html",
                routine="baduanjin",
                source_materializations=split.manifest_path,
                gvhmr_json_root=root / "gvhmr",
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            smoke_check_routine_html(result.manifest_path)

        self.assertEqual(manifest["phases"][0]["gvhmr_status"], "smplx_teaching_track_generated")
        self.assertEqual(manifest["phases"][0]["g1_status"], "missing_gmr_json_fixture_fallback")
        self.assertTrue(manifest["phases"][0]["phase_public_demo"].endswith("index.html"))


class BilibiliDownloaderTests(unittest.TestCase):
    def test_ytdlp_command_preserves_cookie_options_and_stable_page_url(self) -> None:
        command = build_ytdlp_command(
            {
                "bvid": "BV1gT4y1m7ec",
                "page_url": "https://www.bilibili.com/video/BV1gT4y1m7ec/",
                "output_path": "video/bilibili/source.mp4",
            },
            output_path=Path("video/bilibili/source.mp4"),
            quality="480p",
            cookies=Path("cookies.txt"),
        )

        self.assertIn("--cookies", command)
        self.assertIn("cookies.txt", command)
        self.assertIn("height<=480", " ".join(command))
        self.assertEqual(command[-1], "https://www.bilibili.com/video/BV1gT4y1m7ec/")

        with self.assertRaisesRegex(ValueError, "either --cookies"):
            build_ytdlp_command(
                {"page_url": "https://www.bilibili.com/video/BV1gT4y1m7ec/"},
                output_path=Path("out.mp4"),
                cookies=Path("cookies.txt"),
                cookies_from_browser="chrome",
            )

    def test_bilibili_download_dry_run_writes_commands_without_yt_dlp(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = root / "manifest.json"
            cookies = root / "cookies.txt"
            cookies.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
            _write_json(
                manifest_path,
                {
                    "entries": [
                        {
                            "bvid": "BV1gT4y1m7ec",
                            "aid": 1,
                            "cid": 2,
                            "title": "八段锦",
                            "page_url": "https://www.bilibili.com/video/BV1gT4y1m7ec/",
                            "output_path": str(root / "baduanjin.mp4"),
                        }
                    ]
                },
            )

            result = write_bilibili_download_manifest(
                root / "download",
                manifest_path=manifest_path,
                routines=["baduanjin"],
                cookies=cookies,
                dry_run=True,
            )
            payload = json.loads(result.manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["status"], "dry_run")
        self.assertFalse(payload["transient_play_urls_recorded"])
        self.assertEqual(payload["entries"][0]["status"], "planned")
        self.assertIn("--cookies", payload["entries"][0]["command"])

    def test_bilibili_download_failure_is_reported_in_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = root / "manifest.json"
            _write_json(
                manifest_path,
                {
                    "entries": [
                        {
                            "bvid": "BV1gT4y1m7ec",
                            "aid": 1,
                            "cid": 2,
                            "title": "八段锦",
                            "page_url": "https://www.bilibili.com/video/BV1gT4y1m7ec/",
                            "output_path": str(root / "baduanjin.mp4"),
                        }
                    ]
                },
            )

            with patch("neodojo.bilibili.shutil.which", return_value="/usr/bin/yt-dlp"):
                with patch(
                    "neodojo.bilibili.subprocess.run",
                    return_value=SimpleNamespace(returncode=1, stdout="", stderr="download failed"),
                ):
                    with self.assertRaisesRegex(ValueError, "downloads failed"):
                        write_bilibili_download_manifest(
                            root / "download",
                            manifest_path=manifest_path,
                            routines=["baduanjin"],
                            dry_run=False,
                        )
            payload = json.loads((root / "download" / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["entries"][0]["status"], "download_failed")


if __name__ == "__main__":
    unittest.main()
