# MVP Viser Production Teaching UI Plan

Status: IMPLEMENTED FIRST PRODUCTION REVIEW-LOOP CONTRACT AND CONTROLS

## Goal

Move beyond the first optional Viser runtime into a production-quality local
teaching interface for repeated motion review:

```text
scene/timeline contract
  -> Viser local runtime
  -> teaching-focused camera/timeline controls
  -> feedback drilldown
  -> dependency-light preview evidence
```

This plan should keep the public GitHub Pages demo as the lightweight
fixture/public artifact while making Viser the richer local teaching surface.

## Dependencies

- [mvp-viser-multicamera-runtime.md](mvp-viser-multicamera-runtime.md) provides
  the first optional Viser server, scene contract, controls, and preview
  screenshots.
- [mvp-feedback-routine-review.md](mvp-feedback-routine-review.md) provides
  routine feedback terms and key-frame anchors.
- [mvp-roboharness-capture-boundary.md](mvp-roboharness-capture-boundary.md)
  provides browser/public-demo capture evidence; live Viser browser capture is
  a follow-on extension covered by
  [mvp-roboharness-simulator-recorder.md](mvp-roboharness-simulator-recorder.md).

## Inputs

- Teaching playback manifest or public-demo scene/timeline contract.
- SMPL-X/G1 tracks, annotation manifests, routine feedback report, and optional
  render evidence.
- Optional Viser dependency installed locally.
- Browser automation dependency if live-client capture becomes part of the
  verification lane.

## Outputs

- A production teaching UI contract layered on top of the existing Viser
  runtime manifest.
- Clear controls for frame stepping, key-frame navigation, camera presets,
  trajectory visibility, surface/mesh visibility, and feedback detail.
- Dependency-light contract/preview smoke evidence, with live-client browser
  capture deferred to the recorder plan.
- README/STATUS updates that distinguish local Viser teaching UI from the
  static public demo.

## Execution Tasks

1. Scope the teaching workflow.
   - [x] Define the first production review loop: inspect, jump to feedback
     anchor, compare SMPL-X/G1 views, and read scoring-source evidence.
   - [x] Decide which controls are required for the first repeated-use local
     session and which belong in later UX polish.
   - [x] Preserve fixture-only and real-artifact labels in the UI.

2. Improve runtime contract.
   - [x] Add production UI metadata for control grouping, feedback drilldown,
     visibility toggles, and camera presets.
   - [x] Keep the current scene/timeline contract backward compatible.
   - [x] Preserve `scoring_source: smplx` and `g1_scoring_allowed: false`.

3. Implement Viser UI polish.
   - [x] Add ergonomic controls for frame stepping, speed, key-frame jump, and
     layer toggles.
   - [x] Surface routine feedback terms and pass/fail evidence without turning
     G1 into a scoring source.
   - [x] Keep `--write-contract-only` useful for dependency-light CI evidence.

4. Add verification.
   - [x] Extend dependency-light Viser runtime contract tests.
   - [x] Preserve the optional Viser smoke startup test for environments where
     `viser` is installed.
   - [x] Keep default CI green without requiring Viser.
   - [x] Defer live-client browser capture to
     [mvp-roboharness-simulator-recorder.md](mvp-roboharness-simulator-recorder.md).

## Acceptance Evidence

- A local Viser session can expose the scoped teaching review loop without
  relying on the static public demo when the optional `viser` dependency is
  installed.
- Controls expose camera, timeline, layer visibility, and feedback navigation in
  a way that is visible in the runtime contract and dependency-light preview
  smoke.
- SMPL-X remains the only scoring source throughout the UI.
- Default `make demo-public` and `make verify` remain dependency-light.
- Docs clearly separate production local Viser UI from fixture-only public
  Pages.

## Non-Goals

- Hosting Viser publicly.
- Replacing the static GitHub Pages public demo.
- Simulator physics, robot control, or policy training.
- Rebuilding the UI as a separate frontend app before the Viser workflow proves
  useful.

## Stop Condition

Stop condition reached for the first production review-loop slice: the runtime
manifest records `neodojo.viser_teaching_ui.v1` metadata, the optional Viser
server exposes frame stepping, camera, layer, and feedback controls, and the
default verification path stays dependency-light. Live-client Viser browser
capture remains part of the recorder follow-on plan.
