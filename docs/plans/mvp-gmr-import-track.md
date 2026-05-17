# MVP GMR Import Track Plan

Status: IMPLEMENTED

## Goal

Add a dependency-light import boundary for externally produced GMR Unitree G1
tracks:

```text
external GMR unitree_g1 JSON export
  -> normalized G1 visual-track manifest
  -> optional source motion-record frame/timing validation
  -> existing G1 render/playback/public-demo consumers
```

This closes the local contract gap between the fixture-derived G1 skeleton and
the later real GMR output. It does not run GMR locally.

## Dependencies

- [mvp-g1-visual-track.md](mvp-g1-visual-track.md) defines the G1 non-scoring
  boundary and fixture-derived visual-track shape.
- [mvp-local-motion-contract.md](mvp-local-motion-contract.md) provides the
  optional source SMPL-X motion record used for frame-count and timing checks.
- [mvp-g1-real-model-rendering.md](mvp-g1-real-model-rendering.md) consumes the
  same G1 track manifest for render evidence.

## Inputs

- External JSON using schema `neodojo.gmr_unitree_g1_track.v1`.
- `robot: unitree_g1`.
- Per-frame `visual_joints` for the existing viewer contract.
- Per-frame `joint_angles` for the Unitree G1 pose stream.
- Optional source motion-record manifest for frame-count, timing, coordinate,
  and contact alignment.
- Optional G1 model descriptor for downstream render provenance.

## Outputs

- `tracks/g1/manifest.json` using the existing `neodojo.track.v1` schema.
- `tracks/g1/joints.json` containing visual frames plus imported joint-angle
  frames and joint-angle names.
- `comparison-report.json` proving the imported G1 track remains derived and
  non-scoring.
- CLI command:

  ```bash
  PYTHONPATH=src python -m neodojo tracks import-gmr-json \
    --source path/to/gmr-unitree-g1.json \
    --motion-record outputs/motion-contract \
    --out outputs/g1-visual
  ```

## Execution Tasks

1. Define the accepted external export schema.
   - [x] Require `neodojo.gmr_unitree_g1_track.v1`.
   - [x] Require `robot: unitree_g1`.
   - [x] Require at least 8 frames.
   - [x] Require both displayable `visual_joints` and numeric `joint_angles`.

2. Normalize imported frames.
   - [x] Validate all viewer joints required by the current render/playback
     contract.
   - [x] Validate joint-angle keys are stable across frames.
   - [x] Preserve imported joint-angle names and values in track data.

3. Connect to existing contracts.
   - [x] Write the standard G1 visual-track manifest.
   - [x] Validate frame count against a source motion record when supplied.
   - [x] Preserve motion-record timing, coordinates, and contact metadata when
     supplied.
   - [x] Keep `scoring_allowed: false`.

4. Add command and tests.
   - [x] Add `neodojo tracks import-gmr-json`.
   - [x] Test a valid import.
   - [x] Test missing joint-angle rejection.
   - [x] Keep the fixture `tracks build` command unchanged.

## Acceptance Evidence

- `make test` covers valid GMR JSON import and invalid missing joint-angle
  rejection.
- The imported G1 track manifest is consumable by existing G1 render,
  teaching-playback, and public-demo code.
- The comparison report keeps SMPL-X as the scoring source.
- No GMR native outputs, generated tracks, videos, or large files are committed.

## Non-Goals

- Running GMR locally.
- Parsing every upstream GMR native pickle or NumPy output format.
- Solving MuJoCo/Genesis mesh rendering.
- Using G1 as a teaching-feedback source.
- Running GVHMR or any GPU inference.

## Stop Condition

Stopped when an external normalized GMR Unitree G1 JSON export can enter the
repo through a stable G1 visual-track manifest while preserving the SMPL-X
scoring boundary.
