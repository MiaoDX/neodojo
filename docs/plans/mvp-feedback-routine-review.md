# MVP Feedback Routine Review Plan

Status: IMPLEMENTED

## Goal

Move from one opening-form detector to a small SMPL-X-based feedback review:

```text
SMPL-X teaching track
  -> multiple key-frame detectors
  -> posture-term checks
  -> annotation manifest
  -> routine-level feedback report
```

All feedback must remain tied to SMPL-X geometry. G1 visual tracks must not
become the scoring source.

## Dependencies

- [mvp-keyframe-feedback-detection.md](mvp-keyframe-feedback-detection.md)
  provides the first deterministic annotation detector.
- [mvp-pipeline-contract-hardening.md](mvp-pipeline-contract-hardening.md)
  provides annotation manifest versioning.
- A small set of Baduanjin posture terms and measurable geometry definitions is
  chosen.

## Inputs

- SMPL-X motion-record or teaching-track manifest.
- Existing annotation detector output.
- Posture-term definitions such as shoulder sink, elbow drop, wrist symmetry,
  stance stability, and vertical reach.
- Optional manual key-frame anchors for comparison.

## Outputs

- Expanded `neodojo.annotation.v1` or successor manifest with multiple
  key-frame annotations.
- Routine-level feedback report with pass/warn/fail terms and numeric evidence.
- Playback/public-demo labels for feedback anchors.
- Focused tests for detector stability and scoring-source boundaries.

## Execution Tasks

1. Define feedback terms.
   - [x] Pick the first three to five measurable terms.
   - [x] Document required joints and expected geometry.

2. Add detectors.
   - [x] Detect opening stance, settled support, apex, and any stable anchors
     available in the fixture and real-import contracts.
   - [x] Emit term-level evidence and confidence.

3. Add report/playback integration.
   - [x] Write a routine feedback report next to annotations.
   - [x] Surface anchors in teaching playback and public-demo scene metadata.

## Acceptance Evidence

- More than one key-frame or posture term is emitted for the opening-form
  fixture track.
- Tests prove feedback uses SMPL-X data only.
- Playback/public-demo artifacts expose the feedback anchors without claiming
  real qigong correctness for fixture data.
- `make demo-public` writes `outputs/annotations/routine-feedback.json` and the
  public-demo HTML/SVG scene labels include routine feedback anchors.

## Non-Goals

- Medical or clinical claims.
- LLM-generated coaching without geometric evidence.
- G1-based scoring.
- Full Baduanjin routine evaluation.

## Stop Condition

Stopped when a small deterministic routine review exists for the opening-form
fixture/import path and all feedback evidence remains traceable to SMPL-X.
