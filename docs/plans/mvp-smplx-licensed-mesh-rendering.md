# MVP Licensed SMPL-X Mesh Rendering Plan

Status: BLOCKED ON LOCAL LICENSED SMPL-X ASSETS AND RENDERER CHOICE

## Goal

Turn a motion record that already carries imported `neodojo.smplx_parameters.v1`
pose/shape data plus a local-only SMPL-X asset descriptor into inspectable
SMPL-X body mesh playback artifacts:

```text
motion-record/manifest.json
  -> motion-record/smplx-parameters.json
  -> local-only licensed SMPL-X asset descriptor
  -> licensed-asset-safe mesh generation
  -> mesh/surface manifest for teaching/public playback
```

This is the follow-on to the implemented capsule proxy and mesh-input gate. It
must preserve SMPL-X as the teaching/scoring source and must never copy or
commit SMPL-X model files.

## Dependencies

- [mvp-smplx-body-surface-playback.md](mvp-smplx-body-surface-playback.md)
  provides the capsule proxy, local-only asset descriptor, and imported
  parameter boundary.
- [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) or another
  external import must provide a motion record with mesh-ready SMPL-X
  pose/shape parameters.
- A local licensed SMPL-X model asset is available outside git.
- A renderer/library path is selected, such as the official SMPL-X Python
  package plus a dependency-light mesh export, MuJoCo/Genesis mesh ingestion, or
  another local-only renderer.

## Inputs

- Motion record containing `smplx_parameters` with `global_orient`,
  `body_pose`, `betas`, and any needed optional fields.
- Local-only SMPL-X asset descriptor from `neodojo smplx-surface
  register-assets`.
- Renderer/library dependency decision and install notes.
- Output directory under ignored `outputs/`.

## Outputs

- Versioned mesh/surface manifest, for example `neodojo.smplx_mesh_surface.v1`.
- Generated mesh frame data or renderer references under ignored `outputs/`.
- Validation report recording parameter shapes, asset descriptor, renderer
  version, frame count, coordinate convention, and scoring-source boundary.
- Optional teaching/public-demo integration that can switch from capsule proxy
  to licensed mesh evidence when local assets are present.

## Execution Tasks

1. Select renderer boundary.
   - [ ] Choose a local licensed-asset-safe renderer/library path.
   - [ ] Decide whether mesh frame data is stored as compact vertices/faces,
     renderer snapshots, or another manifest-referenced format.
   - [ ] Keep all generated mesh artifacts and model assets out of git.

2. Validate inputs.
   - [ ] Require local-only asset descriptor and existing local model file.
   - [ ] Validate `neodojo.smplx_parameters.v1` required fields and accepted
     shapes for the selected renderer.
   - [ ] Fail clearly for joint-only records, missing parameters, missing
     assets, unsupported renderer dependencies, or unsafe output paths.

3. Generate mesh evidence.
   - [ ] Add a CLI command for the selected mesh path.
   - [ ] Write versioned manifest and generated data under ignored `outputs/`.
   - [ ] Preserve timing, coordinates, contact metadata, fixture/real-artifact
     status, and `scoring_source: smplx`.

4. Integrate playback.
   - [ ] Allow teaching/public demo manifests to reference licensed mesh
     evidence when present.
   - [ ] Keep the dependency-light capsule proxy as the default CI path.
   - [ ] Add focused tests using tiny fake/fixture-safe assets where possible,
     while reserving real SMPL-X asset validation for local-only smoke tests.

## Acceptance Evidence

- A local command can validate a real local SMPL-X asset descriptor and a motion
  record with imported SMPL-X parameters without copying licensed assets.
- The command writes a versioned mesh/surface manifest and generated local
  evidence under ignored `outputs/`.
- Joint-only motion records still fail with clear guidance.
- Default fixture CI remains dependency-light and does not require SMPL-X model
  files.
- Docs continue to distinguish capsule proxy evidence from licensed SMPL-X mesh
  playback.

## Non-Goals

- Bundling or redistributing SMPL-X model files.
- Making licensed SMPL-X assets a default CI dependency.
- Replacing SMPL-X joint-level scoring with mesh-only scoring.
- Photorealistic rendering, hand/face refinement, or video generation.

## Stop Condition

Stop when one local licensed-asset smoke can generate versioned mesh evidence
from an imported SMPL-X-parameter motion record, or when the blocker is
classified as missing local asset, unsupported parameter shape, renderer
dependency issue, or licensing policy issue.
