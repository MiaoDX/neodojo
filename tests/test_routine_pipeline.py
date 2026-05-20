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
        baduanjin_phases = manifest["routines"]["baduanjin"]["phases"]
        baduanjin_duration = sum(phase["duration_seconds"] for phase in baduanjin_phases)
        self.assertGreaterEqual(baduanjin_duration, 180)
        self.assertLessEqual(baduanjin_duration, 220)
        self.assertLessEqual(max(phase["duration_seconds"] for phase in baduanjin_phases), 40)
        separate = next(phase for phase in baduanjin_phases if phase["phase_id"] == "separate_heaven_earth")
        self.assertEqual(separate["start_seconds"], 240.0)

        wuqinxi_phases = manifest["routines"]["wuqinxi"]["phases"]
        wuqinxi_duration = sum(phase["duration_seconds"] for phase in wuqinxi_phases)
        self.assertGreaterEqual(wuqinxi_duration, 230)
        self.assertLessEqual(wuqinxi_duration, 270)
        self.assertLessEqual(max(phase["duration_seconds"] for phase in wuqinxi_phases), 40)
        tiger_lifting = next(phase for phase in wuqinxi_phases if phase["phase_id"] == "tiger_lifting")
        deer_colliding = next(phase for phase in wuqinxi_phases if phase["phase_id"] == "deer_colliding")
        self.assertEqual(tiger_lifting["start_seconds"], 70.0)
        self.assertEqual(deer_colliding["start_seconds"], 229.0)

        yijinjing_phases = manifest["routines"]["yijinjing"]["phases"]
        yijinjing_duration = sum(phase["duration_seconds"] for phase in yijinjing_phases)
        self.assertGreaterEqual(yijinjing_duration, 300)
        self.assertLessEqual(yijinjing_duration, 350)
        self.assertLessEqual(max(phase["duration_seconds"] for phase in yijinjing_phases), 55)
        pestle_1 = next(phase for phase in yijinjing_phases if phase["phase_id"] == "wei_tuo_presents_pestle_1")
        pluck_star = next(
            phase for phase in yijinjing_phases if phase["phase_id"] == "pluck_star_exchange_constellation"
        )
        self.assertEqual(pestle_1["start_seconds"], 40.0)
        self.assertEqual(pluck_star["start_seconds"], 100.0)

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
            manifest = json.loads(html.manifest_path.read_text(encoding="utf-8"))
            smoke = smoke_check_routine_html(html.manifest_path)
            page = html.html_path.read_text(encoding="utf-8")
            gpu_manifest_exists = gpu.manifest_path.exists()
            phases_dir_exists = (root / "html" / "phases").exists()

        self.assertEqual(split.phase_count, 8)
        self.assertEqual(split_manifest["phases"][0]["source_materialization_status"], "dry_run")
        self.assertTrue(gpu_manifest_exists)
        self.assertEqual(manifest["assembly_mode"], "self_contained_report_incomplete")
        self.assertEqual(manifest["phase_evidence_mode"], "lean_playback")
        self.assertEqual(manifest["g1_replay_fps"], 5.0)
        self.assertEqual(smoke.manifest_path, html.manifest_path)
        self.assertFalse(phases_dir_exists)
        self.assertEqual(manifest["phases"][0]["phase_report_status"], "missing_gvhmr_json")
        for phase in split_manifest["phases"]:
            self.assertIn(phase["name_zh"], page)
            self.assertIn(phase["name_en"], page)
        self.assertIn("SMPL-X skeleton teaching track", page)
        self.assertIn("missing gvhmr json", page)
        self.assertIn("G1 non-scoring", page)
        self.assertIn("Original clip", page)
        self.assertIn("Provenance", page)

    def test_routine_assemble_indexes_returned_artifacts_without_phase_demos(self) -> None:
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
            gmr_path = root / "gmr" / first["phase_id"] / "normalized" / "gmr-unitree-g1.normalized.json"
            _write_json(
                gmr_path,
                {
                    "schema": "neodojo.gmr_unitree_g1_track.v1",
                    "robot": "unitree_g1",
                    "fixture_only": False,
                    "fps": 1,
                    "frames": [],
                },
            )
            stale_phase_demo = root / "html" / "phases" / first["phase_id"] / "demo" / "index.html"
            stale_phase_demo.parent.mkdir(parents=True)
            stale_phase_demo.write_text("stale heavy phase demo", encoding="utf-8")

            result = write_routine_html(
                root / "html",
                routine="baduanjin",
                source_materializations=split.manifest_path,
                gvhmr_json_root=root / "gvhmr",
                gmr_json_root=root / "gmr",
                build_phase_demos=False,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            page = result.html_path.read_text(encoding="utf-8")
            smoke_check_routine_html(result.manifest_path)
            phases_dir_exists = (root / "html" / "phases").exists()

        first_phase = manifest["phases"][0]
        self.assertEqual(manifest["assembly_mode"], "lightweight_index")
        self.assertEqual(manifest["phase_evidence_mode"], "index_only")
        self.assertEqual(first_phase["gvhmr_status"], "gvhmr_json_available")
        self.assertEqual(first_phase["g1_status"], "gmr_json_available_non_scoring")
        self.assertEqual(first_phase["phase_report_status"], "phase_report_not_requested_index_only")
        self.assertTrue(first_phase["artifact_availability"]["gvhmr_json"])
        self.assertTrue(first_phase["artifact_availability"]["gmr_json"])
        self.assertIsNone(first_phase["phase_public_demo"])
        self.assertFalse(phases_dir_exists)
        self.assertIn("GVHMR SMPL-X JSON available", page)
        self.assertIn("GMR Unitree G1 JSON available", page)
        self.assertIn(first_phase["gvhmr_json"], page)
        self.assertIn(first_phase["gmr_json"], page)

    def test_routine_assemble_labels_stale_returned_artifacts(self) -> None:
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
                        "source_materialization_sha256": "stale-source-materialization-sha",
                    },
                },
            )
            gmr_path = root / "gmr" / first["phase_id"] / "normalized" / "gmr-unitree-g1.normalized.json"
            _write_json(gmr_path, {"schema": "neodojo.gmr_unitree_g1_track.v1", "robot": "unitree_g1"})

            result = write_routine_html(
                root / "html",
                routine="baduanjin",
                source_materializations=split.manifest_path,
                gvhmr_json_root=root / "gvhmr",
                gmr_json_root=root / "gmr",
                build_phase_demos=False,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

        first_phase = manifest["phases"][0]
        self.assertEqual(first_phase["gvhmr_status"], "gvhmr_json_stale_for_current_source")
        self.assertEqual(first_phase["g1_status"], "gmr_json_available_but_smplx_source_stale")
        self.assertFalse(first_phase["artifact_current"]["gvhmr_json"])
        self.assertFalse(first_phase["artifact_current"]["gmr_json"])

    def test_routine_assemble_builds_lean_phase_reports_by_default(self) -> None:
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
            for phase in split_manifest["phases"]:
                materialization_path = split.manifest_path.parent / phase["source_materialization"]
                materialization = json.loads(materialization_path.read_text(encoding="utf-8"))
                gvhmr_path = root / "gvhmr" / phase["phase_id"] / "gvhmr-smplx-joints.json"
                _write_json(
                    gvhmr_path,
                    {
                        "schema": "neodojo.gvhmr_smplx_joints.v1",
                        "fixture_only": True,
                        "routine": "Baduanjin",
                        "form": phase["name_en"],
                        "fps": 1,
                        "frames": build_smplx_fixture_frames(int(phase["duration_seconds"])),
                        "provenance": {
                            "source_materialization_sha256": sha256_file(materialization_path),
                            "source_id": materialization["source_prep"]["source_id"],
                            "trim": materialization["trim"],
                        },
                    },
                )
                _write_json(
                    root / "gmr" / phase["phase_id"] / "normalized" / "gmr-unitree-g1.normalized.json",
                    {
                        "schema": "neodojo.gmr_unitree_g1_track.v1",
                        "robot": "unitree_g1",
                        "fixture_only": False,
                        "fps": 1,
                        "frames": [],
                    },
                )

            seen_replay_fps: list[object] = []
            fake_report_roots: list[Path] = []

            def fake_demo(out_dir: Path, **kwargs: object) -> SimpleNamespace:
                seen_replay_fps.append(kwargs.get("g1_replay_fps"))
                fake_report_roots.append(out_dir)
                manifest_path = out_dir / "manifest.json"
                public_manifest_path = out_dir / "public-demo" / "manifest.json"
                index_path = out_dir / "public-demo" / "index.html"
                source_video_path = out_dir / "public-demo" / "source-video" / "original.mp4"
                g1_video_path = out_dir / "public-demo" / "g1-replay-video" / "front.mp4"
                source_video_path.parent.mkdir(parents=True, exist_ok=True)
                g1_video_path.parent.mkdir(parents=True, exist_ok=True)
                source_video_path.write_bytes(b"source clip")
                g1_video_path.write_bytes(b"g1 mp4")
                _write_json(
                    public_manifest_path,
                    {
                        "html": "index.html",
                        "scene": "scene.json",
                        "recording": "neodojo-demo.rrd",
                        "source_manifests": {
                            "motion_record": "../motion-contract/motion-record/manifest.json",
                            "g1_track": "../../g1-import/tracks/g1/manifest.json",
                        },
                        "teaching_html": {
                            "g1_replay": {
                                "actual_g1_model_replay": True,
                                "video": {
                                    "available": True,
                                    "path": "g1-replay-video/front.mp4",
                                },
                            }
                        },
                    },
                )
                (out_dir / "public-demo" / "scene.json").write_text("scene", encoding="utf-8")
                (out_dir / "public-demo" / "neodojo-demo.rrd").write_text("recording", encoding="utf-8")
                index_path.write_text(
                    "Original video SMPL-X skeleton teaching track Unitree G1 MuJoCo model replay G1 non-scoring",
                    encoding="utf-8",
                )
                (out_dir / "teaching-demo").mkdir(parents=True)
                (out_dir / "teaching-demo" / "index.html").write_text("duplicate teaching html", encoding="utf-8")
                _write_json(out_dir / "motion-contract" / "motion-record" / "manifest.json", {"motion": True})
                (out_dir / "motion-contract" / "motion-record" / "smplx-parameters.json").write_text(
                    "parameters",
                    encoding="utf-8",
                )
                (out_dir / "real-conversion-validation").mkdir(parents=True)
                (out_dir / "real-conversion-validation" / "gvhmr-smplx-joints.validated.json").write_text(
                    "validated",
                    encoding="utf-8",
                )
                (out_dir / "smplx-surface" / "surfaces" / "smplx").mkdir(parents=True)
                (out_dir / "smplx-surface" / "surfaces" / "smplx" / "surface-proxy.json").write_text(
                    "surface",
                    encoding="utf-8",
                )
                (out_dir / "viser-runtime").mkdir(parents=True)
                (out_dir / "viser-runtime" / "scene.json").write_text("viser scene", encoding="utf-8")
                (out_dir.parent / "g1-import" / "tracks" / "g1").mkdir(parents=True)
                (out_dir.parent / "g1-import" / "tracks" / "g1" / "joints.json").write_text(
                    "joints",
                    encoding="utf-8",
                )
                (out_dir.parent / "preimport-motion-contract" / "motion-record").mkdir(parents=True)
                (out_dir.parent / "preimport-motion-contract" / "motion-record" / "smplx-parameters.json").write_text(
                    "preimport",
                    encoding="utf-8",
                )
                _write_json(
                    manifest_path,
                    {
                        "public_demo": "public-demo/manifest.json",
                        "actual_g1_model_replay": True,
                        "motion_record": "motion-contract/motion-record/manifest.json",
                        "g1_track": "../g1-import/tracks/g1/manifest.json",
                        "smplx_surface": "smplx-surface/surfaces/smplx/manifest.json",
                        "source_validation": "real-conversion-validation/source-validation.json",
                        "g1_render": "g1-mujoco-render/manifest.json",
                    },
                )
                return SimpleNamespace(
                    manifest_path=manifest_path,
                    checked_paths=[
                        index_path,
                        out_dir / "public-demo" / "scene.json",
                        out_dir / "public-demo" / "neodojo-demo.rrd",
                    ],
                )

            with patch(
                "neodojo.routine.write_gvhmr_json_motion_contract",
                return_value=SimpleNamespace(out_dir=root / "motion"),
            ), patch(
                "neodojo.routine.import_gmr_json_track",
                return_value=SimpleNamespace(track_manifest_path=root / "g1-track" / "manifest.json"),
            ), patch("neodojo.routine.write_real_conversion_demo", side_effect=fake_demo):
                result = write_routine_html(
                    root / "html",
                    routine="baduanjin",
                    source_materializations=split.manifest_path,
                    gvhmr_json_root=root / "gvhmr",
                    gmr_json_root=root / "gmr",
                    model_descriptor=root / "g1-model" / "manifest.json",
                    render_mujoco=True,
                    g1_replay_fps=10,
                )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            page = result.html_path.read_text(encoding="utf-8")
            smoke_check_routine_html(result.manifest_path)
            first_report = fake_report_roots[0]
            phase_report_manifest = json.loads((first_report / "manifest.json").read_text(encoding="utf-8"))
            public_manifest = json.loads((first_report / "public-demo" / "manifest.json").read_text(encoding="utf-8"))
            lean_state = {
                "public_index": (first_report / "public-demo" / "index.html").exists(),
                "source_video": (first_report / "public-demo" / "source-video" / "original.mp4").exists(),
                "g1_video": (first_report / "public-demo" / "g1-replay-video" / "front.mp4").exists(),
                "prune_manifest": (first_report / "routine-lean-report.json").exists(),
                "scene": (first_report / "public-demo" / "scene.json").exists(),
                "recording": (first_report / "public-demo" / "neodojo-demo.rrd").exists(),
                "teaching_demo": (first_report / "teaching-demo").exists(),
                "motion_contract": (first_report / "motion-contract").exists(),
                "validation": (first_report / "real-conversion-validation").exists(),
                "surface": (first_report / "smplx-surface").exists(),
                "viser": (first_report / "viser-runtime").exists(),
                "g1_import": (first_report.parent / "g1-import").exists(),
                "preimport": (first_report.parent / "preimport-motion-contract").exists(),
            }

        self.assertEqual(manifest["assembly_mode"], "self_contained_report")
        self.assertEqual(manifest["phase_evidence_mode"], "lean_playback")
        self.assertFalse(manifest["preserve_phase_evidence"])
        self.assertTrue(manifest["phase_evidence_pruned"])
        self.assertEqual(manifest["g1_replay_fps"], 10)
        self.assertTrue(manifest["report_complete"])
        self.assertTrue(manifest["actual_g1_model_replay_complete"])
        self.assertEqual(seen_replay_fps, [10] * 8)
        self.assertTrue(all(phase["phase_report"] for phase in manifest["phases"]))
        self.assertTrue(all(phase["actual_g1_model_replay"] for phase in manifest["phases"]))
        self.assertTrue(all(phase["phase_evidence_mode"] == "lean_playback" for phase in manifest["phases"]))
        self.assertGreater(manifest["phase_evidence_pruned_artifact_count"], 0)
        self.assertTrue(lean_state["public_index"])
        self.assertTrue(lean_state["source_video"])
        self.assertTrue(lean_state["g1_video"])
        self.assertTrue(lean_state["prune_manifest"])
        self.assertFalse(lean_state["scene"])
        self.assertFalse(lean_state["recording"])
        self.assertFalse(lean_state["teaching_demo"])
        self.assertFalse(lean_state["motion_contract"])
        self.assertFalse(lean_state["validation"])
        self.assertFalse(lean_state["surface"])
        self.assertFalse(lean_state["viser"])
        self.assertFalse(lean_state["g1_import"])
        self.assertFalse(lean_state["preimport"])
        self.assertEqual(phase_report_manifest["routine_report_mode"], "lean_self_contained_playback")
        self.assertIsNone(phase_report_manifest["motion_record"])
        self.assertIsNone(phase_report_manifest["g1_track"])
        self.assertIsNone(public_manifest["scene"])
        self.assertIsNone(public_manifest["recording"])
        self.assertIn("Open phase report", page)
        self.assertIn("G1 Model Replay", page)
        self.assertIn("lean playback", page)


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
