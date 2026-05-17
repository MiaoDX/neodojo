# MVP Real Conversion Gate Plan

Status: LATER GPU GATE

## Goal

Produce the first real GVHMR SMPL-X artifact for one short local Baduanjin clip
and prove that it imports through the same motion-record contract used by
fixtures.

This gate prevents the project from becoming only a synthetic demo. It is
deliberately scheduled after the local motion, G1 visual-track, and first
playback contracts. It should not block local interface work, but it is required
before calling the MVP an end-to-end neodojo proof.

## Dependencies

- [mvp-local-motion-contract.md](mvp-local-motion-contract.md) has a stable
  import contract.
- [mvp-g1-visual-track.md](mvp-g1-visual-track.md) has a stable G1 model and
  visual-track contract, so real data can flow into the same downstream shape.
- [mvp-teaching-playback-demo.md](mvp-teaching-playback-demo.md) has a local
  fixture playback path that does not depend on GPU output.
- A GPU-capable environment is available through Colab, RunPod, Modal, Hugging
  Face Jobs, or another machine.
- A local/user-supplied source clip is selected with licensing boundaries
  understood.

## Candidate Source

The likely first source is a short local clip from Baduanjin form 1, "Two Hands
Hold Up the Heavens". The source index currently includes:

- Official source index row `03-006`
- Chinese title: `5八段锦两手托天理三焦`
- Suggested local path:
  `video/03_baduanjin/006_two-hands-hold-up-the-heavens.mp4`

Do not commit the MP4 or any generated motion artifacts. A user-supplied local
path is acceptable and preferred.

## Inputs

- Local source clip path, or a trimmed local clip path.
- Frame range or trim metadata.
- GVHMR environment details:
  - upstream commit or package version
  - model/checkpoint source
  - command or notebook used
  - hardware/runtime
- Output artifact directory from GVHMR.
- Exported `neodojo.gvhmr_smplx_joints.v1` JSON containing precomputed SMPL-X
  teaching joints for the selected frame range.

## Outputs

- External GVHMR artifact directory stored outside tracked source files.
- A small provenance manifest in an ignored output/artifact directory.
- A motion-record import run using
  `neodojo motion-record create --from-gvhmr-json`.
- A short report stating whether downstream local contracts needed changes.

## Execution Tasks

- Select the shortest useful Baduanjin clip segment for the proof.
- Record source metadata: title, source URL or local origin, duration, frame
  range, resolution, and license/rights notes.
- Run GVHMR on a GPU-capable environment.
- Export the SMPL-X result directory with enough metadata for reproducibility.
- Convert or export the GVHMR result into
  `neodojo.gvhmr_smplx_joints.v1` JSON with the teaching joints required by the
  local playback contract.
- Import the exported JSON artifact using
  `neodojo motion-record create --from-gvhmr-json`.
- If import fails, classify the failure:
  - contract too narrow
  - missing GVHMR metadata
  - upstream output format difference
  - source video/clip issue
  - environment issue
- Fix only contract issues that are necessary for real GVHMR output.
- Keep all large/generated artifacts out of git.

## Acceptance Evidence

- A real GVHMR output directory exists outside git.
- The provenance manifest records source, command/runtime, and artifact path.
- The exported JSON artifact imports through the same motion-record contract as
  fixtures.
- The imported record reports frame count, fps or timing, joint coverage, and
  SMPL-X provenance.
- No downstream code needs special real-artifact handling beyond the accepted
  contract.
- Docs continue to distinguish real conversion from fixture playback.

## Non-Goals

- Running GVHMR full-video inference on the local macOS CPU machine.
- HAMER hand refinement.
- GMR retargeting.
- Rendering or UI work.
- G1 model registration.
- Full Baduanjin routine processing.
- Publishing or redistributing source videos or generated motion files.

## Stop Condition

Stop when one real GVHMR artifact imports successfully, or when a blocker is
classified with enough detail to decide whether to fix the contract, change the
source clip, or change the GPU environment.
