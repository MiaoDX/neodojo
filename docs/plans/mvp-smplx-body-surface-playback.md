# MVP SMPL-X Body Surface Playback Plan

Status: PLANNED; BLOCKED ON LICENSED SMPL-X MODEL ASSETS

## Goal

Add an optional body-surface playback path so teaching inspection can show more
than joints and bones:

```text
SMPL-X motion record
  -> licensed local SMPL-X model assets
  -> lightweight body surface or mesh frames
  -> teaching playback/public-demo surface layer
```

The surface layer should improve visual inspection while preserving the SMPL-X
joint track as the feedback/scoring source.

## Dependencies

- [mvp-local-motion-contract.md](mvp-local-motion-contract.md) provides the
  SMPL-X motion-record and teaching-track contracts.
- [mvp-teaching-playback-demo.md](mvp-teaching-playback-demo.md) provides the
  current joint/bone playback.
- User has local rights to SMPL-X model assets and keeps them outside git.

## Inputs

- SMPL-X motion-record manifest.
- Local SMPL-X model asset path and license/provenance notes.
- Shape/pose parameters or export fields sufficient to reconstruct a body
  surface.
- Playback scene/timeline contract.

## Outputs

- Optional SMPL-X surface manifest with asset provenance, frame count, timing,
  and generated surface artifact paths.
- Playback/public-demo layer that can toggle joints, bones, and surface.
- Tests for missing assets, timing mismatch, and fixture fallback behavior.

## Execution Tasks

1. Define asset contract.
   - [ ] Add local-only SMPL-X asset descriptor fields.
   - [ ] Reject missing assets with a clear licensing-safe error.

2. Generate surface data.
   - [ ] Choose lightweight mesh, point cloud, or silhouette output for the
     first slice.
   - [ ] Keep generated surface artifacts ignored.
   - [ ] Preserve timing and coordinate metadata from the motion record.

3. Integrate playback.
   - [ ] Add an optional surface layer to the teaching playback manifest.
   - [ ] Keep joint/bone playback working without SMPL-X assets.

## Acceptance Evidence

- A local command can generate an optional SMPL-X surface artifact from licensed
  local assets.
- Playback can show the surface layer without changing scoring semantics.
- The fixture/CI path remains dependency-light and does not require SMPL-X
  assets.

## Non-Goals

- Bundling SMPL-X model files.
- Replacing joint-level feedback.
- High-fidelity rendering or photorealistic body video.
- Hand/face refinement.

## Stop Condition

Stop when one optional local SMPL-X surface layer can be generated and viewed,
or when the blocker is classified as missing licensed assets, missing upstream
pose fields, or an implementation dependency issue.
