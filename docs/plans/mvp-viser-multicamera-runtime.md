# MVP Viser Multi-Camera Runtime Plan

Status: IMPLEMENTED FIRST OPTIONAL LOCAL SERVER; MULTI-CAMERA OFFSCREEN CAPTURE REMAINS FOLLOW-ON

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
SMPL-X/G1 tracks with a frame slider, trajectory overlays, and explicit
scoring-source labels. Browser screenshot capture and richer multi-camera
interaction remain follow-on work.

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
- Visual smoke procedure with screenshots when browser tooling is available.

## Execution Tasks

1. Define runtime contract.
   - [x] Reuse the existing scene/timeline contract where possible.
   - [x] Identify extra fields needed for local interactivity.

2. Implement first Viser server.
   - [x] Load SMPL-X and G1 tracks.
   - [x] Add timeline synchronization with a frame slider.
   - [x] Add camera-preset metadata and scoring-source labels.

3. Add smoke checks.
   - [x] Verify server startup and populated scene through an optional
     `--smoke-start` path.
   - [ ] Capture screenshot evidence when browser tooling is available.

## Acceptance Evidence

- A local command starts a Viser teaching runtime from existing manifests.
- SMPL-X and G1 playback stay synchronized.
- The UI visibly preserves SMPL-X as the scoring source and G1 as visual-only.
- Static public-demo generation still works independently.
- Optional dependency tests can start and stop the server without making Viser a
  default dependency.

## Non-Goals

- Public hosting of the Viser runtime.
- Replacing GitHub Pages artifact publishing.
- Physics/control simulation.
- Full production UI polish in the first runtime slice.

## Stop Condition

Stopped for the first slice when a local Viser session could load the fixture
scene, expose synchronized SMPL-X/G1 tracks, and pass optional server-start
smoke. Continue when the next task needs browser screenshot capture,
multi-camera offscreen evidence, or production teaching UX.
