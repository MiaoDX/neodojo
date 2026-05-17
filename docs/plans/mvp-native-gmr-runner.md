# MVP Native GMR Runner Plan

Status: PLANNED; BLOCKED ON UPSTREAM GMR ENVIRONMENT AND SAMPLE OUTPUTS

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
support is an adapter into that contract, not a new scoring path.

## Dependencies

- [mvp-gmr-import-track.md](mvp-gmr-import-track.md) defines the normalized GMR
  JSON boundary.
- [mvp-local-motion-contract.md](mvp-local-motion-contract.md) provides SMPL-X
  motion input.
- Upstream GMR repository, model files, and at least one representative native
  output artifact are available outside tracked source.

## Inputs

- Motion-record manifest.
- Upstream GMR environment instructions and version/commit.
- Native GMR output samples such as pickle, NumPy, or project-specific JSON.
- Unitree G1 model metadata required by GMR.

## Outputs

- Adapter command or parser command that writes
  `neodojo.gmr_unitree_g1_track.v1`.
- Provenance fields for upstream GMR version, command, model, and source
  motion.
- Tests using tiny synthetic/native-shaped fixtures, not large upstream
  artifacts.
- Documentation that keeps GMR output non-scoring.

## Execution Tasks

1. Inspect upstream output.
   - [ ] Collect one small sample or schema description outside git.
   - [ ] Decide whether first support is execution, parsing, or both.

2. Add adapter.
   - [ ] Normalize native joint angles into the existing GMR JSON schema.
   - [ ] Preserve stable joint-angle keys and timing checks.
   - [ ] Record provenance and unsupported-field diagnostics.

3. Verify.
   - [ ] Unit-test parser behavior with a tiny fixture.
   - [ ] Smoke-test import through `tracks import-gmr-json`.
   - [ ] Confirm playback/render/public-demo consumers need no special path.

## Acceptance Evidence

- A native GMR output or execution path can produce the normalized GMR JSON
  artifact.
- The normalized artifact imports through the existing non-scoring G1 track
  command.
- Tests cover malformed native output and timing mismatch failures.
- Docs continue to state that G1 is visual-only.

## Non-Goals

- Making G1 the scoring source.
- Training policies or sim2real controllers.
- Bundling upstream model checkpoints.
- Supporting every GMR native output variant in the first slice.

## Stop Condition

Stop when one native GMR adapter path produces a normalized importable G1 track,
or when upstream environment/output blockers are documented precisely enough to
choose the next adapter strategy.
