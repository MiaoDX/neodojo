# MVP Viser Multi-Camera Runtime Plan

Status: IMPLEMENTED FIRST OPTIONAL LOCAL SERVER, CAMERA CONTROLS, AND MULTI-CAMERA PREVIEW EVIDENCE

## Goal

Build the future local/server teaching runtime that sits beyond the static
fixture demo:

```text
scene/timeline contract
  -> Viser local server
  -> synchronized SMPL-X and G1 views
  -> multi-camera controls and overlays
  -> optional offscreen screenshot capture
```

Viser is the richer local teaching surface. It should not replace the Rerun
public-demo artifact or require simulator rendering to ship the first runtime
slice.

The first optional runtime now exists as `neodojo demo serve-viser`. It consumes
the same scene/timeline contract as the public-demo lane, starts a real local
Viser server when the `viser` extra is installed, and exposes synchronized
SMPL-X/G1 tracks with a frame slider, camera preset buttons, annotation-anchor
navigation, trajectory overlays, and explicit scoring-source labels. The
contract writer also emits dependency-light front/side/top SVG preview
screenshots from the same scene contract for visual smoke evidence. The
production review-loop polish is covered by
[mvp-viser-production-teaching-ui.md](mvp-viser-production-teaching-ui.md).

## Dependencies

- [mvp-visualization-and-public-demo.md](mvp-visualization-and-public-demo.md)
  defines the scene/timeline contract.
- [mvp-teaching-playback-demo.md](mvp-teaching-playback-demo.md) defines
  playback semantics.
- [mvp-simulator-mesh-rendering.md](mvp-simulator-mesh-rendering.md) can later
  provide real robot render evidence.

## Inputs

- Public-demo scene/timeline JSON or teaching playback manifest.
- SMPL-X track, G1 track, and annotation manifests.
- Optional Viser dependency through the `viser` extra and browser access.
- Optional camera presets from simulator/render manifests.

## Outputs

- `neodojo demo serve-viser` or equivalent local runtime command.
- Synchronized timeline controls and camera/view selection.
- Overlay support for trajectories, annotations, and scoring-source labels.
- Visual smoke procedure with generated front/side/top screenshots.

## Execution Tasks

1. Define runtime contract.
   - [x] Reuse the existing scene/timeline contract where possible.
   - [x] Identify extra fields needed for local interactivity.

2. Implement first Viser server.
   - [x] Load SMPL-X and G1 tracks.
   - [x] Add timeline synchronization with a frame slider.
   - [x] Add camera-preset metadata and scoring-source labels.
   - [x] Add camera preset buttons and annotation-anchor navigation.

3. Add smoke checks.
   - [x] Verify server startup and populated scene through an optional
     `--smoke-start` path.
   - [x] Capture front/side/top SVG screenshot evidence from the Viser
     scene/timeline contract.

## Acceptance Evidence

- A local command starts a Viser teaching runtime from existing manifests.
- SMPL-X and G1 playback stay synchronized.
- The UI visibly preserves SMPL-X as the scoring source and G1 as visual-only.
- Camera preset controls and annotation-anchor buttons are exposed in the local
  Viser GUI contract and server path.
- Static public-demo generation still works independently.
- Optional dependency tests can start and stop the server without making Viser a
  default dependency.
- `make demo-public` writes the Viser runtime contract and generated
  multi-camera preview screenshots without requiring the optional Viser package.

## Non-Goals

- Public hosting of the Viser runtime.
- Replacing GitHub Pages artifact publishing.
- Physics/control simulation.
- Full production UI polish and browser-verified interaction polish.
- Browser-driven capture of the live Viser client.

## Stop Condition

Stop for this slice when a local Viser session can load the fixture scene,
expose synchronized SMPL-X/G1 tracks, provide camera and annotation controls,
pass optional server-start smoke, and write generated multi-camera preview
screenshots from the runtime contract. Continue when the next task needs
browser-driven live-client capture or production teaching polish.
