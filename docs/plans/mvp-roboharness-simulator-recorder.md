# MVP Roboharness Or Simulator Recorder Plan

Status: IMPLEMENTED FIRST MUJOCO SIMULATOR RECORDER CONTRACT

## Goal

Replace generated SVG evidence and public-demo browser screenshots with a
direct recorder path when the runtime target is selected:

```text
scene/render/runtime target
  -> roboharness or simulator/browser recorder
  -> synchronized camera captures
  -> capture bundle manifest
  -> CI/local artifact upload
```

The implemented lane now provides generated multi-camera evidence, a real
headless Chromium screenshot of the public demo, and an optional direct
simulator-recorder manifest that wraps MuJoCo offscreen render evidence. Direct
roboharness integration and live Viser browser capture remain future backend
choices, not prerequisites for this first recorder contract.

## Dependencies

- [mvp-roboharness-capture-boundary.md](mvp-roboharness-capture-boundary.md)
  provides the capture bundle shape and optional public-demo browser capture.
- [mvp-simulator-mesh-rendering.md](mvp-simulator-mesh-rendering.md) provides
  optional MuJoCo render evidence when local assets are present.
- [mvp-viser-production-teaching-ui.md](mvp-viser-production-teaching-ui.md) may
  provide a live local UI target if the recorder captures Viser instead of
  simulator output.
- The first recorder target is selected: MuJoCo simulator offscreen frames from
  `neodojo render mujoco-g1`.

## Inputs

- Public-demo, Viser, simulator, or render manifest to capture.
- Local runtime dependencies for the selected recorder.
- Local untracked robot/SMPL-X assets if the selected recorder needs them.
- Output directory under ignored `outputs/`.

## Outputs

- Recorder manifest: `neodojo.recorder_capture.v1`.
- Synchronized front/side/top or otherwise named camera captures.
- Capture bundle integration that records the selected recorder backend,
  camera roles, artifact references, frame count, and nonblank checks.
- CI/local artifact upload path that does not track generated videos or images
  in git.

## Execution Tasks

1. Select recorder target.
   - [x] Choose direct roboharness, simulator offscreen capture, or live Viser
     browser capture for the first real recorder lane.
   - [x] Record why the selected target is the narrowest useful proof.
   - [x] Decide whether the dependency is optional local-only or part of CI.

2. Define recorder contract.
   - [x] Add versioned recorder manifest with backend, cameras, frame count,
     source manifests, scoring-source boundary, and generated artifact refs.
   - [x] Validate output paths stay under ignored `outputs/`.
   - [x] Keep generated images/videos/logs out of tracked source.

3. Implement capture.
   - [x] Add a CLI command or Make target for the selected recorder.
   - [x] Write nonblank camera artifacts and manifest evidence.
   - [x] Integrate the recorder manifest into `neodojo capture bundle`.

4. Verify.
   - [x] Add focused tests for manifest validation and missing-artifact errors.
   - [x] Preserve optional local MuJoCo smoke through the existing
     `render mujoco-g1` tests when `mujoco` is installed.
   - [x] Keep default CI dependency-light; the recorder contract is tested with
     fixture-safe MuJoCo-shaped manifests and real MuJoCo capture remains
     optional local work.

## Acceptance Evidence

- A selected recorder backend produces nonblank synchronized camera artifacts
  through `neodojo render mujoco-g1`.
- The capture bundle references recorder artifacts and clearly identifies the
  backend.
- Default fixture/demo commands remain usable without heavyweight recorder
  dependencies unless the target is explicitly promoted into CI.
- Docs distinguish generated SVG evidence, public-demo browser screenshot
  evidence, and direct recorder evidence.

## Non-Goals

- Running GVHMR/GMR or generating real motion artifacts.
- Committing videos, screenshots, logs, or model assets.
- Turning G1 or simulator output into the scoring source.
- Supporting every possible recorder backend in the first implementation.

## Stop Condition

Stop condition reached for the first recorder backend: `neodojo capture
recorder` validates MuJoCo offscreen render evidence, writes
`neodojo.recorder_capture.v1`, and `neodojo capture bundle` can include that
manifest while preserving the SMPL-X scoring boundary. Direct roboharness
integration and live Viser browser capture remain future backend choices.
