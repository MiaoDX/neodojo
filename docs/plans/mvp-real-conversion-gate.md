# MVP Real Conversion Gate Plan

Status: LOCAL PREP READY; LATER GPU GATE

## Goal

Produce the first real GVHMR SMPL-X artifact for one short local Baduanjin clip
and prove that it imports through the same motion-record contract used by
fixtures.

This gate prevents the project from becoming only a synthetic demo. It is
deliberately scheduled after the local motion, G1 visual-track, first playback,
and real G1 model-rendering proof. It should not block local interface work,
but it is required before calling the MVP an end-to-end neodojo proof.

## Dependencies

- [mvp-local-motion-contract.md](mvp-local-motion-contract.md) has a stable
  import contract.
- [mvp-g1-visual-track.md](mvp-g1-visual-track.md) has a stable G1 model and
  visual-track contract, so real data can flow into the same downstream shape.
- [mvp-teaching-playback-demo.md](mvp-teaching-playback-demo.md) has a local
  fixture playback path that does not depend on GPU output.
- [mvp-g1-real-model-rendering.md](mvp-g1-real-model-rendering.md) is the
  preferred next local slice before this GPU gate, so the right-side G1 view can
  become a real model render independently from source-video conversion.
- [mvp-pipeline-contract-hardening.md](mvp-pipeline-contract-hardening.md) is
  expected to stabilize the import, source-prep, normalization, annotation,
  render, playback, and public-demo manifest boundaries before this real
  artifact enters them.
- [mvp-visualization-and-public-demo.md](mvp-visualization-and-public-demo.md)
  and [mvp-devex-ci-surface.md](mvp-devex-ci-surface.md) are not required to run
  GVHMR, but they should provide the fixture public-demo lane that the imported
  real artifact can replace later.
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
- A local prep manifest from `neodojo real-conversion prepare` or its hardened
  successor that records source metadata, trim metadata, checksums,
  provenance/rights notes, and next commands before the GPU run.
- A motion-record import run using
  `neodojo motion-record create --from-gvhmr-json`.
- A short report stating whether downstream local contracts needed changes.

## Implemented Local Prep

The local prep command is:

```bash
PYTHONPATH=src python -m neodojo real-conversion prepare --id 03-006 --start 0 --end 12 --out outputs/real-conversion-gate
```

It writes `outputs/real-conversion-gate/real-conversion-prep.json` with:

- source index row `03-006`
- Chinese title `5八段锦两手托天理三焦`
- English title `Two Hands Hold Up the Heavens`
- official article URL and source MP4 URL from the local source index
- recommended local path
- 0-12 second proof trim
- rights notes
- expected GVHMR output/export paths
- downstream import, G1-track, and playback commands

This command does not download video, run GVHMR, or prove qigong correctness.

## Execution Tasks

- [x] Select an initial Baduanjin source row and bounded 0-12 second proof trim
  candidate.
- [x] Record source metadata: title, source URL or local origin, duration, trim
  window, resolution, and license/rights notes.
- [ ] Run GVHMR on a GPU-capable environment.
- [ ] Export the SMPL-X result directory with enough metadata for reproducibility.
- [ ] Convert or export the GVHMR result into
  `neodojo.gvhmr_smplx_joints.v1` JSON with the teaching joints required by the
  local playback contract.
- [ ] Import the exported JSON artifact using
  `neodojo motion-record create --from-gvhmr-json`.
- [ ] If import fails, classify the failure:
  - contract too narrow
  - missing GVHMR metadata
  - upstream output format difference
  - source video/clip issue
  - environment issue
- [ ] Fix only contract issues that are necessary for real GVHMR output.
- [x] Keep all large/generated artifacts out of git.

## Acceptance Evidence

- A real GVHMR output directory exists outside git.
- The provenance manifest records source, command/runtime, and artifact path.
- The exported JSON artifact imports through the same motion-record contract as
  fixtures.
- The imported record reports frame count, fps or timing, joint coverage, and
  SMPL-X provenance.
- The artifact includes enough coordinate, floor/facing, source-media, and
  annotation metadata to enter the hardened playback/public-demo lane without a
  special real-artifact path.
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
