# MVP Roboharness Capture Boundary Plan

Status: IMPLEMENTED GENERATED BUNDLE AND BROWSER PUBLIC-DEMO CAPTURE; CI VERIFIED; ROBOHARNESS/SIMULATOR RECORDER REMAINS FOLLOW-ON

## Goal

Add a roboharness-style multi-camera evidence boundary without adding a
simulator/browser recorder dependency yet:

```text
public-demo artifact
  -> Viser front/side/top preview evidence
  -> G1 front/side/top render evidence
  -> optional browser-rendered public-demo screenshot evidence
  -> capture bundle manifest
  -> CI artifact
```

This slice gives the pipeline one explicit place to collect and validate
multi-camera evidence. It stays honest that the first implementation validates
generated SVG/HTML/recording artifacts and, when the optional browser lane is
installed, a real headless Chromium rendering of the public-demo HTML. It is
still not a direct roboharness integration, simulator video recorder, live
Viser browser capture, or production teaching UI.

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
- Optional `outputs/browser-capture/manifest.json` from
  `neodojo demo browser-smoke`.
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
- Optional browser-rendered public-demo screenshot manifest using
  `neodojo.browser_capture.v1`.
- CI artifact upload that includes `outputs/capture` and optional
  `outputs/browser-capture` alongside the public demo.
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
   - [x] Optionally validate browser-rendered public-demo screenshot evidence.

3. Add command and orchestration.
   - [x] Add `neodojo capture bundle`.
   - [x] Add `neodojo demo browser-smoke` for optional headless Chromium
     public-demo capture.
   - [x] Run it from `make demo-public` after public-demo and Viser artifacts
     are generated.
   - [x] Run `make demo-public-browser` in CI to include browser capture.
   - [x] Upload the capture bundle in the CI workflow artifact set.

4. Add tests.
   - [x] Test the happy path from fixture motion through capture manifest.
   - [x] Test optional browser-capture manifest inclusion.
   - [x] Test missing multi-camera evidence fails clearly.
   - [x] Keep optional roboharness, browser, simulator, and Viser dependencies
     out of the default test path.

5. Update docs.
   - [x] Keep README.md and README.zh aligned.
   - [x] Update STATUS.md and this plan index.
   - [x] Preserve fixture-only limitations and follow-on recorder gaps.

## Acceptance Evidence

- `make demo-public` writes `outputs/capture/manifest.json`.
- `make demo-public-browser` writes `outputs/browser-capture/manifest.json`,
  `outputs/browser-capture/public-demo-browser.png`, and refreshes
  `outputs/capture/manifest.json` with browser evidence.
- The capture manifest references public-demo, Viser preview, and G1 render
  evidence.
- The manifest contains front, side, and top view entries.
- The command fails if a referenced Viser preview or G1 frame is missing or
  blank.
- When browser capture is supplied, the bundle references the Chromium PNG
  screenshot and marks `real_browser_capture: true` without claiming direct
  roboharness integration.
- The manifest preserves `scoring_source: smplx` and
  `g1_scoring_allowed: false`.
- CI uploads the capture bundle and browser-capture artifacts without
  committing generated outputs, verified by
  `https://github.com/MiaoDX/neodojo/actions/runs/26000413142`.

## Non-Goals

- Importing or depending on roboharness in the default repo path.
- Recording simulator video.
- Browser-driven screenshot capture of the live Viser client.
- Making Playwright a default dependency for `make demo-public`.
- Replacing the Rerun/GitHub Pages public-demo artifact.
- Proving qigong motion correctness or a real GVHMR/GMR conversion.

## Follow-On Gaps After This Plan

- Replace generated SVG evidence and public-demo browser screenshots with a
  real offscreen simulator or roboharness recorder once the runtime target is
  selected.
- Add live-client Viser browser capture when browser automation targets the
  local runtime client, not only the static public demo.
- Decide whether a future roboharness dependency should be optional, vendored,
  or integrated through a manifest-only adapter.

## Stop Condition

Stop when the default fixture lane produces a validated capture bundle manifest,
the optional browser lane can add a real Chromium public-demo screenshot to the
bundle, the bundle is included in CI artifacts, tests cover missing view
evidence, and docs clearly distinguish generated/browser evidence from a direct
roboharness or simulator recorder integration.
