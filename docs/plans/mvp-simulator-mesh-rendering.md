# MVP Simulator Mesh Rendering Plan

Status: IMPLEMENTED OPTIONAL MUJOCO COMMAND; FINAL G1 ASSET PROOF PENDING

## Goal

Add a simulator-backed render evidence path beyond the local SVG schematic, so
registered URDF/MJCF assets can be rendered by MuJoCo when local dependencies
and robot assets are available:

```text
registered G1 model descriptor
  -> MuJoCo or Genesis model load
  -> imported or fixture G1 visual track pose
  -> front/side/top rendered frame evidence
  -> render manifest consumed by playback/public-demo
```

This proves the command and manifest path for real robot geometry while SMPL-X
remains the only teaching feedback source. The first automated smoke uses a
tiny synthetic MJCF model because real Unitree G1 assets must remain
user-supplied and untracked.

## Dependencies

- [mvp-g1-real-model-rendering.md](mvp-g1-real-model-rendering.md) owns the
  existing descriptor and SVG/HTML evidence boundary.
- [mvp-g1-visual-track.md](mvp-g1-visual-track.md) and
  [mvp-gmr-import-track.md](mvp-gmr-import-track.md) provide G1 track inputs.
- Optional `mujoco` Python package, available through the `sim` extra.
- Local Unitree G1 URDF/MJCF and mesh files are available outside tracked
  source for final proof.

## Inputs

- Registered Unitree G1 model descriptor.
- Mesh roots referenced by that descriptor.
- G1 visual-track manifest.
- MuJoCo Python/native dependency.

## Outputs

- Simulator render manifest with backend, model provenance, camera names, frame
  paths, and scoring boundary.
- Low-resolution front/side/top PNG frame images under ignored `outputs/`.
- A smoke command that confirms rendered pixels are nonblank and a real mesh was
  loaded.
- README/STATUS updates that keep SVG evidence and real simulator rendering
  distinct.
- CLI command:

  ```bash
  PYTHONPATH=src python -m neodojo render mujoco-g1 \
    --model-descriptor path/to/registered-g1-model/manifest.json \
    --g1-track outputs/g1-visual/tracks/g1/manifest.json \
    --out outputs/g1-mujoco-render
  ```

## Execution Tasks

1. Select first backend.
   - [x] Try MuJoCo first unless Genesis is materially easier with available G1
     assets.
   - [x] Record install/runtime constraints before adding a required dependency.
   - [x] Add MuJoCo as an optional `sim` extra, not a default dependency.

2. Load real G1 assets.
   - [x] Resolve URDF/MJCF and mesh-root paths from the descriptor.
   - [x] Fail clearly when assets are missing or fixture descriptors are used
     without an explicit fixture flag.
   - [ ] Verify against a real user-supplied Unitree G1 asset bundle.

3. Render evidence.
   - [x] Render a neutral-pose first slice from the registered model.
   - [x] Render front/side/top PNG images at CI-friendly resolution.
   - [x] Preserve `g1_scoring_allowed: false`.
   - [ ] Apply imported GMR joint angles to model qpos when a matching joint
     stream and real asset bundle are available.

4. Verify.
   - [x] Add tests around fixture-model rejection.
   - [x] Add an optional smoke that is skipped unless simulator dependency is
     available locally.
   - [x] Verify optional smoke with a tiny synthetic MJCF model.

## Acceptance Evidence

- A local command writes a MuJoCo render manifest and PNG image frames from a
  registered descriptor.
- The optional smoke check proves images are nonblank and not the existing SVG
  fallback.
- Generated mesh renders stay under ignored output paths.
- Docs do not claim the simulator path exists until the command and smoke pass.
- Final real Unitree G1 proof remains pending until user-supplied G1 assets are
  provided locally.

## Non-Goals

- Physics simulation or control.
- G1 scoring.
- Bundling Unitree assets or meshes.
- Replacing the public demo UI.
- Full-routine video rendering.

## Stop Condition

Stopped for the first slice when the optional MuJoCo command rendered nonblank
PNG frames from a registered MJCF descriptor and wrote a render manifest that
preserves the SMPL-X/G1 scoring boundary. Continue only when local real Unitree
G1 assets are available for final asset proof and qpos application.
