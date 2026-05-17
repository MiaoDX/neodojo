# MVP G1 Visual Track Plan

Status: QUEUED AFTER LOCAL MOTION CONTRACT

## Goal

Add the Unitree G1 visual-track boundary as a derived companion to SMPL-X:

```text
SMPL-X motion record
  -> Unitree G1 model/asset descriptor
  -> G1-like fixture track or GMR-derived G1 track
  -> G1 visual-track manifest
  -> comparison report proving scoring stays on SMPL-X
```

This plan owns G1 model provenance and G1 track semantics together. That keeps
the robot work coherent without pulling in GPU video conversion.

## Dependencies

- [mvp-local-motion-contract.md](mvp-local-motion-contract.md) completed or
  stable enough to provide an SMPL-X motion-record manifest.
- No GVHMR GPU output required.
- Local GMR is optional; an imported GMR output path or fixture-derived G1-like
  track is acceptable for the first local proof.

## Inputs

- SMPL-X motion-record manifest.
- Local path to a Unitree G1 URDF or MJCF model file, when using real assets.
- Local paths to referenced mesh assets, when needed.
- Source URL, upstream repository, commit/tag, license, and model variant notes.
- Optional local GMR installation path and command configuration.
- Optional imported GMR `unitree_g1` output.

## Outputs

- G1 model/asset descriptor with provenance and validation result.
- G1 visual-track manifest.
- Fixture-derived G1-like track mode for local smoke tests.
- Optional imported or locally generated GMR `unitree_g1` track support.
- A comparison report with frame count, fps, joint coverage, dropped frames,
  provenance, and known loss points such as torso and hand DOF.
- Tests for G1 model descriptor validation, track manifest creation, and
  scoring-boundary enforcement.

## Implementation Tasks

- Add a command boundary for robot assets, for example:

  ```bash
  neodojo robot-model register --robot unitree_g1 --model <path> --out <asset-dir>
  ```

- Add a command boundary for visual tracks, for example:

  ```bash
  neodojo tracks build --motion-record <motion-dir> --robot unitree_g1 --out <tracks-dir>
  ```

- Define the G1 model descriptor:
  - `robot`
  - `model_format`
  - `model_path`
  - `mesh_roots`
  - `source_url`
  - `source_revision`
  - `license`
  - `variant`
  - `joint_count`
  - `provenance`
  - `validation`
- Validate that model and mesh paths are local and not accidentally copied into
  tracked source directories.
- Parse enough of the model to list joints, root link/body, and missing asset
  references.
- Keep the initial validator dependency-light. Add MuJoCo or another parser
  only if needed for reliable local load evidence.
- Implement fixture-derived G1-like track generation before requiring GMR.
- Implement a GMR adapter for `unitree_g1`, with import fallback if local GMR
  dependencies are not stable on macOS.
- Validate frame count and timing alignment between SMPL-X and G1 tracks.
- Validate that G1 tracks always have `scoring_allowed: false`.
- Add diagnostics for torso DOF mismatch, hand/gripper simplification,
  foot/contact drift, and dropped/interpolated frames.

## Acceptance Evidence

- A focused test command passes for G1 model/track validation.
- A local G1 asset descriptor can be generated from user-supplied model paths or
  a fixture descriptor.
- Missing mesh/model paths produce clear validation errors.
- A fixture or dry-run can build a G1 visual-track manifest from one SMPL-X
  motion record.
- The G1 track is marked as derived and rejected as a scoring source.
- The comparison report explicitly shows SMPL-X as canonical and G1 as derived.
- No Unitree assets, generated tracks, or large model files are committed by
  default.

## Non-Goals

- Running GVHMR or any GPU workload.
- Using G1 as the teaching scoring source.
- Browser UI.
- Multi-camera rendered videos.
- HAMER hand refinement.
- Sim2real control or physical robot execution.

## Stop Condition

Stop when G1 assets/tracks can be referenced through stable manifests and the
repo can prove that G1 remains a derived visual artifact.
