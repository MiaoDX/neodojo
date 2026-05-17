# MVP SMPL-X Body Surface Playback Plan

Status: IMPLEMENTED SURFACE PROXY, LICENSED-ASSET BOUNDARY, PARAMETER IMPORT, AND EXTERNAL MESH-FRAME IMPORT

## Goal

Add an optional body-surface playback path so teaching inspection can show more
than joints and bones:

```text
SMPL-X motion record
  -> dependency-light capsule surface proxy from teaching joints
  -> optional licensed local SMPL-X model asset descriptor
  -> lightweight proxy or external mesh frames
  -> teaching playback/public-demo surface layer
```

The first implemented surface layer improves fixture/public demo inspection
while preserving the SMPL-X joint track as the feedback/scoring source. The
default fixture path is still the capsule proxy and is not a licensed SMPL-X
body-model mesh. The follow-on mesh path now imports externally generated local
mesh frames through a licensed-asset-safe manifest boundary. Imported GVHMR JSON
can preserve optional `smplx_parameters` in a versioned data file so the mesh
import path has a stable pose/shape parameter boundary.

## Dependencies

- [mvp-local-motion-contract.md](mvp-local-motion-contract.md) provides the
  SMPL-X motion-record and teaching-track contracts.
- [mvp-teaching-playback-demo.md](mvp-teaching-playback-demo.md) provides the
  current joint/bone playback.
- The first proxy path needs only the existing teaching joints.
- External mesh-frame import requires local rights to SMPL-X model assets kept
  outside git and mesh frames generated outside the repo.

## Inputs

- SMPL-X motion-record manifest.
- Optional local SMPL-X model asset path and license/provenance notes for mesh
  evidence.
- Existing teaching joints for the current capsule proxy.
- Shape/pose parameters or export fields sufficient to validate external mesh
  evidence.
- Playback scene/timeline contract.

## Outputs

- Optional SMPL-X surface proxy manifest with frame count, timing, coordinates,
  contact metadata, and generated surface data paths.
- Playback/public-demo layer that can carry and display joints, bones, and the
  surface proxy.
- Tests for surface manifest loading, frame-count mismatch, and fixture
  fallback behavior.
- Optional `neodojo.smplx_parameters.v1` motion-record data file when an
  imported GVHMR JSON provides mesh-ready pose/shape parameters.
- Optional `neodojo.smplx_mesh_surface.v1` manifest when a local external
  `neodojo.smplx_mesh_frames.v1` JSON is supplied.
- CLI command:

  ```bash
  PYTHONPATH=src python -m neodojo smplx-surface proxy \
    --motion-record outputs/motion-contract \
    --out outputs/smplx-surface
  ```

- Local-only licensed asset descriptor command:

  ```bash
  PYTHONPATH=src python -m neodojo smplx-surface register-assets \
    --model path/to/SMPLX_NEUTRAL.npz \
    --license "local licensed SMPL-X asset; do not commit" \
    --out outputs/smplx-assets
  ```

## Execution Tasks

1. Define asset contract.
   - [x] Add a versioned `neodojo.smplx_surface_proxy.v1` manifest for the
     dependency-light capsule proxy.
   - [x] Mark `licensed_smplx_mesh: false` and `scoring_allowed: false`.
   - [x] Add local-only licensed SMPL-X asset descriptor fields for the future
     full-mesh path.
   - [x] Reject missing licensed assets with a clear licensing-safe error when
     the full-mesh path exists.
   - [x] Preserve optional imported SMPL-X pose/shape parameters in a versioned
     motion-record data file for the mesh evidence path.
   - [x] Add a versioned external mesh-frame import boundary for licensed mesh
     evidence.

2. Generate surface data.
   - [x] Choose a lightweight capsule/silhouette proxy derived from teaching
     joints for the first slice.
   - [x] Keep generated surface artifacts under ignored `outputs/`.
   - [x] Preserve timing, coordinate, and contact metadata from the motion
     record.
   - [x] Validate external mesh frames with constant topology, numeric vertices,
     and triangular faces.

3. Integrate playback.
   - [x] Add an optional surface layer to the teaching playback manifest.
   - [x] Render the surface proxy behind SMPL-X joints in the teaching demo.
   - [x] Carry the surface proxy into the public-demo scene, HTML, screenshot,
     and smoke labels.
   - [x] Carry the optional licensed mesh surface into the same teaching/public
     playback layer without changing scoring semantics.
   - [x] Keep joint/bone playback working without SMPL-X assets.

## Acceptance Evidence

- A local command can generate an optional SMPL-X capsule surface proxy without
  licensed local assets.
- Playback can show the surface layer without changing scoring semantics.
- The fixture/CI path remains dependency-light and does not require SMPL-X
  assets.
- `make demo-public` includes the surface proxy in the generated teaching and
  public demo artifacts.
- Local-only licensed SMPL-X asset descriptor registration validates an existing
  file path without copying or committing the asset.
- External GVHMR JSON imports can preserve optional `smplx_parameters` with
  `global_orient`, `body_pose`, `betas`, and optional frame fields in
  `motion-record/smplx-parameters.json`.
- The mesh path rejects joint-only motion records with a clear message
  explaining that mesh-ready SMPL-X pose/shape parameters are required.
- When mesh-ready parameters are present, the mesh path validates the parameter
  data, licensed asset descriptor, local mesh frames, vertices, and faces before
  writing visual-only mesh evidence.

## Non-Goals

- Bundling SMPL-X model files.
- Replacing joint-level feedback.
- High-fidelity rendering or photorealistic body video.
- Hand/face refinement.
- Claiming the capsule proxy is a real SMPL-X mesh.
- Executing or redistributing official SMPL-X body-model assets in the default
  repo command surface.

## Stop Condition

Stop for this slice when a local SMPL-X capsule surface proxy can be generated,
viewed in teaching playback, included in the public demo, smoke tested without
licensed SMPL-X assets, and the licensed-asset path has a local-only descriptor,
optional imported SMPL-X parameter preservation, external mesh-frame import, and
clear rejection for missing assets, joint-only motion records, or invalid mesh
frames.
