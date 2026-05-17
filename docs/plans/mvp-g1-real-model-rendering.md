# MVP G1 Real Model Rendering Plan

Status: IMPLEMENTED LOCAL SVG RENDER EVIDENCE; SIMULATOR MESH RENDERING REMAINS FOLLOW-ON

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
  -> local SVG render evidence path
  -> fixture or imported G1 pose stream
  -> front/side/top render evidence
  -> playback manifest consumable by the teaching demo
```

The stop condition is not "the G1 track exists". The implemented stop condition
is a verifiable local render manifest with front/side/top SVG frame evidence
from a G1 model descriptor and G1 visual track, while preserving the G1
non-scoring boundary. This proves the repo-owned render evidence contract. It
does not yet prove MuJoCo/Genesis simulator mesh rendering.

## Current Gap

- `robot-model register --fixture` writes a G1-like descriptor only.
- `tracks build` currently derives a visual skeleton from SMPL-X fixture
  joints; it does not produce real Unitree G1 joint angles.
- `demo play` draws 2D skeletons on canvas; it does not load MuJoCo, Genesis,
  Viser, URDF/MJCF files, or robot meshes.
- `render g1` now writes SVG/HTML render evidence from a model descriptor and
  G1 visual-track manifest; it is not simulator mesh rendering.
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

- A render command:

  ```bash
  PYTHONPATH=src python -m neodojo render g1 \
    --model-descriptor outputs/g1-real-model/robot-models/unitree_g1/manifest.json \
    --g1-track outputs/g1-visual/tracks/g1/manifest.json \
    --out outputs/g1-render
  ```

  Fixture model descriptors require `--allow-fixture-model` and are accepted
  only for CI/demo smoke paths.

- `outputs/g1-render/manifest.json`, ignored by git, containing:
  - model descriptor path and checksum
  - renderer backend and version
  - camera definitions
  - input track manifest
  - frame/screenshot paths
  - whether the pose stream is fixture, imported GMR, or real converted data
  - `g1_scoring_allowed: false`
- Low-resolution SVG/HTML render evidence under `outputs/`, not committed.
- Focused tests for manifest validation, missing-asset failure messages, and
  scoring-boundary preservation.

## Execution Tasks

1. Choose the first renderer backend.
   - [x] Use a dependency-light SVG schematic renderer first so the contract,
     frame evidence, and CI smoke path work without bundling G1 assets or
     adding simulator dependencies.
   - Keep MuJoCo/Genesis mesh rendering as a follow-on gap once user-supplied
     assets and simulator dependencies are stable.

2. Add a render manifest schema.
   - [x] Keep it separate from the G1 visual-track manifest.
   - [x] Store renderer backend, camera definitions, frame paths, and scoring
     metadata.
   - [x] Make fixture-vs-real status explicit for both the model descriptor and
     G1 track.

3. Load the real model descriptor.
   - [x] Refuse `fixture_descriptor` unless `--allow-fixture-model` is passed.
   - [x] Validate model path, mesh roots, and referenced mesh availability at
     registration time.
   - [x] Fail with actionable messages when assets are missing.

4. Produce a static real-model render first.
   - [x] Render deterministic front/side/top SVG frame evidence from the G1
     descriptor and visual track.
   - [x] Save SVG frames, an HTML evidence page, and a manifest.
   - This proves the right-side render contract and non-scoring boundary, while
     leaving real simulator mesh rendering as follow-on work.

5. Add a pose adapter.
   - [x] Consume the existing G1 visual-track manifest as the pose stream.
   - [x] Keep the current fixture-derived G1-like stream clearly marked as
     fixture.
   - [x] Do not pretend that SMPL-X keypoints alone are a valid full G1
     joint-angle source.

6. Connect rendered evidence to playback.
   - [x] Write a render manifest that later playback/public-demo commands can
     consume.
   - [x] Keep SMPL-X skeleton/teaching feedback as the scoring source.

7. Verify visually.
   - [x] Capture front/side/top SVG evidence.
   - [x] Keep outputs ignored and document how to reproduce the frame locally.
   - [ ] Confirm a MuJoCo/Genesis image contains a real robot mesh, not only
     line joints.

## Acceptance Criteria

- A user-supplied Unitree G1 URDF/MJCF plus meshes can be registered as a model
  descriptor and consumed by the local SVG render evidence command.
- The render command writes a manifest, front/side/top SVG frames, and a local
  HTML evidence page.
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

- Local upstream GMR execution remains external. Native robot-motion pickle
  parsing is now covered by `mvp-native-gmr-runner.md`, and normalized imported
  GMR JSON is supported by `mvp-gmr-import-track.md`.
- SMPL-X mesh/body-surface rendering; the current teaching demo still uses
  skeleton joints.
- MuJoCo/Genesis real robot mesh rendering from registered G1 assets.
- Viser synchronized 3D playback.
- Multi-camera offscreen capture hardening.
- Broader key-frame detection and geometry feedback beyond the first narrow
  detector.
- GPU-side GVHMR artifact generation from a real Baduanjin clip.
