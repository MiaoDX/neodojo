# MVP Roboharness Or Simulator Recorder Plan

Status: FOLLOW-ON; NEED RECORDER TARGET DECISION AND LOCAL RUNTIME ASSETS

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

The current implemented lane already provides generated multi-camera evidence
and a real headless Chromium screenshot of the public demo. This follow-on
covers direct recorder integration for simulator or runtime camera evidence.

## Dependencies

- [mvp-roboharness-capture-boundary.md](mvp-roboharness-capture-boundary.md)
  provides the capture bundle shape and optional public-demo browser capture.
- [mvp-simulator-mesh-rendering.md](mvp-simulator-mesh-rendering.md) provides
  optional MuJoCo render evidence when local assets are present.
- [mvp-viser-production-teaching-ui.md](mvp-viser-production-teaching-ui.md) may
  provide a live local UI target if the recorder captures Viser instead of
  simulator output.
- A recorder target is selected: direct roboharness integration, simulator
  offscreen frames/video, or live Viser browser capture.

## Inputs

- Public-demo, Viser, simulator, or render manifest to capture.
- Local runtime dependencies for the selected recorder.
- Local untracked robot/SMPL-X assets if the selected recorder needs them.
- Output directory under ignored `outputs/`.

## Outputs

- Recorder manifest, for example `neodojo.recorder_capture.v1`.
- Synchronized front/side/top or otherwise named camera captures.
- Capture bundle integration that records the selected recorder backend,
  camera roles, artifact references, frame count, and nonblank checks.
- CI/local artifact upload path that does not track generated videos or images
  in git.

## Execution Tasks

1. Select recorder target.
   - [ ] Choose direct roboharness, simulator offscreen capture, or live Viser
     browser capture for the first real recorder lane.
   - [ ] Record why the selected target is the narrowest useful proof.
   - [ ] Decide whether the dependency is optional local-only or part of CI.

2. Define recorder contract.
   - [ ] Add versioned recorder manifest with backend, cameras, frame count,
     source manifests, scoring-source boundary, and generated artifact refs.
   - [ ] Validate output paths stay under ignored `outputs/`.
   - [ ] Keep generated images/videos/logs out of tracked source.

3. Implement capture.
   - [ ] Add a CLI command or Make target for the selected recorder.
   - [ ] Write nonblank camera artifacts and manifest evidence.
   - [ ] Integrate the recorder manifest into `neodojo capture bundle`.

4. Verify.
   - [ ] Add focused tests for manifest validation and missing-artifact errors.
   - [ ] Add optional local smoke for the real recorder backend.
   - [ ] Add CI only if the dependency/runtime is stable and licensing-safe.

## Acceptance Evidence

- A selected recorder backend produces nonblank synchronized camera artifacts.
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

Stop when one selected recorder backend writes versioned nonblank capture
evidence and the capture bundle can validate it, or when the remaining blocker
is a recorder target decision, missing local runtime asset, unstable dependency,
or CI licensing/runtime limitation.
