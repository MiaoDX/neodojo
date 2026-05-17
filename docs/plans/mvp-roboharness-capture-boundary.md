# MVP Roboharness Capture Boundary Plan

Status: IMPLEMENTED FIRST GENERATED-EVIDENCE BUNDLE; REAL OFFSCREEN RECORDER REMAINS FOLLOW-ON

## Goal

Add a roboharness-style multi-camera evidence boundary without adding a
simulator/browser recorder dependency yet:

```text
public-demo artifact
  -> Viser front/side/top preview evidence
  -> G1 front/side/top render evidence
  -> capture bundle manifest
  -> CI artifact
```

This slice gives the pipeline one explicit place to collect and validate
multi-camera evidence. It stays honest that the first implementation validates
generated SVG/HTML/recording artifacts only; it is not a real roboharness
integration, live browser capture, simulator video recorder, or production
teaching UI.

## Dependencies

- [mvp-devex-ci-surface.md](mvp-devex-ci-surface.md) provides the local
  `make demo-public` orchestration and CI artifact lane.
- [mvp-visualization-and-public-demo.md](mvp-visualization-and-public-demo.md)
  provides the public-demo scene, HTML, screenshot, and `.rrd` target artifact.
- [mvp-viser-multicamera-runtime.md](mvp-viser-multicamera-runtime.md)
  provides generated front/side/top Viser preview screenshots.
- [mvp-g1-real-model-rendering.md](mvp-g1-real-model-rendering.md) provides
  G1 front/side/top render evidence.

## Inputs

- `outputs/public-demo/manifest.json` or an equivalent public-demo manifest.
- `outputs/viser-runtime/viser-runtime.json` or an equivalent Viser runtime
  manifest with front/side/top generated preview screenshots.
- `outputs/g1-render/manifest.json` or an equivalent G1 render manifest with
  front/side/top frame evidence.
- Existing fixture-only labels and SMPL-X/G1 scoring metadata.

## Outputs

- `neodojo capture bundle` CLI command.
- `outputs/capture/manifest.json` using
  `neodojo.capture_bundle.v1`.
- A manifest style marker:
  `roboharness_multi_camera_evidence_manifest`.
- Validated references to:
  - public-demo HTML, scene, recording, and screenshot artifacts
  - Viser front/side/top generated preview screenshots
  - G1 front/side/top render frames
- CI artifact upload that includes `outputs/capture` alongside the public demo.
- README, README.zh, STATUS, and plan-index updates that describe the boundary
  as generated evidence, not a real recorder.

## Execution Tasks

1. Add capture bundle contract.
   - [x] Define `neodojo.capture_bundle.v1`.
   - [x] Record fixture-only status, SMPL-X scoring source, and
     `g1_scoring_allowed: false`.
   - [x] Label the bundle as generated evidence only.

2. Validate upstream artifacts.
   - [x] Reuse public-demo smoke checks for HTML, scene, recording, and
     screenshot evidence.
   - [x] Require Viser front/side/top preview screenshots and expected labels.
   - [x] Require G1 front/side/top render frames and nonblank payloads.

3. Add command and orchestration.
   - [x] Add `neodojo capture bundle`.
   - [x] Run it from `make demo-public` after public-demo and Viser artifacts
     are generated.
   - [x] Upload the capture bundle in the CI workflow artifact set.

4. Add tests.
   - [x] Test the happy path from fixture motion through capture manifest.
   - [x] Test missing multi-camera evidence fails clearly.
   - [x] Keep optional roboharness, browser, simulator, and Viser dependencies
     out of the default test path.

5. Update docs.
   - [x] Keep README.md and README.zh aligned.
   - [x] Update STATUS.md and this plan index.
   - [x] Preserve fixture-only limitations and follow-on recorder gaps.

## Acceptance Evidence

- `make demo-public` writes `outputs/capture/manifest.json`.
- The capture manifest references public-demo, Viser preview, and G1 render
  evidence.
- The manifest contains front, side, and top view entries.
- The command fails if a referenced Viser preview or G1 frame is missing or
  blank.
- The manifest preserves `scoring_source: smplx` and
  `g1_scoring_allowed: false`.
- CI uploads the capture bundle as an artifact without committing generated
  outputs.

## Non-Goals

- Importing or depending on roboharness in the default repo path.
- Recording simulator video.
- Browser-driven screenshot capture of the live Viser client.
- Replacing the Rerun/GitHub Pages public-demo artifact.
- Proving qigong motion correctness or a real GVHMR/GMR conversion.

## Follow-On Gaps After This Plan

- Replace generated SVG evidence with a real offscreen simulator/browser
  recorder once the runtime target is selected.
- Add live-client Viser browser capture when browser automation becomes part of
  the verification lane.
- Decide whether a future roboharness dependency should be optional, vendored,
  or integrated through a manifest-only adapter.

## Stop Condition

Stop when the default fixture lane produces a validated capture bundle manifest,
the bundle is included in CI artifacts, tests cover missing view evidence, and
docs clearly distinguish the generated evidence boundary from a real
roboharness/offscreen recording integration.
