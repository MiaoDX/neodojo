from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from neodojo.demo_html import build_fixture, compute_feedback, render_demo_html, write_demo
from neodojo.g1_visual import build_g1_visual_track, register_g1_model, write_fixture_g1_model_descriptor
from neodojo.motion_contract import validate_output_dir, validate_scoring_source, write_fixture_motion_contract
from neodojo.teaching_playback import write_teaching_playback_demo


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

    def test_fixture_g1_model_descriptor(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = write_fixture_g1_model_descriptor(Path(temp_dir))
            descriptor = json.loads(result.descriptor_path.read_text(encoding="utf-8"))

        self.assertTrue(descriptor["fixture_only"])
        self.assertEqual(descriptor["robot"], "unitree_g1")
        self.assertEqual(descriptor["model_format"], "fixture_descriptor")
        self.assertTrue(descriptor["validation"]["loadable"])

    def test_register_g1_model_from_tiny_urdf(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            mesh_dir = root / "meshes"
            mesh_dir.mkdir()
            mesh = mesh_dir / "body.stl"
            mesh.write_text("solid fixture\nendsolid fixture\n", encoding="utf-8")
            model = root / "g1_fixture.urdf"
            model.write_text(
                """<robot name="unitree_g1_fixture">
  <link name="pelvis">
    <visual><geometry><mesh filename="meshes/body.stl"/></geometry></visual>
  </link>
  <link name="torso"/>
  <joint name="waist_yaw_joint" type="revolute">
    <parent link="pelvis"/>
    <child link="torso"/>
  </joint>
</robot>
""",
                encoding="utf-8",
            )

            result = register_g1_model(
                root / "out",
                model,
                source_url="https://example.invalid/unitree-g1",
                source_revision="fixture",
                license_name="fixture",
                variant="test fixture",
            )
            descriptor = json.loads(result.descriptor_path.read_text(encoding="utf-8"))

        self.assertFalse(descriptor["fixture_only"])
        self.assertEqual(descriptor["model_format"], "urdf")
        self.assertEqual(descriptor["joint_count"], 1)
        self.assertEqual(descriptor["root_name"], "pelvis")
        self.assertEqual(descriptor["validation"]["missing_assets"], [])

    def test_register_g1_model_rejects_missing_mesh(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            model = root / "g1_fixture.urdf"
            model.write_text(
                """<robot name="unitree_g1_fixture">
  <link name="pelvis">
    <visual><geometry><mesh filename="missing/body.stl"/></geometry></visual>
  </link>
</robot>
""",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "missing mesh assets"):
                register_g1_model(root / "out", model)

    def test_build_g1_visual_track_from_motion_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            model = write_fixture_g1_model_descriptor(root / "model")
            result = build_g1_visual_track(
                motion.out_dir,
                root / "g1",
                model_descriptor_path=model.descriptor_path,
            )
            track = json.loads(result.track_manifest_path.read_text(encoding="utf-8"))
            report = json.loads(result.comparison_report_path.read_text(encoding="utf-8"))
            data = json.loads(result.track_data_path.read_text(encoding="utf-8"))

        self.assertEqual(track["track_id"], "g1")
        self.assertEqual(track["robot"], "unitree_g1")
        self.assertFalse(track["scoring_allowed"])
        self.assertEqual(track["derived_from"], "smplx")
        self.assertEqual(track["frame_count"], 10)
        self.assertEqual(len(data["frames"]), 10)
        self.assertEqual(report["canonical_track"], "smplx")
        self.assertFalse(report["g1_scoring_allowed"])
        self.assertTrue(report["frame_count_match"])

    def test_write_teaching_playback_demo_from_track_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            model = write_fixture_g1_model_descriptor(root / "model")
            g1 = build_g1_visual_track(
                motion.out_dir,
                root / "g1",
                model_descriptor_path=model.descriptor_path,
            )
            annotations = root / "annotations.json"
            annotations.write_text('{"name": "fixture key frame", "key_frame": 5}\n', encoding="utf-8")

            result = write_teaching_playback_demo(
                root / "teaching-demo",
                motion.out_dir,
                g1.track_manifest_path,
                annotations_path=annotations,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            html = result.html_path.read_text(encoding="utf-8")

        self.assertEqual(manifest["frame_count"], 10)
        self.assertEqual(manifest["key_frame"], 5)
        self.assertEqual(manifest["scoring_source"], "smplx")
        self.assertFalse(manifest["tracks"]["g1"]["scoring_allowed"])
        self.assertEqual(manifest["annotation_name"], "fixture key frame")
        self.assertEqual(manifest["evidence"]["rendered_tracks"], ["smplx", "g1"])
        self.assertIn("Unitree G1 visual", html)


if __name__ == "__main__":
    unittest.main()
