# MVP Real Conversion Gate Plan

Status: LOCAL PREP, SOURCE MATERIALIZATION, GPU HANDOFF, VALIDATION, AND IMPORT-DEMO READY; LATER GPU GATE

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
- [mvp-source-media-probing.md](mvp-source-media-probing.md) records optional
  local video ffprobe metadata before the GPU run.
- [mvp-source-media-materialization.md](mvp-source-media-materialization.md)
  prepares a dry-run or ffmpeg-backed trimmed clip/reference-frame bundle for
  the GPU run without committing media.
- [mvp-gvhmr-source-validation.md](mvp-gvhmr-source-validation.md) validates
  the returned GVHMR JSON export against the materialized source clip before
  the artifact is imported as a real proof.
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

- Local source clip path, or a trimmed local clip path from
  `neodojo real-conversion materialize-source`.
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
- A source materialization manifest from
  `neodojo real-conversion materialize-source` that records the local validated
  source, trim command, optional generated clip/frames, and GVHMR input handoff.
- A GPU handoff package from `neodojo real-conversion package-gpu-handoff` or
  `make gpu-handoff` that records source-materialization hash, trimmed-video
  readiness, expected export schema, provenance fields, and the local return
  command without copying media.
- A motion-record import run using
  `neodojo motion-record create --from-gvhmr-json`.
- A one-command local import/demo run using
  `neodojo real-conversion import-demo` or `make demo-real` after a GPU export is
  available.
- Optional `neodojo.smplx_parameters.v1` data under the motion record when the
  GVHMR export includes mesh-ready SMPL-X pose/shape parameters.
- A short report stating whether downstream local contracts needed changes.

## Implemented Local Prep And Source Handoff

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
- optional local file checksum and ffprobe media probe metadata when
  `--local-video` is supplied
- expected GVHMR output/export paths
- downstream import, G1-track, and playback commands

The local source handoff command is:

```bash
PYTHONPATH=src python -m neodojo real-conversion materialize-source --prep outputs/real-conversion-gate/real-conversion-prep.json --local-video path/to/local-source.mp4 --dry-run --out outputs/real-conversion-source
```

Without `--dry-run`, the same command requires ffmpeg and writes an ignored
trimmed clip plus reference frames under `outputs/real-conversion-source/`.
Package the materialized source metadata for the external GPU operator:

```bash
PYTHONPATH=src python -m neodojo real-conversion package-gpu-handoff \
  --source-materialization outputs/real-conversion-source/source-materialization.json \
  --out outputs/gvhmr-gpu-handoff

make gpu-handoff \
  SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json
```

This writes `outputs/gvhmr-gpu-handoff/manifest.json`, a README, and
`gvhmr-smplx-joints.template.json`. It reports `ready_for_gpu` only when the
source-materialization manifest points to an existing materialized trimmed clip
with matching checksum; dry-run handoffs correctly report `needs_materialization`.
After the GPU run returns a `neodojo.gvhmr_smplx_joints.v1` export with
matching provenance, validate it locally:

```bash
PYTHONPATH=src python -m neodojo real-conversion validate-source --source-materialization outputs/real-conversion-source/source-materialization.json --gvhmr-json outputs/real-conversion-gate/gvhmr-smplx-joints.json --out outputs/real-conversion-validation
```

Or validate, import, and regenerate the local demo artifacts in one command:

```bash
PYTHONPATH=src python -m neodojo real-conversion import-demo \
  --source-materialization outputs/real-conversion-source/source-materialization.json \
  --gvhmr-json outputs/real-conversion-gate/gvhmr-smplx-joints.json \
  --out outputs/real-demo

make demo-real \
  SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json \
  GVHMR_JSON=outputs/real-conversion-gate/gvhmr-smplx-joints.json
```

These commands avoid downloading video, running GVHMR locally, or proving
qigong correctness. By default, `import-demo` derives a fixture G1 visual
companion from the imported SMPL-X motion record; pass `--g1-track` and
`--model-descriptor`, or the matching `G1_TRACK=... MODEL_DESCRIPTOR=...` make
variables, when an external GMR/G1 visual artifact is available.

## Execution Tasks

- [x] Select an initial Baduanjin source row and bounded 0-12 second proof trim
  candidate.
- [x] Record source metadata: title, source URL or local origin, duration, trim
  window, resolution, and license/rights notes.
- [x] Record optional local source-video checksum and ffprobe metadata when a
  local file is supplied.
- [x] Materialize, or dry-run materialize, the trimmed local source clip and
  reference-frame handoff for the GPU run.
- [x] Package a source-materialization manifest into a GPU handoff bundle with
  export template, provenance fields, readiness status, and local return
  command.
- [x] Validate a returned GVHMR export against the source-materialization
  manifest before importing the validated JSON copy.
- [x] Add a local `real-conversion import-demo` / `make demo-real` wrapper that
  validates the external export, imports it, and regenerates the demo/capture
  lane after the GPU artifact exists.
- [ ] Run GVHMR on a GPU-capable environment.
- [ ] Export the SMPL-X result directory with enough metadata for reproducibility.
- [ ] Convert or export the GVHMR result into
  `neodojo.gvhmr_smplx_joints.v1` JSON with the teaching joints required by the
  local playback contract.
- [ ] Import the exported JSON artifact using
  `neodojo motion-record create --from-gvhmr-json`.
- [ ] Run `neodojo real-conversion import-demo` or `make demo-real` on the real
  exported artifact and inspect `outputs/real-demo/`.
- [ ] If import fails, classify the failure:
  - contract too narrow
  - missing GVHMR metadata
  - upstream output format difference
  - source video/clip issue
  - environment issue
- [ ] Fix only contract issues that are necessary for real GVHMR output.
- [x] Keep all large/generated artifacts out of git.

## Current Blocker Classification

The local, non-GPU side of this gate is complete through prep,
source-materialization, GPU handoff packaging, returned-export validation,
motion import, and `import-demo`/`make demo-real` demo regeneration. The
remaining blocker is external to this macOS CPU workspace:

- blocker type: source clip plus GPU artifact missing
- missing input: a licensed or user-supplied local clip for source `03-006`, or
  an explicitly selected replacement clip with rights understood
- missing runtime: a GPU-capable GVHMR environment such as Colab, RunPod,
  Modal, Hugging Face Jobs, or another CUDA machine
- missing artifact: a `neodojo.gvhmr_smplx_joints.v1` JSON export with
  provenance matching `source-materialization.json`
- not currently implicated: local schema, validation, import, playback,
  public-demo, Viser preview, or capture-bundle contracts

When the external artifact exists, the next command is:

```bash
make demo-real \
  SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json \
  GVHMR_JSON=outputs/real-conversion-gate/gvhmr-smplx-joints.json
```

## Acceptance Evidence

- A real GVHMR output directory exists outside git.
- The provenance manifest records source, command/runtime, and artifact path.
- The exported JSON artifact imports through the same motion-record contract as
  fixtures.
- The one-command import-demo wrapper writes `outputs/real-demo/manifest.json`,
  public-demo artifacts, Viser preview evidence, and a capture bundle.
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

Stop when one real GVHMR artifact imports successfully and the import-demo lane
regenerates the local public-demo/capture artifacts, or when a blocker is
classified with enough detail to decide whether to fix the contract, change the
source clip, or change the GPU environment.
