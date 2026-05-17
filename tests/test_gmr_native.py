from __future__ import annotations

import json
import pickle
import tempfile
import unittest
from pathlib import Path

from neodojo.g1_visual import import_gmr_json_track
from neodojo.gmr_native import (
    GMR_NATIVE_ADAPTER_REPORT_SCHEMA,
    UNITREE_G1_29DOF_JOINT_NAMES,
    normalize_gmr_pickle,
)
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


if __name__ == "__main__":
    unittest.main()
