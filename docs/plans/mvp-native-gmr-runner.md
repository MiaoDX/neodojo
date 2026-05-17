# MVP Native GMR Runner Plan

Status: IMPLEMENTED FIRST PICKLE ADAPTER; LOCAL GMR EXECUTION REMAINS EXTERNAL

## Goal

Move beyond the normalized imported-GMR JSON boundary by supporting native GMR
execution or native output parsing:

```text
SMPL-X motion record
  -> GMR execution or native GMR output parser
  -> normalized neodojo.gmr_unitree_g1_track.v1 JSON
  -> non-scoring G1 visual-track manifest
```

The normalized JSON import remains the stable downstream contract. Native GMR
support is an adapter into that contract, not a new scoring path. The first
implemented slice supports the YanjieZe/GMR robot-motion pickle shape written by
upstream `scripts/*_to_robot.py --save_path`, which contains `fps`, `root_pos`,
`root_rot`, and `dof_pos`.

## Dependencies

- [mvp-gmr-import-track.md](mvp-gmr-import-track.md) defines the normalized GMR
  JSON boundary.
- [mvp-local-motion-contract.md](mvp-local-motion-contract.md) provides SMPL-X
  motion input.
- Upstream GMR repository, model files, and real output artifacts stay outside
  tracked source. Tests use tiny synthetic pickle fixtures with the same field
  names as the upstream saved artifact.

## Inputs

- Motion-record manifest.
- Upstream GMR environment instructions and version/commit.
- Native GMR robot-motion pickle with `fps`, `root_pos`, `root_rot`, and
  `dof_pos`.
- Unitree G1 model metadata required by GMR.

## Outputs

- Adapter command that writes `neodojo.gmr_unitree_g1_track.v1`:

  ```bash
  PYTHONPATH=src python -m neodojo tracks normalize-gmr-pkl \
    --source path/to/gmr-motion.pkl \
    --motion-record outputs/motion-contract \
    --out outputs/gmr-native
  ```

- Provenance fields for upstream GMR version, command, model, and source
  motion.
- Tests using tiny synthetic/native-shaped fixtures, not large upstream
  artifacts.
- Documentation that keeps GMR output non-scoring.

## Execution Tasks

1. Inspect upstream output.
   - [x] Use the upstream saved robot-motion pickle schema: `fps`, `root_pos`,
     `root_rot`, `dof_pos`, plus optional joint-name fields.
   - [x] Decide first support is parsing, not local GMR execution.

2. Add adapter.
   - [x] Normalize native `dof_pos` joint angles into the existing GMR JSON
     schema.
   - [x] Preserve stable Unitree G1 29-DOF joint-angle keys, with CLI override
     for other layouts.
   - [x] Validate frame count against the source motion record and record fps
     match diagnostics.
   - [x] Record provenance and warnings explaining that current display joints
     are derived from the source SMPL-X motion record while native G1 joint
     angles are preserved.

3. Verify.
   - [x] Unit-test parser behavior with a tiny pickle fixture.
   - [x] Smoke-test import through `tracks import-gmr-json`.
   - [x] Confirm playback/render/public-demo consumers need no special path
     because the adapter emits the existing normalized JSON contract.

## Acceptance Evidence

- A native GMR pickle output can produce the normalized GMR JSON artifact.
- The normalized artifact imports through the existing non-scoring G1 track
  command.
- Tests cover malformed native output and timing mismatch failures.
- Docs continue to state that G1 is visual-only.

## Non-Goals

- Making G1 the scoring source.
- Training policies or sim2real controllers.
- Bundling upstream model checkpoints.
- Supporting every GMR native output variant in the first slice.
- Running the upstream GMR environment locally.

## Stop Condition

Stopped when one native GMR adapter path produced a normalized importable G1
track from a pickle-shaped robot-motion artifact. Local upstream GMR execution,
NumPy `.npz` variants, and project-specific JSON variants remain future
extensions, but they are no longer blockers for the first non-GPU adapter lane.
