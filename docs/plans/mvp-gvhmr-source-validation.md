# MVP GVHMR Source Validation Plan

Status: PLANNED; BLOCKED ON A REAL GVHMR EXPORT

## Goal

Validate that an imported real GVHMR artifact came from the intended local
source clip and trim window:

```text
source-materialization manifest
  -> GPU GVHMR provenance
  -> neodojo.gvhmr_smplx_joints.v1 export
  -> source/provenance validation report
  -> motion-record import
```

This closes the handoff gap between local media preparation and imported SMPL-X
motion artifacts.

## Dependencies

- [mvp-source-media-materialization.md](mvp-source-media-materialization.md)
  records the trimmed clip path, checksum, frame references, and GVHMR input
  handoff.
- [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) produces the first
  real GVHMR export on a GPU-capable machine.
- [mvp-local-motion-contract.md](mvp-local-motion-contract.md) imports the
  exported SMPL-X teaching-joints JSON.

## Inputs

- `source-materialization.json`.
- GPU-run provenance manifest or GVHMR export provenance block.
- `neodojo.gvhmr_smplx_joints.v1` JSON export.
- Motion-record import output.

## Outputs

- Validation report comparing source id, trim start/end, expected clip path,
  source/trimmed checksums when available, frame count, fps, and duration.
- Clear pass/fail classification before the artifact is treated as the first
  real conversion proof.
- Tests for provenance mismatch and missing-provenance behavior.

## Execution Tasks

1. Define provenance fields.
   - [ ] Require source-materialization manifest path or digest in the GVHMR
     export provenance.
   - [ ] Record GPU command, runtime, upstream version, and input video path.

2. Add validation command.
   - [ ] Compare source id, trim window, expected input path, and checksums.
   - [ ] Compare motion duration against trim duration within tolerance.
   - [ ] Classify missing provenance separately from mismatch.

3. Wire import gate.
   - [ ] Run validation before claiming a real conversion artifact.
   - [ ] Keep import possible for debugging, but label unvalidated artifacts.

## Acceptance Evidence

- A real GVHMR export with matching provenance passes validation.
- Mismatched source/trim/checksum data fails with actionable errors.
- The motion-record manifest preserves source-validation status.
- Docs state whether the real artifact is validated or only imported.

## Non-Goals

- Running GVHMR locally.
- Downloading or committing source video.
- Proving pose accuracy.
- Validating native GVHMR `.pt` files without an export/provenance adapter.

## Stop Condition

Stop when the first real GVHMR export can be tied back to the materialized
source clip, or when missing provenance blocks the claim and the required export
fields are documented.
