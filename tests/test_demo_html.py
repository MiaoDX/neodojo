from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from neodojo.annotations import detect_opening_form_keyframe, write_detected_annotations
from neodojo.demo_html import build_fixture, compute_feedback, render_demo_html, write_demo
from neodojo.fixtures import TEACHING_JOINTS, build_smplx_fixture_frames, derive_g1_like_frame
from neodojo.g1_render import write_g1_render
from neodojo.g1_visual import (
    build_g1_visual_track,
    import_gmr_json_track,
    register_g1_model,
    write_fixture_g1_model_descriptor,
)
from neodojo.motion_contract import (
    load_motion_record_frames,
    validate_output_dir,
    validate_scoring_source,
    write_fixture_motion_contract,
    write_gvhmr_json_motion_contract,
)
from neodojo.public_demo import build_scene_timeline, smoke_check_public_demo, write_public_demo
from neodojo.real_conversion import (
    _parse_ffprobe_payload,
    materialize_real_conversion_source,
    write_real_conversion_prep,
)
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

    def test_gvhmr_json_motion_contract_outputs_non_fixture_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "gvhmr-smplx-joints.json"
            source.write_text(
                json.dumps(
                    {
                        "schema": "neodojo.gvhmr_smplx_joints.v1",
                        "routine": "Baduanjin",
                        "form": "Two Hands Hold Up the Heavens",
                        "fps": 30,
                        "frames": build_smplx_fixture_frames(10),
                        "provenance": {
                            "gvhmr_results": "hmr4d_results.pt",
                            "exporter": "test fixture",
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = write_gvhmr_json_motion_contract(root / "motion", source)
            motion_record = json.loads(result.motion_record_manifest_path.read_text(encoding="utf-8"))
            smplx_track = json.loads(result.smplx_track_manifest_path.read_text(encoding="utf-8"))
            track_data = json.loads(result.smplx_track_data_path.read_text(encoding="utf-8"))

        self.assertFalse(motion_record["fixture_only"])
        self.assertEqual(motion_record["source_type"], "gvhmr_smplx_joints_json")
        self.assertEqual(motion_record["fps"], 30)
        self.assertEqual(motion_record["provenance"]["gvhmr_results"], "hmr4d_results.pt")
        self.assertFalse(smplx_track["fixture_only"])
        self.assertEqual(len(track_data["frames"]), 10)

    def test_gvhmr_json_motion_contract_rejects_missing_teaching_joint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            frames = build_smplx_fixture_frames(8)
            del frames[0][TEACHING_JOINTS[0]]
            source = root / "bad-gvhmr-smplx-joints.json"
            source.write_text(
                json.dumps({"schema": "neodojo.gvhmr_smplx_joints.v1", "frames": frames}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "missing teaching joints"):
                write_gvhmr_json_motion_contract(root / "motion", source)

    def test_gvhmr_json_motion_contract_rejects_future_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "future-gvhmr-smplx-joints.json"
            source.write_text(
                json.dumps({"schema": "neodojo.gvhmr_smplx_joints.v2", "frames": build_smplx_fixture_frames(8)}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "must use schema neodojo.gvhmr_smplx_joints.v1"):
                write_gvhmr_json_motion_contract(root / "motion", source)

    def test_gvhmr_json_motion_contract_rejects_missing_export_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaisesRegex(ValueError, "does not exist"):
                write_gvhmr_json_motion_contract(root / "motion", root / "missing.json")

    def test_motion_contract_rejects_future_manifest_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = write_fixture_motion_contract(root / "motion", frame_count=10)
            manifest = json.loads(result.motion_record_manifest_path.read_text(encoding="utf-8"))
            manifest["schema"] = "neodojo.motion_record.v2"
            result.motion_record_manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "must use schema neodojo.motion_record.v1"):
                load_motion_record_frames(result.motion_record_manifest_path)

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

    def test_import_gmr_json_track_from_motion_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            _, smplx_frames = load_motion_record_frames(motion.motion_record_manifest_path)
            source = root / "gmr-unitree-g1.json"
            source.write_text(
                json.dumps(
                    {
                        "schema": "neodojo.gmr_unitree_g1_track.v1",
                        "robot": "unitree_g1",
                        "fps": 24,
                        "frames": [
                            {
                                "visual_joints": derive_g1_like_frame(frame),
                                "joint_angles": {
                                    "left_hip_pitch_joint": index * 0.01,
                                    "right_hip_pitch_joint": -index * 0.01,
                                    "waist_yaw_joint": 0.0,
                                },
                            }
                            for index, frame in enumerate(smplx_frames)
                        ],
                        "provenance": {"gmr_command": "fixture export"},
                    }
                ),
                encoding="utf-8",
            )

            result = import_gmr_json_track(root / "g1", source, motion_record=motion.out_dir)
            track = json.loads(result.track_manifest_path.read_text(encoding="utf-8"))
            data = json.loads(result.track_data_path.read_text(encoding="utf-8"))
            report = json.loads(result.comparison_report_path.read_text(encoding="utf-8"))

        self.assertFalse(track["fixture_only"])
        self.assertEqual(track["derivation"], "imported_gmr_unitree_g1")
        self.assertFalse(track["scoring_allowed"])
        self.assertEqual(track["pose_stream"]["kind"], "unitree_g1_joint_angles")
        self.assertEqual(track["pose_stream"]["joint_angle_count"], 3)
        self.assertEqual(len(data["frames"]), 10)
        self.assertEqual(len(data["joint_angles"]), 10)
        self.assertTrue(report["frame_count_match"])
        self.assertTrue(report["fps_match"])

    def test_import_gmr_json_track_rejects_missing_joint_angles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            frames = build_smplx_fixture_frames(10)
            source = root / "bad-gmr-unitree-g1.json"
            source.write_text(
                json.dumps(
                    {
                        "schema": "neodojo.gmr_unitree_g1_track.v1",
                        "robot": "unitree_g1",
                        "frames": [{"visual_joints": derive_g1_like_frame(frame)} for frame in frames],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "joint_angles"):
                import_gmr_json_track(root / "g1", source)

    def test_write_g1_render_from_registered_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            mesh_dir = root / "meshes"
            mesh_dir.mkdir()
            (mesh_dir / "body.stl").write_text("solid fixture\nendsolid fixture\n", encoding="utf-8")
            model_file = root / "g1_fixture.urdf"
            model_file.write_text(
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
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            model = register_g1_model(root / "model", model_file)
            g1 = build_g1_visual_track(
                motion.out_dir,
                root / "g1",
                model_descriptor_path=model.descriptor_path,
            )

            result = write_g1_render(
                root / "render",
                model_descriptor_path=model.descriptor_path,
                g1_track=g1.track_manifest_path,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            html = result.html_path.read_text(encoding="utf-8")
            front_svg = result.frame_paths["front"].read_text(encoding="utf-8")

        self.assertTrue(manifest["fixture_only"])
        self.assertFalse(manifest["model_fixture_only"])
        self.assertTrue(manifest["track_fixture_only"])
        self.assertEqual(manifest["renderer"]["backend"], "neodojo_svg_schematic.v1")
        self.assertEqual(manifest["model_format"], "urdf")
        self.assertFalse(manifest["g1_scoring_allowed"])
        self.assertIn("neodojo G1 render evidence", html)
        self.assertIn("registered model", front_svg)

    def test_write_g1_render_rejects_fixture_model_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            model = write_fixture_g1_model_descriptor(root / "model")
            g1 = build_g1_visual_track(
                motion.out_dir,
                root / "g1",
                model_descriptor_path=model.descriptor_path,
            )

            with self.assertRaisesRegex(ValueError, "allow-fixture-model"):
                write_g1_render(
                    root / "render",
                    model_descriptor_path=model.descriptor_path,
                    g1_track=g1.track_manifest_path,
                )

    def test_write_g1_render_allows_fixture_model_for_ci_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            model = write_fixture_g1_model_descriptor(root / "model")
            g1 = build_g1_visual_track(
                motion.out_dir,
                root / "g1",
                model_descriptor_path=model.descriptor_path,
            )

            result = write_g1_render(
                root / "render",
                model_descriptor_path=model.descriptor_path,
                g1_track=g1.track_manifest_path,
                allow_fixture_model=True,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            front_exists = result.frame_paths["front"].exists()

        self.assertTrue(manifest["fixture_only"])
        self.assertTrue(manifest["model_fixture_only"])
        self.assertTrue(front_exists)

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
        self.assertEqual(manifest["schema"], "neodojo.playback_manifest.v1")
        self.assertEqual(manifest["key_frame"], 5)
        self.assertEqual(manifest["scoring_source"], "smplx")
        self.assertFalse(manifest["tracks"]["g1"]["scoring_allowed"])
        self.assertEqual(manifest["annotation_name"], "fixture key frame")
        self.assertEqual(manifest["annotation_manifest"]["schema"], "neodojo.annotation.v1")
        self.assertIn("coordinates", manifest)
        self.assertIn("contact", manifest)
        self.assertEqual(manifest["evidence"]["rendered_tracks"], ["smplx", "g1"])
        self.assertIn("Unitree G1 visual", html)

    def test_teaching_playback_accepts_annotation_manifest_and_reference_video(self) -> None:
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
            annotations.write_text(
                json.dumps(
                    {
                        "schema": "neodojo.annotation.v1",
                        "keyframes": [
                            {
                                "name": "raise hands apex",
                                "frame": 6,
                                "terms": ["sink shoulders", "drop elbows"],
                                "constraints": [{"source": "smplx", "kind": "elbow_drop"}],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            reference = root / "reference.mp4"
            reference.write_bytes(b"fixture reference video bytes")

            result = write_teaching_playback_demo(
                root / "teaching-demo",
                motion.out_dir,
                g1.track_manifest_path,
                annotations_path=annotations,
                reference_video=reference,
                reference_trim_start_seconds=1.25,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["key_frame"], 6)
        self.assertEqual(manifest["annotation_name"], "raise hands apex")
        self.assertEqual(manifest["reference_video_sync"]["media"]["suffix"], ".mp4")
        self.assertEqual(manifest["reference_video_sync"]["trim_start_seconds"], 1.25)
        self.assertEqual(len(manifest["reference_video_sync"]["media"]["sha256"]), 64)

    def test_detected_annotations_drive_teaching_playback_key_frame(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            _, smplx_frames = load_motion_record_frames(motion.motion_record_manifest_path)
            model = write_fixture_g1_model_descriptor(root / "model")
            g1 = build_g1_visual_track(
                motion.out_dir,
                root / "g1",
                model_descriptor_path=model.descriptor_path,
            )

            annotation_result = write_detected_annotations(root / "annotations", motion.out_dir)
            annotations = json.loads(annotation_result.manifest_path.read_text(encoding="utf-8"))
            playback = write_teaching_playback_demo(
                root / "teaching-demo",
                motion.out_dir,
                g1.track_manifest_path,
                annotations_path=annotation_result.manifest_path,
            )
            feedback_report_exists = annotation_result.feedback_report_path.exists()
            feedback_report = json.loads(annotation_result.feedback_report_path.read_text(encoding="utf-8"))
            manifest = json.loads(playback.manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(detect_opening_form_keyframe(smplx_frames), 9)
        self.assertEqual(annotations["schema"], "neodojo.annotation.v1")
        self.assertEqual(annotations["detector"]["version"], "neodojo.detector.opening_form_routine_review.v1")
        self.assertEqual(len(annotations["keyframes"]), 3)
        self.assertEqual(annotations["keyframes"][0]["name"], "opening stance")
        self.assertEqual(annotations["keyframes"][1]["name"], "settled support")
        self.assertEqual(annotations["keyframes"][2]["name"], "raise hands apex")
        self.assertTrue(annotations["keyframes"][2]["primary"])
        self.assertEqual(annotations["keyframes"][2]["frame"], 9)
        self.assertEqual(annotations["routine_review"]["summary"]["keyframe_count"], 3)
        self.assertEqual(annotations["routine_review"]["scoring_source"], "smplx")
        self.assertEqual(annotations["routine_review"]["term_results"][0]["source"], "smplx")
        self.assertIn("confidence", annotations["routine_review"]["term_results"][0])
        self.assertTrue(feedback_report_exists)
        self.assertEqual(feedback_report["schema"], "neodojo.routine_feedback_report.v1")
        self.assertEqual(manifest["key_frame"], 9)
        self.assertEqual(manifest["annotation_name"], "raise hands apex")
        self.assertTrue(manifest["feedback"]["passed"])
        self.assertEqual(manifest["routine_review"]["summary"]["keyframe_count"], 3)
        self.assertEqual(manifest["routine_review"]["source"], "smplx")

    def test_public_demo_exposes_routine_feedback_anchors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=12)
            model = write_fixture_g1_model_descriptor(root / "model")
            g1 = build_g1_visual_track(
                motion.out_dir,
                root / "g1",
                model_descriptor_path=model.descriptor_path,
            )
            annotation_result = write_detected_annotations(root / "annotations", motion.out_dir)
            playback = write_teaching_playback_demo(
                root / "teaching-demo",
                motion.out_dir,
                g1.track_manifest_path,
                annotations_path=annotation_result.manifest_path,
            )

            result = write_public_demo(
                playback_manifest_path=playback.manifest_path,
                recording_path=root / "public-demo" / "neodojo-demo.rrd",
            )
            smoke = smoke_check_public_demo(root / "public-demo")
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            scene = json.loads(result.scene_path.read_text(encoding="utf-8"))
            html = result.html_path.read_text(encoding="utf-8")
            screenshot = result.screenshot_path.read_text(encoding="utf-8")

        self.assertEqual(scene["routine_review"]["scoring_source"], "smplx")
        self.assertEqual(scene["feedback_anchor_labels"], ["opening stance", "settled support", "raise hands apex"])
        self.assertEqual(manifest["routine_feedback"]["anchor_count"], 3)
        self.assertEqual(manifest["routine_feedback"]["scoring_source"], "smplx")
        self.assertIn("Routine feedback", html)
        self.assertIn("opening stance", html)
        self.assertIn("settled support", screenshot)
        self.assertEqual(len(smoke.checked_paths), 4)

    def test_public_demo_export_writes_scene_recording_html_and_screenshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            model = write_fixture_g1_model_descriptor(root / "model")
            g1 = build_g1_visual_track(
                motion.out_dir,
                root / "g1",
                model_descriptor_path=model.descriptor_path,
            )
            render = write_g1_render(
                root / "render",
                model_descriptor_path=model.descriptor_path,
                g1_track=g1.track_manifest_path,
                allow_fixture_model=True,
            )
            playback = write_teaching_playback_demo(
                root / "teaching-demo",
                motion.out_dir,
                g1.track_manifest_path,
            )

            result = write_public_demo(
                playback_manifest_path=playback.manifest_path,
                g1_render_manifest_path=render.manifest_path,
                recording_path=root / "public-demo" / "neodojo-demo.rrd",
            )
            smoke = smoke_check_public_demo(root / "public-demo")
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            recording = json.loads(result.recording_path.read_text(encoding="utf-8"))
            scene = json.loads(result.scene_path.read_text(encoding="utf-8"))
            html = result.html_path.read_text(encoding="utf-8")
            screenshot = result.screenshot_path.read_text(encoding="utf-8")

        self.assertEqual(manifest["schema"], "neodojo.public_demo.v1")
        self.assertTrue(manifest["fixture_only"])
        self.assertEqual(manifest["recording"], "neodojo-demo.rrd")
        self.assertFalse(manifest["rerun"]["actual_rrd"])
        self.assertEqual(recording["schema"], "neodojo.rerun_recording_export.v1")
        self.assertFalse(recording["actual_rerun_rrd"])
        self.assertEqual(scene["schema"], "neodojo.scene_timeline.v1")
        self.assertIn("SMPL-X teacher", html)
        self.assertIn("Unitree G1 visual", html)
        self.assertIn("fixture-only", html)
        self.assertIn("SMPL-X teacher", screenshot)
        self.assertEqual(smoke.manifest_path.name, "manifest.json")
        self.assertEqual(len(smoke.checked_paths), 4)

    def test_public_demo_smoke_rejects_missing_label(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            model = write_fixture_g1_model_descriptor(root / "model")
            g1 = build_g1_visual_track(
                motion.out_dir,
                root / "g1",
                model_descriptor_path=model.descriptor_path,
            )
            playback = write_teaching_playback_demo(
                root / "teaching-demo",
                motion.out_dir,
                g1.track_manifest_path,
            )
            result = write_public_demo(
                playback_manifest_path=playback.manifest_path,
                recording_path=root / "public-demo" / "neodojo-demo.rrd",
            )
            html = result.html_path.read_text(encoding="utf-8").replace("Unitree G1 visual", "Unitree visual")
            result.html_path.write_text(html, encoding="utf-8")
            screenshot = result.screenshot_path.read_text(encoding="utf-8").replace("Unitree G1 visual", "Unitree visual")
            result.screenshot_path.write_text(screenshot, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing"):
                smoke_check_public_demo(root / "public-demo")

    def test_scene_timeline_preserves_scoring_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            model = write_fixture_g1_model_descriptor(root / "model")
            g1 = build_g1_visual_track(
                motion.out_dir,
                root / "g1",
                model_descriptor_path=model.descriptor_path,
            )
            playback = write_teaching_playback_demo(
                root / "teaching-demo",
                motion.out_dir,
                g1.track_manifest_path,
            )
            scene = build_scene_timeline(playback_manifest_path=playback.manifest_path)

        self.assertEqual(scene["scoring_source"], "smplx")
        self.assertTrue(scene["tracks"]["smplx"]["scoring_allowed"])
        self.assertFalse(scene["tracks"]["g1"]["scoring_allowed"])
        self.assertIn("coordinates", scene)

    def test_write_real_conversion_prep_from_source_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_index = root / "sources.csv"
            source_index.write_text(
                "\n".join(
                    [
                        "category_order,category_chinese,category_slug,item_order,article_title_chinese,title_english,selected_quality,available_qualities,source_size_bytes,source_size_mib,width,height,resolution,duration_seconds,duration_minutes,bit_rate_kbps,codec,article_url,source_mp4_url,recommended_output_path,probe_error",
                        "3,八段锦,03_baduanjin,6,5八段锦两手托天理三焦,Two Hands Hold Up the Heavens,SD,\"LD,SD\",45028780,42.94,1280,720,1280x720,220.843,3.68,1631.2,h264,https://example.invalid/article,https://example.invalid/source.mp4,video/03_baduanjin/006_two-hands-hold-up-the-heavens.mp4,",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = write_real_conversion_prep(
                root / "prep",
                source_index=source_index,
                source_id="03-006",
                start_seconds=1.5,
                end_seconds=9.0,
                rights_notes="local proof only",
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["status"], "gpu_gate_pending")
        self.assertEqual(manifest["source"]["id"], "03-006")
        self.assertEqual(manifest["source"]["title_english"], "Two Hands Hold Up the Heavens")
        self.assertEqual(manifest["trim"]["duration_seconds"], 7.5)
        self.assertFalse(manifest["source_media"]["validation"]["local_file_validated"])
        self.assertTrue(manifest["gpu_run"]["required"])
        self.assertIn("materialize-source", manifest["next_commands"]["materialize_source"])
        self.assertIn("--from-gvhmr-json", manifest["next_commands"]["import_motion_record"])

    def test_real_conversion_prep_records_local_video_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_index = root / "sources.csv"
            source_index.write_text(
                "\n".join(
                    [
                        "category_order,category_chinese,category_slug,item_order,article_title_chinese,title_english,selected_quality,available_qualities,source_size_bytes,source_size_mib,width,height,resolution,duration_seconds,duration_minutes,bit_rate_kbps,codec,article_url,source_mp4_url,recommended_output_path,probe_error",
                        "3,八段锦,03_baduanjin,6,5八段锦两手托天理三焦,Two Hands Hold Up the Heavens,SD,\"LD,SD\",45028780,42.94,1280,720,1280x720,220.843,3.68,1631.2,h264,https://example.invalid/article,https://example.invalid/source.mp4,video/03_baduanjin/006_two-hands-hold-up-the-heavens.mp4,",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            local_video = root / "source.mp4"
            local_video.write_bytes(b"fixture source video bytes")

            result = write_real_conversion_prep(
                root / "prep",
                source_index=source_index,
                source_id="03-006",
                local_video=local_video,
                start_seconds=1.5,
                end_seconds=9.0,
                rights_notes="local proof only",
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

        self.assertTrue(manifest["source_media"]["validation"]["local_file_validated"])
        self.assertEqual(manifest["source_media"]["local_file"]["suffix"], ".mp4")
        self.assertEqual(len(manifest["source_media"]["local_file"]["sha256"]), 64)
        self.assertIn("probe", manifest["source_media"])
        self.assertIn("media_probe_succeeded", manifest["source_media"]["validation"])
        self.assertTrue(manifest["source_media"]["reference_video_sync"]["available"])

    def test_ffprobe_payload_parser_extracts_video_metadata(self) -> None:
        parsed = _parse_ffprobe_payload(
            {
                "streams": [
                    {
                        "codec_type": "video",
                        "codec_name": "h264",
                        "width": 1280,
                        "height": 720,
                        "avg_frame_rate": "30000/1001",
                    }
                ],
                "format": {
                    "duration": "12.3456",
                    "size": "123456",
                    "bit_rate": "456789",
                    "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
                },
            }
        )

        self.assertEqual(parsed["format"]["duration_seconds"], 12.3456)
        self.assertEqual(parsed["format"]["size_bytes"], 123456)
        self.assertEqual(parsed["video_stream"]["codec"], "h264")
        self.assertEqual(parsed["video_stream"]["width"], 1280)
        self.assertEqual(parsed["video_stream"]["height"], 720)
        self.assertAlmostEqual(parsed["video_stream"]["avg_frame_rate"], 29.97003)

    def test_real_conversion_source_materialization_dry_run_writes_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_index = root / "sources.csv"
            source_index.write_text(
                "\n".join(
                    [
                        "category_order,category_chinese,category_slug,item_order,article_title_chinese,title_english,selected_quality,available_qualities,source_size_bytes,source_size_mib,width,height,resolution,duration_seconds,duration_minutes,bit_rate_kbps,codec,article_url,source_mp4_url,recommended_output_path,probe_error",
                        "3,八段锦,03_baduanjin,6,5八段锦两手托天理三焦,Two Hands Hold Up the Heavens,SD,\"LD,SD\",45028780,42.94,1280,720,1280x720,220.843,3.68,1631.2,h264,https://example.invalid/article,https://example.invalid/source.mp4,video/03_baduanjin/006_two-hands-hold-up-the-heavens.mp4,",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            local_video = root / "source.mp4"
            local_video.write_bytes(b"fixture source video bytes")
            prep = write_real_conversion_prep(
                root / "prep",
                source_index=source_index,
                source_id="03-006",
                local_video=local_video,
                start_seconds=1.5,
                end_seconds=9.0,
            )

            result = materialize_real_conversion_source(
                root / "source-materialized",
                prep_manifest=prep.manifest_path,
                frame_rate=2.0,
                dry_run=True,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["schema"], "neodojo.real_conversion_source_materialization.v1")
        self.assertEqual(manifest["status"], "dry_run")
        self.assertFalse(manifest["validation"]["gvhmr_input_ready"])
        self.assertEqual(manifest["source_prep"]["source_id"], "03-006")
        self.assertEqual(manifest["trim"]["duration_seconds"], 7.5)
        self.assertEqual(manifest["outputs"]["extracted_frame_count"], 0)
        self.assertEqual(manifest["ffmpeg"]["commands"][0]["kind"], "trim_clip")
        self.assertIn("trimmed-clip.mp4", manifest["gpu_handoff"]["trimmed_video_argument"])

    def test_real_conversion_prep_rejects_unknown_source_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_index = root / "sources.csv"
            source_index.write_text(
                "category_order,item_order,duration_seconds\n3,6,220.843\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "was not found"):
                write_real_conversion_prep(root / "prep", source_index=source_index, source_id="03-999")


if __name__ == "__main__":
    unittest.main()
