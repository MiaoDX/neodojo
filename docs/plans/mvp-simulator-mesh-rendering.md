# MVP Simulator Mesh Rendering Plan

Status: IMPLEMENTED OPTIONAL MUJOCO COMMAND, REAL G1 ASSET SMOKE, AND GMR QPOS APPLICATION

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
tiny synthetic MJCF model because real Unitree G1 assets must remain untracked.
The asset-load proof has also been verified locally with an untracked clone of
`https://github.com/unitreerobotics/unitree_mujoco` at revision
`517e161b4a89d1a62831357314d8aa6d90d9c18d`, registering
`unitree_robots/g1/g1_29dof.xml` and rendering front/side/top PNG frames.
The qpos proof has been verified against the same local G1 asset descriptor and
an imported-GMR fixture track: matching `left_hip_pitch_joint`,
`right_hip_pitch_joint`, and `waist_yaw_joint` values were applied to MuJoCo
`qpos`, the PNG frames were nonblank, and the render manifest recorded zero
missing joints for that smoke.

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
- Pose-application manifest evidence for imported GMR joint angles: applied,
  missing, skipped, and clipped joints.
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
   - [x] Verify against a real local, untracked Unitree G1 asset bundle from
     the upstream `unitreerobotics/unitree_mujoco` repository.

3. Render evidence.
   - [x] Render a neutral-pose first slice from the registered model.
   - [x] Render front/side/top PNG images at CI-friendly resolution.
   - [x] Preserve `g1_scoring_allowed: false`.
   - [x] Apply imported GMR joint angles to model qpos when a matching joint
     stream and real asset bundle are available.

4. Verify.
   - [x] Add tests around fixture-model rejection.
   - [x] Add an optional smoke that is skipped unless simulator dependency is
     available locally.
   - [x] Verify optional smoke with a tiny synthetic MJCF model.
   - [x] Verify imported GMR joint-angle qpos application with the optional
     MuJoCo test and the local untracked Unitree G1 MJCF asset.

## Acceptance Evidence

- A local command writes a MuJoCo render manifest and PNG image frames from a
  registered descriptor.
- The optional smoke check proves images are nonblank and not the existing SVG
  fallback.
- Generated mesh renders stay under ignored output paths.
- Docs do not claim the simulator path exists until the command and smoke pass.
- Real Unitree G1 asset-load proof has been verified from an untracked local
  asset clone; generated renders remain under ignored output paths.
- Imported GMR joint angles are applied to matching MuJoCo hinge/slide qpos
  entries when present, and the manifest records applied, missing, skipped, and
  clipped joints.

## Non-Goals

- Physics simulation or control.
- G1 scoring.
- Bundling Unitree assets or meshes.
- Replacing the public demo UI.
- Full-routine video rendering.

## Stop Condition

Stop for this slice when the optional MuJoCo command renders nonblank PNG
frames from an untracked local Unitree G1 MJCF descriptor, applies matching
imported GMR joint angles to `qpos`, and writes a render manifest that preserves
the SMPL-X/G1 scoring boundary.
