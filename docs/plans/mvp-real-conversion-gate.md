# MVP Real Conversion Gate Plan

Status: LOCAL PREP, SOURCE MATERIALIZATION, GPU HANDOFF, GPU INPUT BUNDLE, GPU RUNNER, TRANSFER ARCHIVE, GPU EXECUTION PROBE, EXPORT HELPER, RESULT INSPECTION, VALIDATION, AND IMPORT-DEMO READY; LATER GPU GATE

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
- [mvp-gvhmr-export-adapter.md](mvp-gvhmr-export-adapter.md) packages a
  GPU-side helper script for converting GVHMR `hmr4d_results.pt` plus licensed
  local SMPL-X assets into the neodojo JSON import schema.
- [mvp-gvhmr-gpu-runner-surface.md](mvp-gvhmr-gpu-runner-surface.md) packages
  a CI-safe `run_gvhmr_neodojo.sh` script so the GPU operator has one
  executable wrapper around upstream GVHMR and the neodojo exporter.
- [mvp-gvhmr-gpu-transfer-archive.md](mvp-gvhmr-gpu-transfer-archive.md)
  packages the ignored GPU input bundle as a single `.tar.gz` transfer file.
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
  readiness, expected export schema, provenance fields, a GPU-side exporter
  helper script, an executable GPU runner, and the local return command without
  copying media.
- An optional GPU input transfer archive from
  `neodojo real-conversion archive-gpu-input` or `make gpu-input-archive` for
  upload to the selected GPU environment.
- A result inspection manifest from `neodojo real-conversion
  inspect-gvhmr-result` or `make gvhmr-inspect` that reports top-level
  `hmr4d_results.pt` keys and candidate SMPL-X parameter blocks when run in a
  GVHMR/GPU environment with `torch`, or inspects JSON summaries/exports in the
  default local environment.
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

For an official source-index row, it writes
`outputs/real-conversion-gate/real-conversion-prep.json` with:

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

For a local/user-supplied source that should not be attached to an official
source-index row, use custom local-source provenance:

```bash
PYTHONPATH=src python -m neodojo real-conversion prepare \
  --local-source-id local-baduanjin \
  --local-video path/to/local-source.mp4 \
  --local-title "Local Baduanjin proof clip" \
  --start 0 \
  --end 12 \
  --out outputs/real-conversion-gate
```

`make real-handoff` accepts the same route through `REAL_LOCAL_SOURCE_ID=...`
and optional `REAL_LOCAL_TITLE=...`.

The local source handoff command is:

```bash
PYTHONPATH=src python -m neodojo real-conversion materialize-source --prep outputs/real-conversion-gate/real-conversion-prep.json --local-video path/to/local-source.mp4 --dry-run --out outputs/real-conversion-source

make real-handoff \
  LOCAL_VIDEO=path/to/local-source.mp4
```

Without `--dry-run`, the same command requires ffmpeg and writes an ignored
trimmed clip plus reference frames under `outputs/real-conversion-source/`.
`make real-handoff` wraps source prep, dry-run materialization by default, and
GPU handoff packaging; set `REAL_DRY_RUN=0` to actually trim/extract media when
ffmpeg is installed. `make real-handoff-smoke` exercises the same default
dry-run handoff path with an ignored placeholder `.mp4` and runs inside
`make verify`. CI uploads the resulting metadata-only handoff bundle as
`neodojo-real-handoff-smoke` without uploading the placeholder source media;
GitHub Actions run `26003369563` verified that artifact contains the expected
prep/source/handoff metadata and no video files.
A local Bilibili Baduanjin candidate was also materialized with
`REAL_LOCAL_SOURCE_ID=bilibili-baduanjin-480p` and `REAL_DRY_RUN=0` under
`outputs/real-handoff-local-bilibili/`; that handoff reports `ready_for_gpu`
and keeps rights marked unconfirmed.

For the external GPU operator archive, use the one-command local packaging
target:

```bash
make real-gpu-archive \
  LOCAL_VIDEO=path/to/local-source.mp4 \
  REAL_LOCAL_SOURCE_ID=local-baduanjin
```

This target forces non-dry-run source materialization, creates the
media-including GPU input bundle, and writes the transfer archive without
running GVHMR locally.

Package the materialized source metadata for the external GPU operator:

```bash
PYTHONPATH=src python -m neodojo real-conversion package-gpu-handoff \
  --source-materialization outputs/real-conversion-source/source-materialization.json \
  --out outputs/gvhmr-gpu-handoff

make gpu-handoff \
  SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json
```

This writes `outputs/gvhmr-gpu-handoff/manifest.json`, a README,
`source-materialization.json`, `gvhmr-smplx-joints.template.json`,
`export_neodojo_gvhmr.py`, and `run_gvhmr_neodojo.sh`. It reports
`ready_for_gpu` only when the source-materialization manifest points to an
existing materialized trimmed clip with matching checksum; dry-run handoffs
correctly report `needs_materialization`.
Package a copyable GPU input directory when the materialized clip should travel
with the handoff:

```bash
PYTHONPATH=src python -m neodojo real-conversion package-gpu-input \
  --gpu-handoff outputs/gvhmr-gpu-handoff \
  --include-media \
  --out outputs/gvhmr-gpu-input

make gpu-input-bundle \
  GPU_HANDOFF=outputs/gvhmr-gpu-handoff \
  GPU_INPUT_INCLUDE_MEDIA=1
```

This writes `RUN_ON_GPU.md`, handoff metadata, the export template,
`export_neodojo_gvhmr.py`, `run_gvhmr_neodojo.sh`, and
`source/trimmed-clip.mp4` under ignored output. It is a transfer bundle only;
do not commit or publish it. The runner can be invoked on the GPU machine as:

```bash
SMPLX_MODEL_DIR=<path-to-licensed-smplx-model-dir> ./run_gvhmr_neodojo.sh --install
```

Set `GVHMR_REPO=/path/to/GVHMR` and omit `--install` when the GPU environment
already has GVHMR installed.
Package that directory as one transfer archive when needed:

```bash
PYTHONPATH=src python -m neodojo real-conversion archive-gpu-input \
  --gpu-input outputs/gvhmr-gpu-input \
  --out outputs/gvhmr-gpu-input-archive

make gpu-input-archive \
  GPU_INPUT=outputs/gvhmr-gpu-input
```

This writes `neodojo-gvhmr-gpu-input.tar.gz` and a
`neodojo.gvhmr_gpu_input_archive.v1` manifest under ignored output. Metadata-only
archives are CI-safe; media-containing archives must not be committed or
published.
After GVHMR writes `hmr4d_results.pt` on the GPU machine, the packaged exporter
can be run there with a licensed local SMPL-X model directory to write the
expected `neodojo.gvhmr_smplx_joints.v1` JSON. The exporter remains a GPU-side
handoff helper; it is not exercised by default on the local CPU workspace. Its
command uses bundle-local filenames so the handoff directory can be copied to a
GPU machine without rewriting paths.
Inspect the returned GVHMR result structure before writing the final neodojo
export:

```bash
PYTHONPATH=src python -m neodojo real-conversion probe-gpu-execution \
  --out outputs/gvhmr-gpu-execution-probe

make gpu-execution-probe

PYTHONPATH=src python -m neodojo real-conversion inspect-gvhmr-result \
  --source outputs/real-conversion-gate/hmr4d_results.pt \
  --out outputs/gvhmr-result-inspection

make gvhmr-inspect \
  GVHMR_RESULT=outputs/real-conversion-gate/hmr4d_results.pt
```

The GPU execution probe writes a safe readiness manifest with local CUDA,
Docker GPU runtime, provider CLI, and provider environment-variable-name
evidence only; it does not record secret values or run GVHMR. Native `.pt`
inspection requires `torch` and should normally run in the GVHMR/GPU
environment. The command can inspect JSON summaries or existing
`neodojo.gvhmr_smplx_joints.v1` exports in the default local environment. It
does not convert raw `.pt` results locally.
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

make real-artifact-intake \
  REAL_ARTIFACT_GVHMR_JSON=outputs/real-conversion-gate/gvhmr-smplx-joints.json
```

These commands avoid downloading video, running GVHMR locally, or proving
qigong correctness. By default, `import-demo` derives a fixture G1 visual
companion from the imported SMPL-X motion record; pass `--g1-track` and
`--model-descriptor`, or the matching `G1_TRACK=... MODEL_DESCRIPTOR=...` make
variables, when an external GMR/G1 visual artifact is available.
`make real-artifact-intake` is the shorter wrapper for the standard returned
artifact path; it defaults to
`outputs/real-conversion-source/source-materialization.json` and
`outputs/real-demo`.

## Execution Tasks

- [x] Select an initial Baduanjin source row and bounded 0-12 second proof trim
  candidate.
- [x] Record source metadata: title, source URL or local origin, duration, trim
  window, resolution, and license/rights notes.
- [x] Record optional local source-video checksum and ffprobe metadata when a
  local file is supplied.
- [x] Support custom local/user-supplied source provenance with
  `--local-source-id` so local clips are not misidentified as official
  source-index rows.
- [x] Materialize, or dry-run materialize, the trimmed local source clip and
  reference-frame handoff for the GPU run.
- [x] Package a source-materialization manifest into a GPU handoff bundle with
  export template, provenance fields, readiness status, and local return
  command.
- [x] Package an ignored copyable GPU input bundle with explicit media inclusion
  for transfer to the selected GPU machine.
- [x] Package an executable `run_gvhmr_neodojo.sh` GPU-side runner in the
  handoff and input bundles, and smoke-check it without running GVHMR.
- [x] Package the GPU input bundle into a `.tar.gz` transfer archive and
  metadata manifest, with CI-safe metadata-only smoke coverage.
- [x] Add `make real-handoff LOCAL_VIDEO=...` to run local prep,
  materialization, and GPU handoff packaging as one command without running
  GVHMR locally.
- [x] Include a dependency-light `make real-handoff-smoke` target in
  `make verify` and the GitHub Actions workflow so CI exercises the handoff
  command surface without real media.
- [x] Upload the CI real-handoff smoke metadata bundle without including the
  placeholder source media.
- [x] Add a GPU-side exporter helper to the handoff bundle for turning
  `hmr4d_results.pt` plus licensed SMPL-X assets into
  `neodojo.gvhmr_smplx_joints.v1`.
- [x] Add a GVHMR result inspection command for returned `hmr4d_results.pt` or
  JSON summaries so the export adapter can identify candidate SMPL-X parameter
  blocks before writing `neodojo.gvhmr_smplx_joints.v1`.
- [x] Validate a returned GVHMR export against the source-materialization
  manifest before importing the validated JSON copy.
- [x] Add a local `real-conversion import-demo` / `make demo-real` wrapper that
  validates the external export, imports it, and regenerates the demo/capture
  lane after the GPU artifact exists.
- [x] Add a shorter `make real-artifact-intake` wrapper for the standard
  returned artifact path.
- [x] Add fixture-backed `make real-artifact-intake-smoke` coverage for the
  returned-artifact wrapper without claiming a real GPU result.
- [x] Add a safe `real-conversion probe-gpu-execution` / `make
  gpu-execution-probe` command that records local CUDA/provider readiness
  without running GVHMR or exposing secret values.
- [x] Add `real-conversion audit-completion` / `make real-conversion-audit`
  so local and CI runs write a non-failing blocker classification manifest for
  this gate.
- [ ] Run GVHMR on a GPU-capable environment.
- [ ] Export the SMPL-X result directory with enough metadata for reproducibility.
- [ ] Convert or export the GVHMR result into
  `neodojo.gvhmr_smplx_joints.v1` JSON with the teaching joints required by the
  local playback contract.
- [ ] Import the exported JSON artifact using
  `neodojo motion-record create --from-gvhmr-json`.
- [ ] Run `neodojo real-conversion import-demo`, `make demo-real`, or
  `make real-artifact-intake` on the real exported artifact and inspect
  `outputs/real-demo/`.
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
source-materialization, GPU handoff packaging, GPU runner packaging, transfer
archive packaging, GPU execution readiness probing, returned-result inspection,
GPU-side export-helper packaging, returned-export validation, motion import,
and `import-demo`/`make demo-real` demo regeneration.
A local ignored Bilibili Baduanjin source candidate has been materialized as a
replacement-source GPU input handoff, but rights remain unconfirmed and no real
GVHMR export has been returned. The remaining blocker is external to this macOS
CPU workspace:

- blocker type: GPU artifact missing
- input status: custom local source handoff candidate exists under ignored
  `outputs/real-handoff-local-bilibili/`, and a media-including transfer bundle
  exists under ignored `outputs/gvhmr-gpu-input-local-bilibili/` with
  `run_gvhmr_neodojo.sh`; a media-including ignored transfer archive exists at
  `outputs/gvhmr-gpu-input-archive-local-bilibili/neodojo-gvhmr-gpu-input.tar.gz`
  with manifest status `archive_with_media`, `media_included: true`, and
  `safe_for_git: false`; official source `03-006` is still an available
  source-index path if rights/source selection change
- missing runtime: a GPU-capable GVHMR environment such as Colab, RunPod,
  Modal, Hugging Face Jobs, or another CUDA machine
- missing artifact: a `neodojo.gvhmr_smplx_joints.v1` JSON export with
  provenance matching `source-materialization.json`
- not currently implicated: local schema, validation, import, playback,
  public-demo, Viser preview, or capture-bundle contracts

Latest local execution probe, now reproducible with `make gpu-execution-probe`:

- no `nvidia-smi` or CUDA runtime is visible on this macOS ARM workspace
- no Modal, RunPod, Hugging Face, AWS, GCP, Replicate, or similar provider
  credentials are exposed through the local environment
- no matching provider CLI is installed, except Docker, which does not expose a
  GPU runtime here
- GitHub repository configuration exposes only the Pages deploy variable and no
  repository secrets for a GPU job

That probe keeps the blocker classified as external artifact acquisition rather
than an unimplemented local command or contract gap.

The broader real-conversion completion audit is now executable with
`make real-conversion-audit`. It writes
`outputs/real-conversion-audit/manifest.json` with schema
`neodojo.real_conversion_audit.v1`, the GPU probe status, source/export/demo
checks, `complete: false`, and the next action while the real artifact is
missing. This target exits successfully for blocker classification; use
`neodojo real-conversion audit-completion --require-complete` when automation
should fail unless a real non-fixture demo has been generated.

The returned-artifact import wrapper is now covered by fixture-only local and
CI smoke evidence: `make real-artifact-intake-smoke` writes fixture source
materialization and GVHMR JSON inputs, runs `make real-artifact-intake`, and
produces source-validation, real-demo, public-demo, and capture manifests
without media. GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/26006210299` uploaded the
`neodojo-real-artifact-intake-smoke` artifact and verified 36 frames at 24 fps
with matching provenance. The generated real-demo manifest separates
`gvhmr_artifact_imported` from `real_gvhmr_artifact_imported`, so fixture smoke
records the contract import without claiming a real GVHMR execution.

When the external artifact exists, the next command is:

```bash
make demo-real \
  SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json \
  GVHMR_JSON=outputs/real-conversion-gate/gvhmr-smplx-joints.json

make real-artifact-intake \
  REAL_ARTIFACT_GVHMR_JSON=outputs/real-conversion-gate/gvhmr-smplx-joints.json
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
