from __future__ import annotations

import json
import pickle
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from neodojo.g1_visual import import_gmr_json_track
from neodojo.gmr_native import (
    GMR_LOCAL_RUN_SCHEMA,
    GMR_NATIVE_ADAPTER_REPORT_SCHEMA,
    UNITREE_G1_29DOF_JOINT_NAMES,
    normalize_gmr_pickle,
    run_local_gmr_unitree_g1,
)
from neodojo.motion_contract import _timing_metadata
from neodojo.motion_contract import write_fixture_motion_contract


def _write_native_gmr_pickle(path: Path, frame_count: int, *, fps: int = 24, dof_count: int = 29) -> None:
    payload = {
        "fps": fps,
        "root_pos": [[0.01 * index, 0.0, 0.9] for index in range(frame_count)],
        "root_rot": [[0.0, 0.0, 0.0, 1.0] for _ in range(frame_count)],
        "dof_pos": [
            [round(0.001 * (index + joint), 6) for joint in range(dof_count)]
            for index in range(frame_count)
        ],
        "local_body_pos": None,
        "link_body_list": None,
    }
    with path.open("wb") as file:
        pickle.dump(payload, file)


class GMRNativeTests(unittest.TestCase):
    def test_normalize_gmr_pickle_writes_importable_g1_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            source = root / "gmr-motion.pkl"
            _write_native_gmr_pickle(source, frame_count=10)

            result = normalize_gmr_pickle(root / "native", source, motion_record=motion.out_dir)
            imported = import_gmr_json_track(
                root / "g1",
                result.normalized_export_path,
                motion_record=motion.out_dir,
            )
            normalized = json.loads(result.normalized_export_path.read_text(encoding="utf-8"))
            report = json.loads(result.report_path.read_text(encoding="utf-8"))
            track = json.loads(imported.track_manifest_path.read_text(encoding="utf-8"))
            data = json.loads(imported.track_data_path.read_text(encoding="utf-8"))

        self.assertEqual(normalized["schema"], "neodojo.gmr_unitree_g1_track.v1")
        self.assertEqual(normalized["provenance"]["native_format"], "YanjieZe/GMR robot motion pickle")
        self.assertEqual(normalized["provenance"]["joint_name_source"], "unitree_g1_29dof_default")
        self.assertEqual(report["schema"], GMR_NATIVE_ADAPTER_REPORT_SCHEMA)
        self.assertEqual(report["joint_angle_count"], 29)
        self.assertEqual(report["joint_angle_names"], UNITREE_G1_29DOF_JOINT_NAMES)
        self.assertFalse(report["g1_scoring_allowed"])
        self.assertEqual(track["pose_stream"]["joint_angle_count"], 29)
        self.assertFalse(track["scoring_allowed"])
        self.assertEqual(len(data["joint_angles"]), 10)
        self.assertIn("left_hip_pitch_joint", data["joint_angles"][0])

    def test_normalize_gmr_pickle_uses_motion_record_fps_for_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            manifest_path = motion.motion_record_manifest_path
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["fps"] = 25
            manifest["timing"] = _timing_metadata(25, 10)
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            source = root / "gmr-motion.pkl"
            _write_native_gmr_pickle(source, frame_count=10, fps=30)

            result = normalize_gmr_pickle(root / "native", source, motion_record=motion.out_dir)
            normalized = json.loads(result.normalized_export_path.read_text(encoding="utf-8"))
            report = json.loads(result.report_path.read_text(encoding="utf-8"))

        self.assertEqual(normalized["fps"], 25)
        self.assertEqual(normalized["provenance"]["native_fps"], 30)
        self.assertEqual(report["native_fps"], 30)
        self.assertFalse(report["native_fps_match"])

    def test_normalize_gmr_pickle_rejects_frame_count_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            source = root / "gmr-motion.pkl"
            _write_native_gmr_pickle(source, frame_count=9)

            with self.assertRaisesRegex(ValueError, "frame count"):
                normalize_gmr_pickle(root / "native", source, motion_record=motion.out_dir)

    def test_normalize_gmr_pickle_requires_joint_names_for_unknown_dof_width(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            source = root / "gmr-motion.pkl"
            _write_native_gmr_pickle(source, frame_count=10, dof_count=2)

            with self.assertRaisesRegex(ValueError, "joint names"):
                normalize_gmr_pickle(root / "native", source, motion_record=motion.out_dir)

            result = normalize_gmr_pickle(
                root / "native-custom",
                source,
                motion_record=motion.out_dir,
                joint_names=["left_test_joint", "right_test_joint"],
            )
            normalized = json.loads(result.normalized_export_path.read_text(encoding="utf-8"))

        self.assertEqual(
            list(normalized["frames"][0]["joint_angles"]),
            ["left_test_joint", "right_test_joint"],
        )

    def test_run_local_gmr_unitree_g1_writes_prepared_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            gvhmr_result = root / "hmr4d_results.pt"
            gvhmr_result.write_bytes(b"native GVHMR placeholder")

            result = run_local_gmr_unitree_g1(
                root / "gmr-run",
                motion_record=motion.out_dir,
                gvhmr_result=gvhmr_result,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(result.status, "prepared_missing_gmr_repo")
        self.assertEqual(manifest["schema"], GMR_LOCAL_RUN_SCHEMA)
        self.assertFalse(manifest["execute"])
        self.assertIn("gvhmr_to_robot.py", " ".join(manifest["command"]))
        self.assertIn("tracks import-gmr-json", manifest["next_commands"]["import_gmr_json"])
        self.assertIsNone(manifest["normalized_export"])

    def test_run_local_gmr_unitree_g1_execute_uses_headless_runner(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            gvhmr_result = root / "hmr4d_results.pt"
            gvhmr_result.write_bytes(b"native GVHMR placeholder")
            body_models = root / "body-models"
            body_models.mkdir()

            def fake_headless_runner(**kwargs):
                _write_native_gmr_pickle(kwargs["native_artifact_path"], frame_count=10, fps=30)
                return {
                    "runner": "neodojo_headless_gmr_library.v1",
                    "frame_count": 10,
                    "fps": 30,
                    "opened_viewer": False,
                }

            with patch("neodojo.gmr_native._run_headless_gmr_unitree_g1", side_effect=fake_headless_runner):
                result = run_local_gmr_unitree_g1(
                    root / "gmr-run",
                    motion_record=motion.out_dir,
                    gvhmr_result=gvhmr_result,
                    body_models=body_models,
                    execute=True,
                )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(result.status, "normalized")
        self.assertEqual(manifest["runner"], "neodojo_headless_gmr_library.v1")
        self.assertFalse(manifest["completed_process"]["opened_viewer"])
        self.assertIsNotNone(manifest["normalized_export"])
        self.assertIsNotNone(result.normalized_export_path)


if __name__ == "__main__":
    unittest.main()
