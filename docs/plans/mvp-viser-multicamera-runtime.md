# MVP Viser Multi-Camera Runtime Plan

Status: PLANNED; BLOCKED ON RUNTIME DEPENDENCY AND INTERACTION DESIGN

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
- Local Viser dependency and browser access.
- Optional camera presets from simulator/render manifests.

## Outputs

- `neodojo demo serve-viser` or equivalent local runtime command.
- Synchronized timeline controls and camera/view selection.
- Overlay support for trajectories, annotations, and scoring-source labels.
- Visual smoke procedure with screenshots when browser tooling is available.

## Execution Tasks

1. Define runtime contract.
   - [ ] Reuse the existing scene/timeline contract where possible.
   - [ ] Identify extra fields needed for local interactivity.

2. Implement first Viser server.
   - [ ] Load SMPL-X and G1 tracks.
   - [ ] Add timeline synchronization.
   - [ ] Add camera presets and scoring-source labels.

3. Add smoke checks.
   - [ ] Verify server startup and nonblank rendered scene.
   - [ ] Capture screenshot evidence when browser tooling is available.

## Acceptance Evidence

- A local command starts a Viser teaching runtime from existing manifests.
- SMPL-X and G1 playback stay synchronized.
- The UI visibly preserves SMPL-X as the scoring source and G1 as visual-only.
- Static public-demo generation still works independently.

## Non-Goals

- Public hosting of the Viser runtime.
- Replacing GitHub Pages artifact publishing.
- Physics/control simulation.
- Full production UI polish in the first runtime slice.

## Stop Condition

Stop when a local Viser session can load the fixture scene, scrub synchronized
tracks, and produce a screenshot or when dependency/runtime blockers are
classified clearly.
