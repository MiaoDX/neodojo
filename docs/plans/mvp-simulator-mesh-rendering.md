# MVP Simulator Mesh Rendering Plan

Status: PLANNED; BLOCKED ON USER-SUPPLIED G1 ASSETS AND SIMULATOR DEPENDENCY

## Goal

Replace local SVG render evidence with a real Unitree G1 mesh render from
local URDF/MJCF plus meshes:

```text
registered G1 model descriptor
  -> MuJoCo or Genesis model load
  -> imported or fixture G1 visual track pose
  -> front/side/top rendered frame evidence
  -> render manifest consumed by playback/public-demo
```

This proves that the visual companion can use real robot geometry while SMPL-X
remains the only teaching feedback source.

## Dependencies

- [mvp-g1-real-model-rendering.md](mvp-g1-real-model-rendering.md) owns the
  existing descriptor and SVG/HTML evidence boundary.
- [mvp-g1-visual-track.md](mvp-g1-visual-track.md) and
  [mvp-gmr-import-track.md](mvp-gmr-import-track.md) provide G1 track inputs.
- Local Unitree G1 URDF/MJCF and mesh files are available outside tracked
  source.

## Inputs

- Registered Unitree G1 model descriptor.
- Mesh roots referenced by that descriptor.
- G1 visual-track manifest.
- Chosen simulator backend and installed Python/native dependency.

## Outputs

- Simulator render manifest with backend, model provenance, camera names, frame
  paths, and scoring boundary.
- Low-resolution front/side/top frame images under ignored `outputs/`.
- A smoke command that confirms rendered pixels are nonblank and a real mesh was
  loaded.
- README/STATUS updates that keep SVG evidence and real simulator rendering
  distinct.

## Execution Tasks

1. Select first backend.
   - [ ] Try MuJoCo first unless Genesis is materially easier with available G1
     assets.
   - [ ] Record install/runtime constraints before adding a required dependency.

2. Load real G1 assets.
   - [ ] Resolve URDF/MJCF and mesh-root paths from the descriptor.
   - [ ] Fail clearly when assets are missing or fixture descriptors are used
     without an explicit fixture flag.

3. Render evidence.
   - [ ] Apply one representative G1 track frame or neutral pose.
   - [ ] Render front/side/top images at CI-friendly resolution.
   - [ ] Preserve `g1_scoring_allowed: false`.

4. Verify.
   - [ ] Add tests around manifest validation and missing-asset errors.
   - [ ] Add an optional smoke that is skipped unless simulator assets are
     available locally.

## Acceptance Evidence

- A local command writes a real-mesh render manifest and image frames from a
  user-supplied G1 descriptor.
- The smoke check proves images are nonblank and not the existing SVG fallback.
- Generated mesh renders stay under ignored output paths.
- Docs do not claim the simulator path exists until the command and smoke pass.

## Non-Goals

- Physics simulation or control.
- G1 scoring.
- Bundling Unitree assets or meshes.
- Replacing the public demo UI.
- Full-routine video rendering.

## Stop Condition

Stop when one real G1 mesh frame set renders from local assets and the manifest
can be consumed by existing playback/public-demo plumbing, or when the blocker
is classified as an asset, dependency, or model-format issue.
