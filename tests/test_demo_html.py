from __future__ import annotations

import json
import importlib.util
import socket
import tempfile
import unittest
from pathlib import Path

from neodojo.annotations import detect_opening_form_keyframe, write_detected_annotations
from neodojo.capture_bundle import write_capture_bundle
from neodojo.contracts import sha256_file
from neodojo.demo_html import build_fixture, compute_feedback, render_demo_html, write_demo
from neodojo.fixtures import TEACHING_JOINTS, build_smplx_fixture_frames, derive_g1_like_frame
from neodojo.g1_render import G1_MUJOCO_RENDER_BACKEND, G1_RENDER_SCHEMA, write_g1_mujoco_render, write_g1_render
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
from neodojo.quality import check_quality_surface
from neodojo.recorder_capture import write_simulator_recorder_capture
from neodojo.real_conversion import (
    _parse_ffprobe_payload,
    materialize_real_conversion_source,
    validate_gvhmr_source,
    write_real_conversion_prep,
)
from neodojo.smplx_surface import (
    load_smplx_asset_descriptor,
    load_smplx_surface_layer,
    load_smplx_surface_proxy,
    register_smplx_asset_descriptor,
    validate_smplx_mesh_generation_inputs,
    write_smplx_mesh_surface,
    write_smplx_surface_proxy,
)
from neodojo.teaching_playback import write_teaching_playback_demo
from neodojo.viser_runtime import serve_viser_runtime, write_viser_runtime_contract


def _free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


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

    def test_write_mujoco_render_rejects_fixture_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            model = write_fixture_g1_model_descriptor(root / "model")
            g1 = build_g1_visual_track(
                motion.out_dir,
                root / "g1",
                model_descriptor_path=model.descriptor_path,
            )

            with self.assertRaisesRegex(ValueError, "registered URDF/MJCF"):
                write_g1_mujoco_render(
                    root / "mujoco-render",
                    model_descriptor_path=model.descriptor_path,
                    g1_track=g1.track_manifest_path,
                    allow_fixture_model=True,
                )

    @unittest.skipUnless(importlib.util.find_spec("mujoco"), "mujoco optional dependency is not installed")
    def test_write_mujoco_render_from_registered_mjcf(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            model_file = root / "g1_fixture.xml"
            model_file.write_text(
                """<mujoco model="unitree_g1_fixture">
  <compiler angle="radian"/>
  <worldbody>
    <light pos="0 -3 3"/>
    <body name="pelvis" pos="0 0 0.8">
      <geom name="body" type="capsule" size="0.08 0.28" fromto="0 0 0 0 0 0.56"/>
      <joint name="waist_yaw_joint" type="hinge" axis="0 0 1"/>
      <body name="torso" pos="0 0 0.56">
        <geom name="head" type="sphere" size="0.1" pos="0 0 0.18"/>
      </body>
    </body>
  </worldbody>
</mujoco>
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

            result = write_g1_mujoco_render(
                root / "mujoco-render",
                model_descriptor_path=model.descriptor_path,
                g1_track=g1.track_manifest_path,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            front_png = result.frame_paths["front"].read_bytes()

        self.assertEqual(manifest["renderer"]["backend"], "mujoco_python_offscreen.v1")
        self.assertTrue(manifest["mesh_loaded"])
        self.assertTrue(manifest["nonblank_pixel_check"])
        self.assertEqual(set(result.frame_paths), {"front", "side", "top"})
        self.assertTrue(front_png.startswith(b"\x89PNG"))

    @unittest.skipUnless(importlib.util.find_spec("mujoco"), "mujoco optional dependency is not installed")
    def test_write_mujoco_render_applies_imported_gmr_joint_angles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            model_file = root / "g1_fixture.xml"
            model_file.write_text(
                """<mujoco model="unitree_g1_fixture">
  <compiler angle="radian"/>
  <worldbody>
    <light pos="0 -3 3"/>
    <body name="pelvis" pos="0 0 0.8">
      <geom name="body" type="capsule" size="0.08 0.28" fromto="0 0 0 0 0 0.56"/>
      <joint name="waist_yaw_joint" type="hinge" axis="0 0 1" range="-1 1"/>
      <body name="torso" pos="0 0 0.56">
        <geom name="head" type="sphere" size="0.1" pos="0 0 0.18"/>
      </body>
    </body>
  </worldbody>
</mujoco>
""",
                encoding="utf-8",
            )
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            _, smplx_frames = load_motion_record_frames(motion.motion_record_manifest_path)
            model = register_g1_model(root / "model", model_file)
            source = root / "gmr-unitree-g1.json"
            source.write_text(
                json.dumps(
                    {
                        "schema": "neodojo.gmr_unitree_g1_track.v1",
                        "robot": "unitree_g1",
                        "fps": 30,
                        "frames": [
                            {
                                "visual_joints": derive_g1_like_frame(frame),
                                "joint_angles": {
                                    "waist_yaw_joint": index * 0.05,
                                    "right_hip_pitch_joint": -index * 0.01,
                                },
                            }
                            for index, frame in enumerate(smplx_frames)
                        ],
                    }
                ),
                encoding="utf-8",
            )
            g1 = import_gmr_json_track(
                root / "g1",
                source,
                motion_record=motion.out_dir,
                model_descriptor_path=model.descriptor_path,
            )

            result = write_g1_mujoco_render(
                root / "mujoco-render",
                model_descriptor_path=model.descriptor_path,
                g1_track=g1.track_manifest_path,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

        pose_application = manifest["pose_application"]
        self.assertEqual(manifest["pose_stream"], "imported_gmr_unitree_g1")
        self.assertEqual(pose_application["source"], "imported_gmr_joint_angles")
        self.assertEqual(pose_application["joint_angle_count"], 2)
        self.assertEqual(pose_application["applied_joint_count"], 1)
        self.assertEqual(pose_application["applied_joint_values"]["waist_yaw_joint"], 0.25)
        self.assertEqual(pose_application["missing_joints"], ["right_hip_pitch_joint"])

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

    def test_smplx_surface_proxy_integrates_with_playback_and_public_demo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            surface = write_smplx_surface_proxy(root / "surface", motion.out_dir)
            model = write_fixture_g1_model_descriptor(root / "model")
            g1 = build_g1_visual_track(
                motion.out_dir,
                root / "g1",
                model_descriptor_path=model.descriptor_path,
            )

            surface_manifest, surface_frames = load_smplx_surface_proxy(surface.manifest_path)
            playback = write_teaching_playback_demo(
                root / "teaching-demo",
                motion.out_dir,
                g1.track_manifest_path,
                smplx_surface=surface.manifest_path,
            )
            public = write_public_demo(
                playback_manifest_path=playback.manifest_path,
                recording_path=root / "public-demo" / "neodojo-demo.rrd",
            )
            smoke = smoke_check_public_demo(root / "public-demo")
            playback_manifest = json.loads(playback.manifest_path.read_text(encoding="utf-8"))
            playback_html = playback.html_path.read_text(encoding="utf-8")
            public_manifest = json.loads(public.manifest_path.read_text(encoding="utf-8"))
            scene = json.loads(public.scene_path.read_text(encoding="utf-8"))
            screenshot = public.screenshot_path.read_text(encoding="utf-8")

        self.assertEqual(surface_manifest["schema"], "neodojo.smplx_surface_proxy.v1")
        self.assertFalse(surface_manifest["licensed_smplx_mesh"])
        self.assertFalse(surface_manifest["scoring_allowed"])
        self.assertEqual(len(surface_frames), 10)
        self.assertEqual(playback_manifest["surface_layers"]["smplx_proxy"]["surface_kind"], "joint_capsule_proxy")
        self.assertEqual(playback_manifest["evidence"]["rendered_surface_layers"], ["smplx_proxy"])
        self.assertIn("SMPL-X surface proxy", playback_html)
        self.assertEqual(scene["surface_proxy"]["surface_kind"], "joint_capsule_proxy")
        self.assertFalse(public_manifest["surface_layers"]["smplx_proxy"]["licensed_smplx_mesh"])
        self.assertIn("SMPL-X surface proxy", screenshot)
        self.assertEqual(len(smoke.checked_paths), 4)

    def test_teaching_playback_rejects_surface_frame_count_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            shorter_motion = write_fixture_motion_contract(root / "shorter-motion", frame_count=9)
            surface = write_smplx_surface_proxy(root / "surface", shorter_motion.out_dir)
            model = write_fixture_g1_model_descriptor(root / "model")
            g1 = build_g1_visual_track(
                motion.out_dir,
                root / "g1",
                model_descriptor_path=model.descriptor_path,
            )

            with self.assertRaisesRegex(ValueError, "surface frame count"):
                write_teaching_playback_demo(
                    root / "teaching-demo",
                    motion.out_dir,
                    g1.track_manifest_path,
                    smplx_surface=surface.manifest_path,
                )

    def test_register_smplx_asset_descriptor_is_local_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            asset = root / "SMPLX_NEUTRAL.npz"
            asset.write_bytes(b"licensed fixture asset placeholder")

            result = register_smplx_asset_descriptor(
                root / "assets-out",
                model_path=asset,
                license_name="local licensed fixture",
                source_url="https://example.invalid/smplx",
                source_revision="fixture",
                variant="neutral fixture",
            )
            descriptor = load_smplx_asset_descriptor(result.descriptor_path)

        self.assertEqual(descriptor["schema"], "neodojo.smplx_asset_descriptor.v1")
        self.assertTrue(descriptor["local_only"])
        self.assertTrue(descriptor["licensed_smplx_mesh"])
        self.assertEqual(descriptor["license"], "local licensed fixture")
        self.assertEqual(descriptor["variant"], "neutral fixture")
        self.assertEqual(len(descriptor["sha256"]), 64)

    def test_smplx_asset_descriptor_rejects_missing_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaisesRegex(ValueError, "licensed SMPL-X model asset does not exist"):
                register_smplx_asset_descriptor(
                    root / "assets-out",
                    model_path=root / "missing-SMPLX_NEUTRAL.npz",
                    license_name="local licensed fixture",
                )

    def test_smplx_mesh_gate_rejects_joint_only_motion_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            asset = root / "SMPLX_NEUTRAL.npz"
            asset.write_bytes(b"licensed fixture asset placeholder")
            descriptor = register_smplx_asset_descriptor(
                root / "assets-out",
                model_path=asset,
                license_name="local licensed fixture",
            )
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)

            with self.assertRaisesRegex(ValueError, "only exposes teaching joints"):
                validate_smplx_mesh_generation_inputs(
                    motion_record=motion.out_dir,
                    asset_descriptor=descriptor.descriptor_path,
                )

    def test_gvhmr_json_motion_contract_preserves_smplx_parameters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            frame_count = 10
            source = root / "gvhmr-smplx-joints.json"
            source.write_text(
                json.dumps(
                    {
                        "schema": "neodojo.gvhmr_smplx_joints.v1",
                        "routine": "Baduanjin",
                        "form": "Two Hands Hold Up the Heavens",
                        "fps": 30,
                        "frames": build_smplx_fixture_frames(frame_count),
                        "smplx_parameters": {
                            "parameterization": "smplx_axis_angle",
                            "global_orient": [[0.0, 0.0, 0.0] for _ in range(frame_count)],
                            "body_pose": [[0.0] * 63 for _ in range(frame_count)],
                            "transl": [[0.0, 0.0, 0.0] for _ in range(frame_count)],
                            "betas": [0.0] * 10,
                        },
                    }
                ),
                encoding="utf-8",
            )
            motion = write_gvhmr_json_motion_contract(root / "motion", source)
            asset = root / "SMPLX_NEUTRAL.npz"
            asset.write_bytes(b"licensed fixture asset placeholder")
            descriptor = register_smplx_asset_descriptor(
                root / "assets-out",
                model_path=asset,
                license_name="local licensed fixture",
            )
            manifest = json.loads(motion.motion_record_manifest_path.read_text(encoding="utf-8"))
            parameter_data = json.loads(motion.smplx_parameters_data_path.read_text(encoding="utf-8"))

            validation = validate_smplx_mesh_generation_inputs(
                motion_record=motion.out_dir,
                asset_descriptor=descriptor.descriptor_path,
            )

        self.assertEqual(manifest["smplx_parameters"]["schema"], "neodojo.smplx_parameters.v1")
        self.assertTrue(manifest["smplx_parameters"]["mesh_ready"])
        self.assertEqual(manifest["smplx_parameters"]["missing_required_fields"], [])
        self.assertEqual(manifest["data_files"]["smplx_parameters"], "smplx-parameters.json")
        self.assertEqual(parameter_data["schema"], "neodojo.smplx_parameters.v1")
        self.assertEqual(parameter_data["frame_count"], frame_count)
        self.assertEqual(parameter_data["parameterization"], "smplx_axis_angle")
        self.assertIn("global_orient", parameter_data["fields"])
        self.assertIn("body_pose", parameter_data["fields"])
        self.assertIn("betas", parameter_data["fields"])
        self.assertTrue(validation["valid"])
        self.assertEqual(validation["renderer_boundary"]["backend"], "external_licensed_smplx_mesh_frames.v1")
        self.assertEqual(validation["motion_record"]["frame_count"], frame_count)

    def test_smplx_mesh_surface_import_integrates_with_playback_and_public_demo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            frame_count = 10
            source = root / "gvhmr-smplx-joints.json"
            source.write_text(
                json.dumps(
                    {
                        "schema": "neodojo.gvhmr_smplx_joints.v1",
                        "routine": "Baduanjin",
                        "form": "Two Hands Hold Up the Heavens",
                        "fps": 30,
                        "frames": build_smplx_fixture_frames(frame_count),
                        "smplx_parameters": {
                            "parameterization": "smplx_axis_angle",
                            "global_orient": [[0.0, 0.0, 0.0] for _ in range(frame_count)],
                            "body_pose": [[0.0] * 63 for _ in range(frame_count)],
                            "transl": [[0.0, 0.0, 0.0] for _ in range(frame_count)],
                            "betas": [0.0] * 10,
                        },
                    }
                ),
                encoding="utf-8",
            )
            motion = write_gvhmr_json_motion_contract(root / "motion", source)
            asset = root / "SMPLX_NEUTRAL.npz"
            asset.write_bytes(b"licensed fixture asset placeholder")
            descriptor = register_smplx_asset_descriptor(
                root / "assets-out",
                model_path=asset,
                license_name="local licensed fixture",
            )
            mesh_frames = root / "smplx-mesh-frames.json"
            mesh_frames.write_text(
                json.dumps(
                    {
                        "schema": "neodojo.smplx_mesh_frames.v1",
                        "frame_count": frame_count,
                        "faces": [[0, 1, 2], [0, 2, 3]],
                        "frames": [
                            {
                                "vertices": [
                                    [-0.15, 1.0 + frame * 0.01, 0.0],
                                    [0.15, 1.0 + frame * 0.01, 0.0],
                                    [0.15, 1.35 + frame * 0.01, 0.02],
                                    [-0.15, 1.35 + frame * 0.01, 0.02],
                                ]
                            }
                            for frame in range(frame_count)
                        ],
                        "provenance": {
                            "renderer": "fixture-safe external licensed SMPL-X renderer stand-in",
                        },
                    }
                ),
                encoding="utf-8",
            )
            mesh = write_smplx_mesh_surface(
                root / "smplx-mesh",
                motion_record=motion.out_dir,
                asset_descriptor=descriptor.descriptor_path,
                mesh_frames=mesh_frames,
            )
            model = write_fixture_g1_model_descriptor(root / "model")
            g1 = build_g1_visual_track(
                motion.out_dir,
                root / "g1",
                model_descriptor_path=model.descriptor_path,
            )
            surface_manifest, surface_data = load_smplx_surface_layer(mesh.manifest_path)
            validation = json.loads(mesh.validation_path.read_text(encoding="utf-8"))
            playback = write_teaching_playback_demo(
                root / "teaching-demo",
                motion.out_dir,
                g1.track_manifest_path,
                smplx_surface=mesh.manifest_path,
            )
            public = write_public_demo(
                playback_manifest_path=playback.manifest_path,
                recording_path=root / "public-demo" / "neodojo-demo.rrd",
            )
            smoke = smoke_check_public_demo(root / "public-demo")
            playback_manifest = json.loads(playback.manifest_path.read_text(encoding="utf-8"))
            playback_html = playback.html_path.read_text(encoding="utf-8")
            public_manifest = json.loads(public.manifest_path.read_text(encoding="utf-8"))
            scene = json.loads(public.scene_path.read_text(encoding="utf-8"))
            screenshot = public.screenshot_path.read_text(encoding="utf-8")

        self.assertEqual(surface_manifest["schema"], "neodojo.smplx_mesh_surface.v1")
        self.assertEqual(surface_manifest["surface_kind"], "licensed_smplx_mesh_external_frames")
        self.assertTrue(surface_manifest["licensed_smplx_mesh"])
        self.assertFalse(surface_manifest["scoring_allowed"])
        self.assertEqual(surface_data["vertex_count"], 4)
        self.assertEqual(surface_data["face_count"], 2)
        self.assertEqual(validation["mesh_frames"]["vertex_count"], 4)
        self.assertEqual(playback_manifest["surface_layers"]["smplx_mesh"]["surface_kind"], "licensed_smplx_mesh_external_frames")
        self.assertEqual(playback_manifest["evidence"]["rendered_surface_layers"], ["smplx_mesh"])
        self.assertIn("SMPL-X licensed mesh surface", playback_html)
        self.assertEqual(scene["surface_proxy"]["label"], "SMPL-X licensed mesh surface")
        self.assertTrue(scene["surface_proxy"]["licensed_smplx_mesh"])
        self.assertTrue(public_manifest["surface_layers"]["smplx_mesh"]["licensed_smplx_mesh"])
        self.assertFalse(public_manifest["surface_layers"]["smplx_mesh"]["scoring_allowed"])
        self.assertIn("SMPL-X licensed mesh surface", screenshot)
        self.assertEqual(len(smoke.checked_paths), 4)

    def test_gvhmr_json_motion_contract_rejects_bad_smplx_parameter_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "bad-gvhmr-smplx-joints.json"
            source.write_text(
                json.dumps(
                    {
                        "schema": "neodojo.gvhmr_smplx_joints.v1",
                        "frames": build_smplx_fixture_frames(10),
                        "smplx_parameters": {
                            "global_orient": [[0.0, 0.0, 0.0] for _ in range(9)],
                            "body_pose": [[0.0] * 63 for _ in range(10)],
                            "betas": [0.0] * 10,
                        },
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "global_orient frame count"):
                write_gvhmr_json_motion_contract(root / "motion", source)

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
                annotations_path=write_detected_annotations(root / "annotations", motion.out_dir).manifest_path,
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

    @unittest.skipUnless(importlib.util.find_spec("rerun"), "rerun optional dependency is not installed")
    def test_public_demo_can_write_true_rerun_recording(self) -> None:
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
                annotations_path=write_detected_annotations(root / "annotations", motion.out_dir).manifest_path,
            )

            result = write_public_demo(
                playback_manifest_path=playback.manifest_path,
                recording_path=root / "public-demo" / "neodojo-demo.rrd",
                use_rerun_sdk=True,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            recording_bytes = result.recording_path.read_bytes()

        self.assertTrue(manifest["rerun"]["actual_rrd"])
        self.assertIsNotNone(manifest["rerun"]["sdk_version"])
        self.assertGreater(len(recording_bytes), 128)
        self.assertFalse(recording_bytes.startswith(b"{"))

    def test_viser_runtime_contract_reuses_scene_timeline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            model = write_fixture_g1_model_descriptor(root / "model")
            g1 = build_g1_visual_track(
                motion.out_dir,
                root / "g1",
                model_descriptor_path=model.descriptor_path,
            )
            annotations = write_detected_annotations(root / "annotations", motion.out_dir)
            playback = write_teaching_playback_demo(
                root / "teaching-demo",
                motion.out_dir,
                g1.track_manifest_path,
                annotations_path=annotations.manifest_path,
            )

            result = write_viser_runtime_contract(
                root / "viser-runtime",
                playback_manifest_path=playback.manifest_path,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            scene = json.loads(result.scene_path.read_text(encoding="utf-8"))
            front_screenshot = result.screenshot_paths["front"].read_text(encoding="utf-8")

        self.assertEqual(manifest["schema"], "neodojo.viser_runtime.v1")
        self.assertEqual(manifest["runtime"]["target"], "viser")
        self.assertEqual(manifest["scene"], "scene.json")
        self.assertEqual(manifest["scoring_source"], "smplx")
        self.assertFalse(manifest["g1_scoring_allowed"])
        self.assertEqual(manifest["coordinate_transform"]["viser_world_up_axis"], "z")
        self.assertIn("front", manifest["camera_presets"])
        self.assertEqual(manifest["controls"][0]["kind"], "slider")
        self.assertEqual(scene["schema"], "neodojo.scene_timeline.v1")
        self.assertIn("SMPL-X teacher", manifest["overlays"]["public_labels"])
        self.assertEqual(set(manifest["visual_smoke"]["screenshot_paths"]), {"front", "side", "top"})
        self.assertEqual(set(result.screenshot_paths), {"front", "side", "top"})
        control_kinds = {control["kind"] for control in manifest["controls"]}
        self.assertIn("camera_preset_button", control_kinds)
        self.assertIn("annotation_keyframe_button", control_kinds)
        self.assertIn("visibility_toggle", control_kinds)
        self.assertIn("button", control_kinds)
        self.assertEqual(manifest["teaching_ui"]["profile"], "neodojo.viser_teaching_ui.v1")
        self.assertEqual(manifest["teaching_ui"]["scoring_policy"]["scoring_source"], "smplx")
        self.assertFalse(manifest["teaching_ui"]["scoring_policy"]["g1_scoring_allowed"])
        self.assertEqual(
            {group["id"] for group in manifest["teaching_ui"]["control_groups"]},
            {"timeline", "camera", "layers", "feedback"},
        )
        self.assertIn("playback_speed", manifest["teaching_ui"]["control_groups"][0]["controls"])
        self.assertIn(1.0, manifest["teaching_ui"]["timeline"]["speed_options"])
        self.assertEqual(len(manifest["teaching_ui"]["feedback_drilldown"]), 3)
        self.assertTrue(manifest["teaching_ui"]["live_client_smoke"]["optional"])
        self.assertFalse(manifest["teaching_ui"]["live_client_smoke"]["default_ci_required"])
        self.assertIn("Viser front preview", front_screenshot)
        self.assertIn("G1 scoring allowed: false", front_screenshot)

    def test_capture_bundle_collects_multi_camera_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=10)
            surface = write_smplx_surface_proxy(root / "surface", motion.out_dir)
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
            annotations = write_detected_annotations(root / "annotations", motion.out_dir)
            playback = write_teaching_playback_demo(
                root / "teaching-demo",
                motion.out_dir,
                g1.track_manifest_path,
                annotations_path=annotations.manifest_path,
                smplx_surface=surface.manifest_path,
            )
            public = write_public_demo(
                playback_manifest_path=playback.manifest_path,
                g1_render_manifest_path=render.manifest_path,
                recording_path=root / "public-demo" / "neodojo-demo.rrd",
            )
            viser = write_viser_runtime_contract(
                root / "viser-runtime",
                playback_manifest_path=playback.manifest_path,
                g1_render_manifest_path=render.manifest_path,
            )

            result = write_capture_bundle(
                root / "capture",
                public_demo=public.manifest_path,
                viser_runtime=viser.manifest_path,
                g1_render=render.manifest_path,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["schema"], "neodojo.capture_bundle.v1")
        self.assertEqual(manifest["style"], "roboharness_multi_camera_evidence_manifest")
        self.assertTrue(manifest["fixture_only"])
        self.assertEqual(manifest["scoring_source"], "smplx")
        self.assertFalse(manifest["g1_scoring_allowed"])
        self.assertFalse(manifest["source"]["real_offscreen_recorder"])
        self.assertEqual(set(manifest["views"]), {"front", "side", "top"})
        self.assertIn("viser_preview", manifest["views"]["front"]["artifacts"])
        self.assertIn("g1_render_frame", manifest["views"]["front"]["artifacts"])
        self.assertGreaterEqual(manifest["verification"]["nonblank_artifact_count"], 10)
        self.assertEqual(set(manifest["verification"]["required_views"]), {"front", "side", "top"})

    def test_capture_bundle_can_include_browser_capture(self) -> None:
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
            public = write_public_demo(
                playback_manifest_path=playback.manifest_path,
                g1_render_manifest_path=render.manifest_path,
                recording_path=root / "public-demo" / "neodojo-demo.rrd",
            )
            viser = write_viser_runtime_contract(
                root / "viser-runtime",
                playback_manifest_path=playback.manifest_path,
                g1_render_manifest_path=render.manifest_path,
            )
            browser_dir = root / "browser-capture"
            browser_dir.mkdir()
            browser_screenshot = browser_dir / "public-demo-browser.png"
            browser_screenshot.write_bytes(b"browser screenshot bytes")
            (browser_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "schema": "neodojo.browser_capture.v1",
                        "capture_kind": "playwright_chromium_public_demo_screenshot",
                        "real_browser_capture": True,
                        "fixture_only": True,
                        "public_demo": "../public-demo/manifest.json",
                        "screenshot": "public-demo-browser.png",
                        "viewport": {"width": 1280, "height": 720},
                        "scoring_source": "smplx",
                        "g1_scoring_allowed": False,
                    }
                ),
                encoding="utf-8",
            )

            result = write_capture_bundle(
                root / "capture",
                public_demo=public.manifest_path,
                viser_runtime=viser.manifest_path,
                g1_render=render.manifest_path,
                browser_capture=browser_dir,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

        self.assertTrue(manifest["source"]["real_browser_capture"])
        self.assertFalse(manifest["source"]["real_offscreen_recorder"])
        self.assertFalse(manifest["source"]["real_roboharness_integration"])
        self.assertEqual(
            manifest["artifact_groups"]["browser_capture"]["screenshot"],
            "../browser-capture/public-demo-browser.png",
        )
        self.assertTrue(manifest["verification"]["browser_capture_smoke_checked"])

    def test_simulator_recorder_capture_wraps_mujoco_render(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            render_dir = root / "mujoco-render"
            frame_dir = render_dir / "frames"
            frame_dir.mkdir(parents=True)
            for view in ("front", "side", "top"):
                (frame_dir / f"{view}.png").write_bytes(f"{view} png bytes".encode("utf-8"))
            (render_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "schema": G1_RENDER_SCHEMA,
                        "fixture_only": False,
                        "renderer": {
                            "backend": G1_MUJOCO_RENDER_BACKEND,
                            "resolution": {"width": 640, "height": 480},
                        },
                        "frame_count": 10,
                        "selected_frame": 5,
                        "timing": {"fps": 30},
                        "camera_definitions": {
                            "front": {"azimuth": 0},
                            "side": {"azimuth": 90},
                            "top": {"elevation": -90},
                        },
                        "frame_paths": {
                            "front": "frames/front.png",
                            "side": "frames/side.png",
                            "top": "frames/top.png",
                        },
                        "scoring_source": "smplx",
                        "g1_scoring_allowed": False,
                        "nonblank_pixel_check": True,
                        "nonblank_views": {"front": True, "side": True, "top": True},
                    }
                ),
                encoding="utf-8",
            )

            result = write_simulator_recorder_capture(root / "recorder-capture", simulator_render=render_dir)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["schema"], "neodojo.recorder_capture.v1")
        self.assertEqual(manifest["backend"]["kind"], "mujoco_offscreen_frame_recorder.v1")
        self.assertTrue(manifest["real_offscreen_recorder"])
        self.assertTrue(manifest["real_simulator_recorder"])
        self.assertFalse(manifest["real_roboharness_integration"])
        self.assertEqual(set(manifest["camera_captures"]), {"front", "side", "top"})
        self.assertEqual(len(result.checked_paths), 3)

    def test_capture_bundle_can_include_simulator_recorder_capture(self) -> None:
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
            public = write_public_demo(
                playback_manifest_path=playback.manifest_path,
                g1_render_manifest_path=render.manifest_path,
                recording_path=root / "public-demo" / "neodojo-demo.rrd",
            )
            viser = write_viser_runtime_contract(
                root / "viser-runtime",
                playback_manifest_path=playback.manifest_path,
                g1_render_manifest_path=render.manifest_path,
            )
            recorder_dir = root / "recorder-capture"
            recorder_frames = root / "mujoco-render" / "frames"
            recorder_frames.mkdir(parents=True)
            for view in ("front", "side", "top"):
                (recorder_frames / f"{view}.png").write_bytes(f"{view} recorder png".encode("utf-8"))
            (recorder_dir).mkdir()
            (recorder_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "schema": "neodojo.recorder_capture.v1",
                        "capture_kind": "simulator_offscreen_camera_capture",
                        "backend": {"kind": "mujoco_offscreen_frame_recorder.v1"},
                        "camera_captures": {
                            view: {
                                "camera_role": f"{view}_simulator_offscreen_recorder",
                                "artifact": f"../mujoco-render/frames/{view}.png",
                                "nonblank": True,
                            }
                            for view in ("front", "side", "top")
                        },
                        "real_offscreen_recorder": True,
                        "real_simulator_recorder": True,
                        "real_roboharness_integration": False,
                        "scoring_source": "smplx",
                        "g1_scoring_allowed": False,
                    }
                ),
                encoding="utf-8",
            )

            result = write_capture_bundle(
                root / "capture",
                public_demo=public.manifest_path,
                viser_runtime=viser.manifest_path,
                g1_render=render.manifest_path,
                recorder_capture=recorder_dir,
            )
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

        self.assertTrue(manifest["source"]["real_offscreen_recorder"])
        self.assertTrue(manifest["source"]["real_simulator_recorder"])
        self.assertIn("recorder_capture", manifest["artifact_groups"])
        self.assertIn("recorder_capture", manifest["views"]["front"]["artifacts"])
        self.assertTrue(manifest["verification"]["recorder_capture_smoke_checked"])

    def test_capture_bundle_rejects_missing_viser_preview(self) -> None:
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
            public = write_public_demo(
                playback_manifest_path=playback.manifest_path,
                g1_render_manifest_path=render.manifest_path,
                recording_path=root / "public-demo" / "neodojo-demo.rrd",
            )
            viser = write_viser_runtime_contract(
                root / "viser-runtime",
                playback_manifest_path=playback.manifest_path,
                g1_render_manifest_path=render.manifest_path,
            )
            viser.screenshot_paths["top"].unlink()

            with self.assertRaisesRegex(ValueError, "viser top preview artifact is missing"):
                write_capture_bundle(
                    root / "capture",
                    public_demo=public.manifest_path,
                    viser_runtime=viser.manifest_path,
                    g1_render=render.manifest_path,
                )

    @unittest.skipUnless(importlib.util.find_spec("viser"), "viser optional dependency is not installed")
    def test_viser_runtime_can_start_and_stop_with_optional_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            motion = write_fixture_motion_contract(root / "motion", frame_count=8)
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

            result = serve_viser_runtime(
                playback_manifest_path=playback.manifest_path,
                out_dir=root / "viser-runtime",
                host="127.0.0.1",
                port=_free_local_port(),
                stop_after_start=True,
                verbose=False,
            )

        self.assertEqual(result.manifest_path.name, "viser-runtime.json")
        self.assertEqual(result.scene_path.name, "scene.json")
        self.assertEqual(set(result.screenshot_paths), {"front", "side", "top"})
        self.assertTrue(result.url.startswith("http://127.0.0.1:"))

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

    def test_quality_check_validates_current_plan_surface(self) -> None:
        result = check_quality_surface(Path.cwd())

        self.assertGreaterEqual(result.checked_plan_count, 1)
        self.assertIn("mvp-quality-release-surface.md", result.checked_links)

    def test_quality_check_rejects_missing_plan_link(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plans = root / "docs" / "plans"
            plans.mkdir(parents=True)
            plan_text = "\n".join(
                [
                    "# Present Plan",
                    "",
                    "Status: PLANNED",
                    "",
                    "## Goal",
                    "Do a thing.",
                    "",
                    "## Execution Tasks",
                    "- [ ] Task.",
                    "",
                    "## Acceptance Evidence",
                    "- Evidence.",
                    "",
                    "## Non-Goals",
                    "- Non-goal.",
                    "",
                    "## Stop Condition",
                    "Stop.",
                ]
            )
            (plans / "mvp-implementation-phases.md").write_text(
                "# MVP Implementation Plan Index\n\n"
                "Status: SPLIT INTO EXECUTABLE PLAN FILES\n\n"
                "[mvp-present.md](mvp-present.md)\n",
                encoding="utf-8",
            )
            (plans / "mvp-present.md").write_text(plan_text + "\n", encoding="utf-8")
            (plans / "mvp-unlinked.md").write_text(plan_text + "\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing plan links"):
                check_quality_surface(root)

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

    def test_gvhmr_source_validation_writes_validated_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            materialization = root / "source-materialization.json"
            materialization.write_text(
                json.dumps(
                    {
                        "schema": "neodojo.real_conversion_source_materialization.v1",
                        "source_prep": {"source_id": "03-006"},
                        "trim": {
                            "start_seconds": 0.25,
                            "end_seconds": 1.75,
                            "duration_seconds": 1.5,
                        },
                        "outputs": {
                            "trimmed_video_path": "outputs/real-conversion-source/source/trimmed-clip.mp4",
                            "trimmed_video": {"sha256": "abc123"},
                        },
                        "gpu_handoff": {
                            "trimmed_video_argument": "outputs/real-conversion-source/source/trimmed-clip.mp4",
                        },
                    }
                ),
                encoding="utf-8",
            )
            gvhmr = root / "gvhmr-smplx-joints.json"
            gvhmr.write_text(
                json.dumps(
                    {
                        "schema": "neodojo.gvhmr_smplx_joints.v1",
                        "routine": "Baduanjin",
                        "form": "Two Hands Hold Up the Heavens",
                        "fps": 24,
                        "frames": build_smplx_fixture_frames(36),
                        "provenance": {
                            "source_materialization_manifest": str(materialization),
                            "source_materialization_sha256": sha256_file(materialization),
                            "source_id": "03-006",
                            "trim": {
                                "start_seconds": 0.25,
                                "end_seconds": 1.75,
                                "duration_seconds": 1.5,
                            },
                            "input_video": "outputs/real-conversion-source/source/trimmed-clip.mp4",
                            "input_video_sha256": "abc123",
                            "gpu_command": "python tools/demo/demo.py --video trimmed-clip.mp4",
                            "runtime": "test gpu",
                            "upstream_version": "gvhmr-test",
                        },
                    }
                ),
                encoding="utf-8",
            )

            validation = validate_gvhmr_source(
                root / "validation",
                source_materialization=materialization,
                gvhmr_json=gvhmr,
            )
            report = json.loads(validation.report_path.read_text(encoding="utf-8"))
            validated_export = json.loads(validation.validated_export_path.read_text(encoding="utf-8"))
            motion = write_gvhmr_json_motion_contract(root / "motion", validation.validated_export_path)
            motion_manifest = json.loads(motion.motion_record_manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(validation.status, "validated")
        self.assertTrue(report["passed"])
        self.assertEqual(report["schema"], "neodojo.gvhmr_source_validation.v1")
        self.assertEqual(validated_export["source_validation"]["status"], "validated")
        self.assertEqual(
            motion_manifest["provenance"]["source_validation"]["schema"],
            "neodojo.gvhmr_source_validation.v1",
        )

    def test_gvhmr_source_validation_reports_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            materialization = root / "source-materialization.json"
            materialization.write_text(
                json.dumps(
                    {
                        "schema": "neodojo.real_conversion_source_materialization.v1",
                        "source_prep": {"source_id": "03-006"},
                        "trim": {"start_seconds": 0.0, "end_seconds": 1.0, "duration_seconds": 1.0},
                        "outputs": {"trimmed_video_path": "trimmed.mp4", "trimmed_video": None},
                        "gpu_handoff": {"trimmed_video_argument": "trimmed.mp4"},
                    }
                ),
                encoding="utf-8",
            )
            gvhmr = root / "gvhmr-smplx-joints.json"
            gvhmr.write_text(
                json.dumps(
                    {
                        "schema": "neodojo.gvhmr_smplx_joints.v1",
                        "routine": "Baduanjin",
                        "form": "Two Hands Hold Up the Heavens",
                        "fps": 24,
                        "frames": build_smplx_fixture_frames(24),
                        "provenance": {
                            "source_materialization_manifest": str(materialization),
                            "source_materialization_sha256": sha256_file(materialization),
                            "source_id": "03-999",
                            "trim": {"start_seconds": 0.0, "end_seconds": 1.0, "duration_seconds": 1.0},
                            "input_video": "trimmed.mp4",
                        },
                    }
                ),
                encoding="utf-8",
            )

            validation = validate_gvhmr_source(
                root / "validation",
                source_materialization=materialization,
                gvhmr_json=gvhmr,
            )
            report = json.loads(validation.report_path.read_text(encoding="utf-8"))

        self.assertEqual(validation.status, "failed")
        self.assertFalse(report["passed"])
        self.assertIsNone(validation.validated_export_path)
        self.assertIn("source_id", [check["name"] for check in report["checks"] if check["status"] == "fail"])

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
