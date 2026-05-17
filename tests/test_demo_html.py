from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from neodojo.demo_html import build_fixture, compute_feedback, render_demo_html, write_demo
from neodojo.motion_contract import validate_output_dir, validate_scoring_source, write_fixture_motion_contract


class DemoHtmlTests(unittest.TestCase):
    def test_fixture_preserves_scoring_boundary(self) -> None:
        fixture = build_fixture(frame_count=16)

        self.assertTrue(fixture["fixture_only"])
        self.assertEqual(fixture["scoring_source"], "smplx")
        self.assertIn("teaching accuracy source", fixture["tracks"]["smplx"]["role"])
        self.assertIn("derived visual companion", fixture["tracks"]["g1"]["role"])
        self.assertEqual(len(fixture["tracks"]["smplx"]["frames"]), 16)
        self.assertEqual(len(fixture["tracks"]["g1"]["frames"]), 16)

    def test_feedback_uses_smplx_key_frame(self) -> None:
        fixture = build_fixture(frame_count=16)
        key_frame = fixture["key_frame"]
        smplx_frame = fixture["tracks"]["smplx"]["frames"][key_frame]

        feedback = compute_feedback(smplx_frame)

        self.assertEqual(feedback["source"], "smplx")
        self.assertTrue(feedback["passed"])
        self.assertGreaterEqual(feedback["shoulder_clearance_m"], 0.08)
        self.assertGreaterEqual(feedback["elbow_drop_m"], 0.18)

    def test_rendered_html_is_self_contained(self) -> None:
        html = render_demo_html(build_fixture(frame_count=12))

        self.assertIn("neodojo fixture teaching demo", html)
        self.assertIn("SMPL-X teacher", html)
        self.assertIn("Unitree G1 visual", html)
        self.assertIn("const DEMO =", html)
        self.assertNotIn("__NEODOJO_DEMO_DATA__", html)
        self.assertNotIn("fetch(", html)

    def test_write_demo_outputs_html_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = write_demo(Path(temp_dir), frame_count=12)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            motion_record = json.loads(result.motion_record_manifest_path.read_text(encoding="utf-8"))
            smplx_track = json.loads(result.smplx_track_manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(result.html_path.name, "index.html")
        self.assertTrue(manifest["fixture_only"])
        self.assertEqual(manifest["scoring_source"], "smplx")
        self.assertEqual(manifest["frame_count"], 12)
        self.assertEqual(manifest["motion_record"], "motion-record/manifest.json")
        self.assertEqual(manifest["tracks"]["smplx"]["manifest"], "tracks/smplx/manifest.json")
        self.assertEqual(manifest["tracks"]["g1"]["manifest"], None)
        self.assertEqual(motion_record["scoring_source"], "smplx")
        self.assertEqual(motion_record["frame_count"], 12)
        self.assertTrue(smplx_track["scoring_allowed"])
        self.assertEqual(smplx_track["source_motion_record"], "../../motion-record/manifest.json")

    def test_fixture_motion_contract_outputs_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = write_fixture_motion_contract(Path(temp_dir), frame_count=10)
            motion_record = json.loads(result.motion_record_manifest_path.read_text(encoding="utf-8"))
            smplx_track = json.loads(result.smplx_track_manifest_path.read_text(encoding="utf-8"))
            track_data = json.loads(result.smplx_track_data_path.read_text(encoding="utf-8"))

        self.assertTrue(motion_record["fixture_only"])
        self.assertEqual(motion_record["source_type"], "synthetic_fixture")
        self.assertEqual(motion_record["scoring_source"], "smplx")
        self.assertEqual(motion_record["data_files"]["smplx_frames"], "smplx-joints.json")
        self.assertEqual(smplx_track["track_id"], "smplx")
        self.assertTrue(smplx_track["scoring_allowed"])
        self.assertEqual(smplx_track["data_files"]["frames"], "joints.json")
        self.assertEqual(len(track_data["frames"]), 10)

    def test_rejects_non_smplx_scoring_source(self) -> None:
        smplx = {"track_id": "smplx", "scoring_allowed": True}
        g1 = {"track_id": "g1", "scoring_allowed": False}

        validate_scoring_source({"smplx": smplx, "g1": g1})

        with self.assertRaisesRegex(ValueError, "only allowed scoring source"):
            validate_scoring_source({"smplx": smplx, "g1": g1}, scoring_source="g1")

        with self.assertRaisesRegex(ValueError, "derived visual tracks"):
            validate_scoring_source({"smplx": smplx, "g1": {"track_id": "g1", "scoring_allowed": True}})

    def test_rejects_repo_output_outside_outputs_dir(self) -> None:
        with self.assertRaisesRegex(ValueError, "under outputs"):
            validate_output_dir(Path("src/generated-motion-contract"))


if __name__ == "__main__":
    unittest.main()
