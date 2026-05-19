---
refactor_scope: real-g1-model-replay
status: DONE
accepted_severities:
  - P0
  - P1
  - P2
last_verified: 2026-05-19
---

# Refactor Scope: Real G1 Model Replay

## Status

DONE

## Target

Replace the current right-panel G1 schematic in the real-demo/public-demo path
with a true Unitree G1 model replay rendered from MuJoCo/roboharness assets and
GMR-produced Unitree G1 joint angles.

The current public-demo HTML can label the right panel as a G1 robot model
replay while still drawing a canvas schematic derived from the visual track.
That is a false-positive boundary for the real Baduanjin pipeline. The fixed
pipeline must fail closed unless all real replay inputs are present:

```text
local Baduanjin video clip
  -> GVHMR SMPL-X motion record
  -> local GMR Unitree G1 joint-angle output
  -> imported G1 visual-track contract
  -> roboharness/robot_descriptions Unitree G1 MJCF descriptor
  -> MuJoCo rendered G1 frame sequence
  -> public teaching HTML with SMPL-X left and actual G1 model replay right
```

SMPL-X remains the teaching and scoring source. G1 remains a visual-only
companion track.

## Accepted Severities

- P0: Public-demo or audit passes while the right panel is not an actual G1
  model replay.
- P1: Missing local GMR execution support blocks the Baduanjin real-demo from
  producing Unitree G1 joint angles.
- P1: MuJoCo render evidence is static single-frame evidence instead of a
  synchronized frame sequence usable by the HTML replay.
- P2: Fixture-derived G1 tracks, fixture model descriptors, or schematic render
  labels remain as confusing defaults in real-demo commands.
- P2: roboharness dependency setup uses PyPI instead of a pinned Git source.

## Accepted Cleanup Checklist

1. Add the real replay dependency surface.
   - Add an optional dependency group for real G1 replay using a pinned Git
     source for `roboharness[demo]`, not PyPI.
   - Keep default fixture CI and default package install independent of
     roboharness, MuJoCo, robot model assets, and local GMR runtime.
   - Document the `uv` install command for the optional Git dependency.

2. Register the actual Unitree G1 model.
   - Add a command such as `neodojo robot-model register-roboharness-g1`.
   - Load `robot_descriptions.g1_mj_description.MJCF_PATH` through the
     roboharness demo dependency stack.
   - Write a non-fixture G1 MJCF descriptor that records source package,
     source commit/dependency, model path, mesh root, model format, and
     descriptor provenance.

3. Run or wrap local GMR for the Baduanjin clip.
   - Add the local execution path that turns the GVHMR/SMPL-X motion record into
     a native GMR Unitree G1 robot-motion artifact.
   - Feed that artifact through the existing `tracks normalize-gmr-pkl` and
     `tracks import-gmr-json` boundary.
   - Mark SMPL-X-derived or fixture G1 visual tracks as unacceptable for
     actual G1 model replay.

4. Render a real G1 frame sequence.
   - Extend `neodojo render mujoco-g1` or add a dedicated replay command that
     renders per-frame PNGs from the real G1 MJCF descriptor.
   - Apply imported/native GMR joint angles to matching MuJoCo qpos entries on
     every rendered frame.
   - Manifest fields must distinguish actual replay from neutral-pose or
     single-frame evidence, including applied/missing joint counts, frame
     paths, timing, renderer backend, and nonblank/changed-frame checks.

5. Update the teaching public-demo.
   - When the render manifest contains a real MuJoCo G1 frame sequence, the
     right panel must display the rendered G1 image frames synchronized to the
     SMPL-X left panel.
   - When real frames are missing, the UI and manifest must label the right
     panel as schematic evidence, not actual G1 model replay.
   - `real-conversion import-demo` must accept the imported GMR track and real
     G1 descriptor/render artifacts instead of silently generating fixture
     fallbacks for the actual replay lane.

6. Harden verification.
   - Add strict audit checks for: real GVHMR artifact, native/imported GMR G1
     joint angles, non-fixture G1 descriptor, MuJoCo rendered frame sequence,
     visible frame changes, and public HTML consumption of those frames.
   - `make verify-real` or a new explicit real replay verifier must fail if any
     actual-replay input is absent.

## Parked Cross-Seam / Future Ideas

- Colab, hosted GPU, self-hosted Actions GPU, and Pages promotion paths remain
  out of scope for this refactor.
- High-fidelity robot control, physics validation, RL, sim2real, and using G1
  as a scoring source remain out of scope.
- Full-routine 12-minute rendering optimization can be handled after the
  80-92 second Baduanjin proof clip is correct.
- Meshcat or Viser live interactive embedding can be added after deterministic
  static HTML frame replay is correct.

## Evidence Ladder

- L1: Unit tests for dependency metadata, GMR normalization/import, descriptor
  generation, fail-closed public-demo labels, and render manifest semantics.
- L2: Contract tests proving manifests require real GMR joint angles and a
  non-fixture model descriptor before claiming actual G1 replay.
- L4: Local MuJoCo render test with a real or tiny MJCF model proving nonblank
  rendered frames and changed pixels across replay frames.
- L4: Local Baduanjin integration run from GVHMR output through GMR, G1 render
  frames, public-demo HTML, and strict verification.

## Stop Condition

The refactor is done when the local Baduanjin proof clip can regenerate
`outputs/real-demo/public-demo/index.html` with:

- SMPL-X replay on the left;
- actual Unitree G1 MuJoCo model PNG frame replay on the right;
- a synchronized timeline;
- manifest/audit evidence that the G1 pose source is imported/native GMR joint
  angles;
- strict verification that fails if the right panel falls back to a schematic,
  fixture model, neutral pose, or static single-frame render;
- no committed raw videos, model assets, generated motion files, rendered
  frames, checkpoints, or logs.

## Execution Log

- 2026-05-19: Plan created after inspecting the current `real-demo` path,
  `render mujoco-g1`, GMR import boundaries, and the local
  `/home/mi/ws/gogo/roboharness` package. User selected local GMR execution and
  a Git-source roboharness dependency instead of PyPI.
- 2026-05-19: Implemented the fail-closed command/contract surface: pinned
  optional `real-g1-replay` dependency, `register-roboharness-g1`, local GMR
  run wrapper, MuJoCo replay-frame manifest fields, public HTML schematic-vs-
  actual labels with PNG frame consumption, `real-conversion import-demo`
  support for supplied G1 render artifacts, and stricter actual-replay audit
  checks. This checkpoint still awaited a local Baduanjin run with real GMR
  output, a non-fixture MJCF descriptor, and a nonblank/changing MuJoCo frame
  sequence under ignored `outputs/`.
- 2026-05-19: Completed the local ignored Baduanjin `80s-92s` proof. Fixed MJCF
  `compiler meshdir` asset resolution for the roboharness/robot_descriptions G1
  descriptor, added a headless local GMR execution path that saves all native
  retargeted frames without opening MuJoCo's viewer, imported the resulting 300
  Unitree G1 joint-angle frames, rendered a 300-frame nonblank/changing MuJoCo
  PNG replay sequence, regenerated `outputs/real-demo/public-demo/index.html`
  with actual G1 replay frames, and verified the strict audit with
  `make verify-real REAL_ARTIFACT_SOURCE_MATERIALIZATION=outputs/real-conversion-motion-80-92/source-materialized/source-materialization.json REAL_ARTIFACT_GVHMR_JSON=outputs/real-conversion-motion-80-92/gpu-run/gvhmr-smplx-joints.json REAL_ARTIFACT_OUT=outputs/real-demo`.
