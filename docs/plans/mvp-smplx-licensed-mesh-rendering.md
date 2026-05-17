# MVP Licensed SMPL-X Mesh Rendering Plan

Status: IMPLEMENTED EXTERNAL LICENSED MESH-FRAME IMPORT; OFFICIAL BODY-MODEL EXECUTION REMAINS EXTERNAL

## Goal

Turn a motion record that already carries imported `neodojo.smplx_parameters.v1`
pose/shape data plus a local-only SMPL-X asset descriptor into inspectable
SMPL-X mesh surface playback artifacts:

```text
motion-record/manifest.json
  -> motion-record/smplx-parameters.json
  -> local-only licensed SMPL-X asset descriptor
  -> external local licensed SMPL-X mesh-frame JSON
  -> mesh/surface manifest for teaching/public playback
```

This is the follow-on to the implemented capsule proxy and mesh-input gate. The
implemented renderer boundary is deliberately local and external:
`neodojo smplx-surface mesh` imports a local `neodojo.smplx_mesh_frames.v1`
JSON written by a licensed SMPL-X renderer outside this repo. It validates the
asset descriptor, imported parameters, vertices, faces, frame count, and
scoring-source boundary, then writes `neodojo.smplx_mesh_surface.v1` evidence
under ignored `outputs/`.

The repo still must not copy, commit, execute, or redistribute official SMPL-X
model files. SMPL-X joints remain the teaching/scoring source; the mesh surface
is visual evidence only.

## Dependencies

- [mvp-smplx-body-surface-playback.md](mvp-smplx-body-surface-playback.md)
  provides the capsule proxy, local-only asset descriptor, and imported
  parameter boundary.
- [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) or another
  external import must provide a motion record with mesh-ready SMPL-X
  pose/shape parameters.
- A local licensed SMPL-X model asset remains outside git and is referenced by
  descriptor only.
- An external local renderer writes `neodojo.smplx_mesh_frames.v1` with
  constant vertex topology across frames.

## Inputs

- Motion record containing `smplx_parameters` with `global_orient`,
  `body_pose`, `betas`, and any optional fields preserved from import.
- Local-only SMPL-X asset descriptor from `neodojo smplx-surface
  register-assets`.
- Local `neodojo.smplx_mesh_frames.v1` JSON with `faces` and per-frame
  `vertices`.
- Output directory under ignored `outputs/`.

## Outputs

- Versioned mesh/surface manifest: `neodojo.smplx_mesh_surface.v1`.
- Generated mesh-surface data under ignored `outputs/smplx-mesh/`.
- Validation report recording parameter fields, asset descriptor, external
  renderer boundary, mesh frame count, vertex/face counts, coordinate metadata,
  and scoring-source boundary.
- Teaching/public-demo integration that can switch from capsule proxy to
  licensed mesh evidence when local mesh frames are supplied.

## Execution Tasks

1. Select renderer boundary.
   - [x] Choose a local licensed-asset-safe boundary:
     `external_licensed_smplx_mesh_frames.v1`.
   - [x] Store mesh frame data as vertices plus shared triangular faces in a
     versioned JSON artifact under ignored outputs.
   - [x] Keep all generated mesh artifacts and model assets out of git.

2. Validate inputs.
   - [x] Require local-only asset descriptor and existing local model file.
   - [x] Validate `neodojo.smplx_parameters.v1` required fields and frame count.
   - [x] Fail clearly for joint-only records, missing parameters, missing
     assets, mismatched mesh frames, invalid vertices/faces, or unsafe output
     paths.

3. Generate mesh evidence.
   - [x] Add `neodojo smplx-surface mesh --mesh-frames ...`.
   - [x] Write versioned manifest, mesh-surface data, and validation report under
     ignored `outputs/`.
   - [x] Preserve timing, coordinates, contact metadata, fixture/real-artifact
     status, and `scoring_source: smplx_joints`.

4. Integrate playback.
   - [x] Allow teaching/public demo manifests to reference licensed mesh evidence
     when present.
   - [x] Keep the dependency-light capsule proxy as the default CI path.
   - [x] Add focused tests using tiny fake/fixture-safe assets while reserving
     real SMPL-X asset execution for local-only external tooling.

## Acceptance Evidence

- A local command validates a local SMPL-X asset descriptor and a motion record
  with imported SMPL-X parameters without copying licensed assets.
- The command writes a versioned mesh/surface manifest and generated local
  evidence under ignored `outputs/`.
- Joint-only motion records still fail with clear guidance.
- Default fixture CI remains dependency-light and does not require SMPL-X model
  files.
- Teaching/public-demo artifacts can reference either the capsule proxy or the
  licensed mesh surface while preserving SMPL-X joint scoring.
- Docs distinguish capsule proxy evidence, externally generated licensed mesh
  evidence, and the absent built-in official SMPL-X body-model runner.

## Non-Goals

- Bundling or redistributing SMPL-X model files.
- Making licensed SMPL-X assets a default CI dependency.
- Executing the official SMPL-X Python body model inside the default repo
  command surface.
- Replacing SMPL-X joint-level scoring with mesh-only scoring.
- Photorealistic rendering, hand/face refinement, or video generation.

## Stop Condition

Stop when one local fixture-safe licensed-asset smoke can generate versioned
mesh evidence from an imported SMPL-X-parameter motion record, teaching/public
playback can reference that evidence, and the default fixture CI lane remains
dependency-light. Built-in official SMPL-X body-model execution remains an
external/local-asset concern until the repo deliberately adopts that dependency.
