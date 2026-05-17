# MVP Key-Frame Feedback Detection Plan

Status: IMPLEMENTED FIRST DETECTOR

## Goal

Replace the public-demo lane's implicit last-frame feedback anchor with an
explicit SMPL-X annotation detector:

```text
SMPL-X motion record
  -> deterministic key-frame detection
  -> neodojo.annotation.v1 manifest
  -> teaching playback feedback anchor
  -> public-demo scene annotation metadata
```

The first detector targets the Baduanjin opening-form "raise hands apex" shape.
It is intentionally narrow and SMPL-X-only.

## Dependencies

- [mvp-local-motion-contract.md](mvp-local-motion-contract.md) provides SMPL-X
  joint frames and timing metadata.
- [mvp-pipeline-contract-hardening.md](mvp-pipeline-contract-hardening.md)
  defines the annotation manifest schema.
- [mvp-teaching-playback-demo.md](mvp-teaching-playback-demo.md) consumes
  annotation manifests to choose the feedback key frame.

## Inputs

- Motion-record root or manifest path.
- SMPL-X joint frames containing wrists, elbows, shoulders, and neck.
- Existing SMPL-X geometry feedback checks.

## Outputs

- CLI command:

  ```bash
  PYTHONPATH=src python -m neodojo annotations detect \
    --motion-record outputs/motion-contract \
    --out outputs/annotations
  ```

- `outputs/annotations/manifest.json` using schema `neodojo.annotation.v1`.
- A keyframe named `raise hands apex`.
- SMPL-X-only constraints for shoulders below neck, wrists above elbows, and
  wrist symmetry.
- `make demo-public` wiring that feeds detected annotations into
  `neodojo demo play`.

## Execution Tasks

1. Add a first deterministic detector.
   - [x] Select the frame with highest average wrist height, elbow drop, and
     wrist symmetry.
   - [x] Keep the detector advisory and SMPL-X-only.
   - [x] Reject tracks with too few frames.

2. Emit the existing annotation contract.
   - [x] Write `neodojo.annotation.v1`.
   - [x] Preserve source motion-record provenance.
   - [x] Include selected joints, terms, constraints, and feedback metrics.

3. Connect to playback/public demo.
   - [x] Add `neodojo annotations detect`.
   - [x] Feed detected annotations into `make demo-public`.
   - [x] Keep G1 out of scoring and feedback decisions.

4. Verify.
   - [x] Unit-test key-frame detection.
   - [x] Unit-test detected annotations driving teaching playback.
   - [x] Run the full public-demo smoke command.

## Acceptance Evidence

- `make test` covers detector output and playback consumption.
- `make demo-public` generates `outputs/annotations/manifest.json` and uses it
  when writing `outputs/teaching-demo/manifest.json`.
- Public-demo export carries annotation metadata from playback.
- The detector is clearly scoped as an opening-form heuristic, not full routine
  understanding.

## Non-Goals

- Full-routine key-frame detection.
- LLM term parsing.
- Webcam/user-practice comparison.
- G1-based scoring.
- Replacing human review of qigong correctness.

## Stop Condition

Stopped when the fixture public-demo lane uses an explicit generated annotation
manifest for the first SMPL-X feedback key frame.
