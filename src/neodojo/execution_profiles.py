from __future__ import annotations

from typing import Any

EXECUTION_PROFILE_SCHEMA = "neodojo.execution_profile.v1"

G1_SCHEMATIC_EVIDENCE_PROFILE = "g1_schematic_evidence"
G1_MUJOCO_MESH_EVIDENCE_PROFILE = "g1_mujoco_mesh_evidence"
G1_ACTUAL_MUJOCO_REPLAY_EVIDENCE_PROFILE = "g1_actual_mujoco_replay_evidence"
G1_PUBLIC_ACTUAL_MUJOCO_REPLAY_EVIDENCE_PROFILE = "g1_public_actual_mujoco_replay_evidence"

G1_RENDER_EXECUTION_PROFILE_CHOICES = (
    "auto",
    G1_SCHEMATIC_EVIDENCE_PROFILE,
    G1_MUJOCO_MESH_EVIDENCE_PROFILE,
    G1_ACTUAL_MUJOCO_REPLAY_EVIDENCE_PROFILE,
)

G1_MUJOCO_RENDER_EXECUTION_PROFILE_CHOICES = (
    "auto",
    G1_MUJOCO_MESH_EVIDENCE_PROFILE,
    G1_ACTUAL_MUJOCO_REPLAY_EVIDENCE_PROFILE,
)


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _check(name: str, *, passed: bool, required: bool, message: str) -> dict[str, Any]:
    return {
        "name": name,
        "required": required,
        "passed": bool(passed),
        "message": message,
    }


def _profile_status(checks: list[dict[str, Any]]) -> str:
    failed_required = [
        check for check in checks
        if check.get("required") is True and check.get("passed") is not True
    ]
    return "satisfied" if not failed_required else "unsatisfied"


def _profile(profile_id: str, *, claim: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": EXECUTION_PROFILE_SCHEMA,
        "profile": profile_id,
        "claim": claim,
        "status": _profile_status(checks),
        "checks": checks,
    }


def select_g1_render_execution_profile(
    *,
    renderer_backend: str,
    actual_g1_model_replay: bool,
) -> str:
    if renderer_backend == "neodojo_svg_schematic.v1":
        return G1_SCHEMATIC_EVIDENCE_PROFILE
    if actual_g1_model_replay:
        return G1_ACTUAL_MUJOCO_REPLAY_EVIDENCE_PROFILE
    return G1_MUJOCO_MESH_EVIDENCE_PROFILE


def build_g1_render_execution_profile(
    *,
    requested_profile: str = "auto",
    renderer_backend: str,
    scoring_source: str,
    g1_scoring_allowed: bool,
    model_fixture_only: bool | None,
    track_fixture_only: bool | None,
    pose_application: dict[str, Any] | None = None,
    replay_frames: dict[str, Any] | None = None,
    mesh_loaded: bool | None = None,
    nonblank_pixel_check: bool | None = None,
    actual_g1_model_replay: bool = False,
) -> dict[str, Any]:
    profile_id = requested_profile
    if profile_id == "auto":
        profile_id = select_g1_render_execution_profile(
            renderer_backend=renderer_backend,
            actual_g1_model_replay=actual_g1_model_replay,
        )
    if profile_id not in G1_RENDER_EXECUTION_PROFILE_CHOICES or profile_id == "auto":
        raise ValueError(f"unsupported G1 execution profile: {requested_profile}")

    common_checks = [
        _check(
            "smplx_scoring_source",
            passed=scoring_source == "smplx",
            required=True,
            message="Teaching and scoring evidence must remain SMPL-X based.",
        ),
        _check(
            "g1_non_scoring",
            passed=g1_scoring_allowed is False,
            required=True,
            message="G1 evidence is visual-only and cannot enable scoring.",
        ),
    ]

    if profile_id == G1_SCHEMATIC_EVIDENCE_PROFILE:
        checks = [
            *common_checks,
            _check(
                "schematic_renderer",
                passed=renderer_backend == "neodojo_svg_schematic.v1",
                required=True,
                message="Schematic evidence must use the dependency-light SVG renderer.",
            ),
            _check(
                "no_actual_replay_claim",
                passed=actual_g1_model_replay is False,
                required=True,
                message="Schematic evidence must not claim actual G1 model replay.",
            ),
        ]
        return _profile(
            profile_id,
            claim="local schematic G1 visual evidence",
            checks=checks,
        )

    if profile_id == G1_MUJOCO_MESH_EVIDENCE_PROFILE:
        checks = [
            *common_checks,
            _check(
                "mujoco_renderer",
                passed=renderer_backend == "mujoco_python_offscreen.v1",
                required=True,
                message="Mesh evidence must come from the MuJoCo offscreen renderer.",
            ),
            _check(
                "registered_model_descriptor",
                passed=model_fixture_only is False,
                required=True,
                message="MuJoCo mesh evidence requires a non-fixture G1 model descriptor.",
            ),
            _check(
                "mesh_loaded",
                passed=mesh_loaded is True,
                required=True,
                message="MuJoCo mesh evidence must prove the model mesh was loaded.",
            ),
            _check(
                "nonblank_rendered_views",
                passed=nonblank_pixel_check is True,
                required=True,
                message="Rendered views must be nonblank.",
            ),
        ]
        return _profile(
            profile_id,
            claim="MuJoCo G1 mesh evidence without an actual replay claim",
            checks=checks,
        )

    pose_application = pose_application or {}
    replay_frames = replay_frames or {}
    checks = [
        *common_checks,
        _check(
            "mujoco_renderer",
            passed=renderer_backend == "mujoco_python_offscreen.v1",
            required=True,
            message="Actual G1 replay must come from the MuJoCo offscreen renderer.",
        ),
        _check(
            "registered_model_descriptor",
            passed=model_fixture_only is False,
            required=True,
            message="Actual G1 replay requires a non-fixture G1 model descriptor.",
        ),
        _check(
            "non_fixture_gmr_track",
            passed=track_fixture_only is False,
            required=True,
            message="Actual G1 replay requires a non-fixture imported GMR track.",
        ),
        _check(
            "imported_gmr_pose_source",
            passed=pose_application.get("source") == "imported_gmr_joint_angles",
            required=True,
            message="Actual G1 replay must apply imported GMR Unitree G1 joint angles.",
        ),
        _check(
            "selected_frame_applies_joints",
            passed=(_as_int(pose_application.get("applied_joint_count")) or 0) > 0,
            required=True,
            message="The selected frame must apply at least one matching G1 joint to MuJoCo qpos.",
        ),
        _check(
            "replay_frame_sequence_available",
            passed=replay_frames.get("available") is True and (_as_int(replay_frames.get("frame_count")) or 0) > 0,
            required=True,
            message="Actual G1 replay must write a frame sequence.",
        ),
        _check(
            "replay_frames_are_nonblank",
            passed=replay_frames.get("nonblank_pixel_check") is True,
            required=True,
            message="Every replay frame must be nonblank.",
        ),
        _check(
            "replay_frames_change",
            passed=replay_frames.get("changed_frame_check") is True,
            required=True,
            message="The replay sequence must contain visible frame changes.",
        ),
        _check(
            "replay_applies_joints",
            passed=(_as_int(replay_frames.get("applied_joint_count_min")) or 0) > 0,
            required=True,
            message="Every sampled replay frame must apply at least one matching G1 joint.",
        ),
        _check(
            "actual_replay_claim_matches_profile",
            passed=actual_g1_model_replay is True and replay_frames.get("actual_g1_model_replay") is True,
            required=True,
            message="The manifest-level actual replay claim must match the replay-frame evidence.",
        ),
    ]
    return _profile(
        profile_id,
        claim="actual Unitree G1 MuJoCo frame-sequence replay from imported GMR joint angles",
        checks=checks,
    )


def build_public_g1_replay_execution_profile(
    *,
    render_execution_profile: dict[str, Any] | None,
    actual_g1_model_replay: bool,
    visual_style: str,
    public_media_available: bool,
    scoring_source: str,
    g1_scoring_allowed: bool,
) -> dict[str, Any]:
    if not actual_g1_model_replay:
        return _profile(
            G1_SCHEMATIC_EVIDENCE_PROFILE,
            claim="public schematic G1 visual evidence",
            checks=[
                _check(
                    "smplx_scoring_source",
                    passed=scoring_source == "smplx",
                    required=True,
                    message="Public teaching replay keeps SMPL-X as the scoring source.",
                ),
                _check(
                    "g1_non_scoring",
                    passed=g1_scoring_allowed is False,
                    required=True,
                    message="Public G1 evidence remains visual-only.",
                ),
                _check(
                    "no_actual_replay_claim",
                    passed=actual_g1_model_replay is False,
                    required=True,
                    message="Schematic public evidence must not claim actual G1 model replay.",
                ),
            ],
        )

    render_profile_ok = bool(
        isinstance(render_execution_profile, dict)
        and render_execution_profile.get("schema") == EXECUTION_PROFILE_SCHEMA
        and render_execution_profile.get("profile") == G1_ACTUAL_MUJOCO_REPLAY_EVIDENCE_PROFILE
        and render_execution_profile.get("status") == "satisfied"
    )
    checks = [
        _check(
            "smplx_scoring_source",
            passed=scoring_source == "smplx",
            required=True,
            message="Public teaching replay keeps SMPL-X as the scoring source.",
        ),
        _check(
            "g1_non_scoring",
            passed=g1_scoring_allowed is False,
            required=True,
            message="Public G1 evidence remains visual-only.",
        ),
        _check(
            "render_profile_satisfied",
            passed=render_profile_ok,
            required=True,
            message="Public actual replay must be backed by a satisfied render execution profile.",
        ),
        _check(
            "public_media_available",
            passed=public_media_available,
            required=True,
            message="Public actual replay must expose copied PNG frames or encoded video media.",
        ),
        _check(
            "public_visual_style_is_replay",
            passed=visual_style in {"mujoco-video-replay.v1", "mujoco-png-frame-sequence.v1"},
            required=True,
            message="Public actual replay must use a MuJoCo replay visual style.",
        ),
    ]
    return _profile(
        G1_PUBLIC_ACTUAL_MUJOCO_REPLAY_EVIDENCE_PROFILE,
        claim="public teaching HTML consumes actual G1 MuJoCo replay media",
        checks=checks,
    )


def require_satisfied_execution_profile(profile: dict[str, Any], *, label: str) -> None:
    if profile.get("schema") != EXECUTION_PROFILE_SCHEMA:
        raise ValueError(f"{label} must use schema {EXECUTION_PROFILE_SCHEMA}")
    if profile.get("status") == "satisfied":
        return
    failed = [
        str(check.get("name"))
        for check in profile.get("checks", [])
        if isinstance(check, dict)
        and check.get("required") is True
        and check.get("passed") is not True
    ]
    suffix = f": {', '.join(failed)}" if failed else ""
    raise ValueError(f"{label} did not satisfy execution profile {profile.get('profile')}{suffix}")
