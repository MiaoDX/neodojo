# MVP G1 Real Model Rendering Plan

Status: PLANNED LOCAL NON-GPU SLICE

## Purpose

Close the gap between the current fixture-only G1 visual track and an actual
Unitree G1-looking render.

The existing `mvp-g1-visual-track.md` slice creates a model descriptor,
derived visual-track manifest, and scoring separation report. The existing
`mvp-teaching-playback-demo.md` slice consumes that manifest, but it draws a
2D G1-like skeleton in HTML. This plan is the missing local slice that proves
a real Unitree G1 URDF/MJCF plus meshes can be loaded, posed, and rendered
before the GPU GVHMR conversion gate.

This is still not the end-to-end real-video pipeline. It should run on a local
macOS CPU development machine with user-supplied robot assets and small
fixture/imported pose data.

## Goal

Create the first real G1 rendering path:

```text
Unitree G1 URDF/MJCF + meshes
  -> robot-model descriptor
  -> lightweight MuJoCo or Genesis loader
  -> fixture or imported G1 pose stream
  -> front/side/top render evidence
  -> playback manifest consumable by the teaching demo
```

The stop condition is not "the G1 track exists". The stop condition is a
verifiable local screenshot/frame manifest showing the real Unitree G1 model,
not the current canvas skeleton.

## Current Gap

- `robot-model register --fixture` writes a G1-like descriptor only.
- `tracks build` currently derives a visual skeleton from SMPL-X fixture
  joints; it does not produce real Unitree G1 joint angles.
- `demo play` draws 2D skeletons on canvas; it does not load MuJoCo, Genesis,
  Viser, URDF/MJCF files, or robot meshes.
- A real model render needs both the robot asset loader and a pose source that
  matches the robot model's actuated joints.

## Inputs

- A real Unitree G1 model path, supplied locally and not committed:
  `*.urdf`, `*.xml`, or `*.mjcf`.
- Local mesh roots for the model descriptor, also not committed.
- Existing SMPL-X motion-record and teaching-track manifests.
- Existing G1 visual-track manifest for provenance and timing.
- Optional external GMR output containing Unitree G1 joint-angle frames.

Example existing asset-registration command:

```bash
PYTHONPATH=src python -m neodojo robot-model register \
  --robot unitree_g1 \
  --model /path/to/unitree_g1.xml \
  --mesh-root /path/to/unitree_g1/meshes \
  --out outputs/g1-real-model
```

## Outputs To Add

- A render command, for example:

  ```bash
  PYTHONPATH=src python -m neodojo render g1 \
    --model-descriptor outputs/g1-real-model/robot-models/unitree_g1/manifest.json \
    --g1-track outputs/g1-visual/tracks/g1/manifest.json \
    --out outputs/g1-render
  ```

- `outputs/g1-render/manifest.json`, ignored by git, containing:
  - model descriptor path and checksum
  - renderer backend and version
  - camera definitions
  - input track manifest
  - frame/screenshot paths
  - whether the pose stream is fixture, imported GMR, or real converted data
  - `g1_scoring_allowed: false`
- Low-resolution render evidence under `outputs/`, not committed.
- Focused tests for manifest validation, missing-asset failure messages, and
  scoring-boundary preservation.

## Execution Tasks

1. Choose the first renderer backend.
   - Prefer MuJoCo first if the local G1 MJCF/URDF loads cleanly and can render
     low-resolution frames on CPU.
   - Use Genesis only if its local install path is lighter or better matches
     available G1 assets.
   - Do not introduce a broad simulator abstraction until one real backend is
     proven.

2. Add a render manifest schema.
   - Keep it separate from the G1 visual-track manifest.
   - Store provenance, camera definitions, frame paths, and scoring metadata.
   - Make fixture-vs-real status explicit.

3. Load the real model descriptor.
   - Refuse `fixture_descriptor` for final acceptance.
   - Validate model path, mesh roots, and referenced mesh availability.
   - Fail with actionable messages when assets are missing.

4. Produce a static real-model render first.
   - Render neutral or deterministic pose from the real G1 model.
   - Save at least one screenshot/frame and a manifest.
   - This proves the right-side viewer can become a real robot, even before GMR
     animation is complete.

5. Add a pose adapter.
   - If imported GMR Unitree G1 joint angles are available, consume them.
   - If not, add a small deterministic G1 joint-angle fixture that drives a few
     visible joints and is clearly marked as fixture.
   - Do not pretend that SMPL-X keypoints alone are a valid full G1 joint-angle
     source.

6. Connect rendered evidence to playback.
   - Let `demo play` or a follow-up playback command consume the G1 render
     manifest.
   - The first integration may use still frames or a low-frame-count image
     sequence.
   - Keep SMPL-X skeleton/teaching feedback as the scoring source.

7. Verify visually.
   - Capture front/side/top evidence.
   - Confirm the image contains a real robot mesh, not only line joints.
   - Keep outputs ignored and document how to reproduce the frame locally.

## Acceptance Criteria

- A user-supplied Unitree G1 URDF/MJCF plus meshes can be registered and loaded
  by the chosen renderer.
- The render command writes a manifest and at least one local screenshot/frame
  showing the real G1 model.
- Missing model files, missing mesh roots, and fixture descriptors fail clearly.
- The render manifest preserves `g1_scoring_allowed: false`.
- A fixture or imported-GMR pose stream can move at least a small set of visible
  G1 joints, or the plan explicitly stops at static render proof with the
  animation gap documented.
- No raw robot assets, rendered videos, logs, or large outputs are committed.

## Non-Goals

- Running GVHMR full-video inference.
- Producing the first real source-video SMPL-X artifact.
- Solving full GMR integration if no GMR joint-angle export is available.
- Using G1 as the teaching-feedback source.
- High-quality ray tracing or full-routine batch rendering.
- Physical robot control, RL, or sim2real work.

## Follow-On Gaps After This Plan

- Real GMR adapter or imported GMR output support for full Unitree G1 joint
  angles.
- SMPL-X mesh/body-surface rendering; the current teaching demo still uses
  skeleton joints.
- Viser synchronized 3D playback.
- Multi-camera offscreen capture hardening.
- Automatic key-frame detection and broader geometry feedback.
- GPU-side GVHMR artifact generation from a real Baduanjin clip.
