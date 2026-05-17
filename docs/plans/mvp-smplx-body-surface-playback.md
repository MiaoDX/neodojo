# MVP SMPL-X Body Surface Playback Plan

Status: IMPLEMENTED SURFACE PROXY; LICENSED SMPL-X MESH REMAINS FOLLOW-ON

## Goal

Add an optional body-surface playback path so teaching inspection can show more
than joints and bones:

```text
SMPL-X motion record
  -> dependency-light capsule surface proxy from teaching joints
  -> optional future licensed local SMPL-X model assets
  -> lightweight body surface or mesh frames
  -> teaching playback/public-demo surface layer
```

The first implemented surface layer improves fixture/public demo inspection
while preserving the SMPL-X joint track as the feedback/scoring source. It is
not a licensed SMPL-X body-model mesh. Full SMPL-X mesh generation still waits
for local licensed model assets and richer pose parameters.

## Dependencies

- [mvp-local-motion-contract.md](mvp-local-motion-contract.md) provides the
  SMPL-X motion-record and teaching-track contracts.
- [mvp-teaching-playback-demo.md](mvp-teaching-playback-demo.md) provides the
  current joint/bone playback.
- The first proxy path needs only the existing teaching joints.
- Future full-mesh generation requires local rights to SMPL-X model assets kept
  outside git.

## Inputs

- SMPL-X motion-record manifest.
- Optional local SMPL-X model asset path and license/provenance notes for the
  future full-mesh path.
- Existing teaching joints for the current capsule proxy.
- Shape/pose parameters or export fields sufficient to reconstruct a body
  surface for the future full-mesh path.
- Playback scene/timeline contract.

## Outputs

- Optional SMPL-X surface proxy manifest with frame count, timing, coordinates,
  contact metadata, and generated surface data paths.
- Playback/public-demo layer that can carry and display joints, bones, and the
  surface proxy.
- Tests for surface manifest loading, frame-count mismatch, and fixture
  fallback behavior.
- CLI command:

  ```bash
  PYTHONPATH=src python -m neodojo smplx-surface proxy \
    --motion-record outputs/motion-contract \
    --out outputs/smplx-surface
  ```

## Execution Tasks

1. Define asset contract.
   - [x] Add a versioned `neodojo.smplx_surface_proxy.v1` manifest for the
     dependency-light capsule proxy.
   - [x] Mark `licensed_smplx_mesh: false` and `scoring_allowed: false`.
   - [ ] Add local-only licensed SMPL-X asset descriptor fields for the future
     full-mesh path.
   - [ ] Reject missing licensed assets with a clear licensing-safe error when
     the full-mesh path exists.

2. Generate surface data.
   - [x] Choose a lightweight capsule/silhouette proxy derived from teaching
     joints for the first slice.
   - [x] Keep generated surface artifacts under ignored `outputs/`.
   - [x] Preserve timing, coordinate, and contact metadata from the motion
     record.

3. Integrate playback.
   - [x] Add an optional surface layer to the teaching playback manifest.
   - [x] Render the surface proxy behind SMPL-X joints in the teaching demo.
   - [x] Carry the surface proxy into the public-demo scene, HTML, screenshot,
     and smoke labels.
   - [x] Keep joint/bone playback working without SMPL-X assets.

## Acceptance Evidence

- A local command can generate an optional SMPL-X capsule surface proxy without
  licensed local assets.
- Playback can show the surface layer without changing scoring semantics.
- The fixture/CI path remains dependency-light and does not require SMPL-X
  assets.
- `make demo-public` includes the surface proxy in the generated teaching and
  public demo artifacts.

## Non-Goals

- Bundling SMPL-X model files.
- Replacing joint-level feedback.
- High-fidelity rendering or photorealistic body video.
- Hand/face refinement.
- Claiming the capsule proxy is a real SMPL-X mesh.

## Stop Condition

Stopped for the first slice when a local SMPL-X capsule surface proxy can be
generated, viewed in teaching playback, included in the public demo, and smoke
tested without licensed SMPL-X assets. The remaining follow-on is full licensed
SMPL-X mesh/body-model playback once local assets and richer pose fields are
available.
