# MVP Real Conversion Gate Plan

Status: LOCAL GPU PROOF COMPLETE; STRICT AUDIT PASSED; LIVE PAGES STILL FIXTURE-ONLY

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
- [mvp-real-gpu-colab-command.md](mvp-real-gpu-colab-command.md) chains local
  source materialization, transfer archive, generated run request, and Colab
  notebook handoff for notebook-based GPU operators.
- [mvp-gvhmr-operator-package.md](mvp-gvhmr-operator-package.md) collocates the
  archive, run request, and notebook into one copyable operator package.
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
Use `make real-gpu-run-request LOCAL_VIDEO=...` when the same local command
should also write the generated operator request from that archive.
Use `make real-gpu-colab-notebook LOCAL_VIDEO=...` when the same local command
should also write the generated Colab operator notebook from that request.
Use `make real-gpu-operator-package LOCAL_VIDEO=...` when the external operator
should receive one collocated package directory containing the archive, request,
and notebook.
Use `make real-gpu-operator-package-archive LOCAL_VIDEO=...` when the external
operator should receive that validated package as one transfer `.tar.gz`; use
`make gvhmr-operator-package-archive-validate GVHMR_OPERATOR_PACKAGE_ARCHIVE=...`
to recheck an existing package archive artifact before handoff.
Use `make real-gvhmr-acquisition-status GVHMR_OPERATOR_PACKAGE_ARCHIVE=...`
after archive validation to write a non-failing operator-facing preflight. That
manifest records whether the archive is media-containing and ready for external
GPU handoff, embeds the current real-conversion audit status, and repeats the
required non-fixture return-artifact contract without running GVHMR.

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

make gpu-execution-probe GPU_PROBE_GITHUB_REPO=MiaoDX/neodojo

PYTHONPATH=src python -m neodojo real-conversion inspect-gvhmr-result \
  --source outputs/real-conversion-gate/hmr4d_results.pt \
  --out outputs/gvhmr-result-inspection

make gvhmr-inspect \
  GVHMR_RESULT=outputs/real-conversion-gate/hmr4d_results.pt
```

The GPU execution probe writes a safe readiness manifest with local CUDA,
Docker GPU runtime, provider CLI, provider environment-variable-name, and
optional GitHub self-hosted GPU runner evidence only; it does not record secret
values, secret names, or run GVHMR. Native `.pt`
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
- [x] Generate an external GPU run-request manifest and README from a transfer
  archive so the remaining operator step has archive hash, required assets,
  expected return artifact, GPU commands, and local return checks in one place.
- [x] Add `make real-gpu-run-request LOCAL_VIDEO=...` to prepare the ignored
  media archive and generated operator request together for local GPU handoff.
- [x] Add `make real-gpu-colab-notebook LOCAL_VIDEO=...` to prepare the ignored
  media archive, generated operator request, and Colab operator notebook
  together for notebook-based GPU handoff.
- [x] Add `make real-gpu-operator-package LOCAL_VIDEO=...` to collocate the
  ignored media archive, generated operator request, and Colab notebook into one
  package directory for transfer.
- [x] Add `make real-gpu-operator-package-archive LOCAL_VIDEO=...` and
  `make gvhmr-operator-package-archive GVHMR_OPERATOR_PACKAGE=...` to wrap a
  validated collocated package as one transfer `.tar.gz`.
- [x] Add `make gvhmr-operator-package-archive-validate
  GVHMR_OPERATOR_PACKAGE_ARCHIVE=...` to revalidate existing package archives.
- [x] Add `make real-gvhmr-acquisition-status
  GVHMR_OPERATOR_PACKAGE_ARCHIVE=...` to write a non-failing preflight that
  validates the operator package archive, embeds the blocked real-conversion
  audit, and repeats the non-fixture return contract.
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
- [x] Extend the probe with an opt-in GitHub Actions check for self-hosted GPU
  runner availability and repository secret counts without recording secret
  values or secret names.
- [x] Add `real-conversion audit-completion` / `make real-conversion-audit`
  so local and CI runs write a non-failing blocker classification manifest for
  this gate.
- [x] Add `make real-conversion-audit-strict` / `make verify-real` as opt-in
  failing gates that require a real non-fixture demo before reporting success.
- [x] Add an optional self-hosted GPU workflow-dispatch path that can run the
  packaged archive on a user-managed runner without changing default CI.
- [x] Have that self-hosted workflow run returned-artifact intake and strict
  audit after the GPU wrapper produces `gvhmr-smplx-joints.json`.
- [x] Add a guarded manual Pages promotion workflow that can publish a validated
  self-hosted real-demo artifact only after explicit confirmation and strict
  real-demo audit validation.
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

## Current Local Gate Status

The local, non-GPU side of this gate is complete through prep,
source-materialization, GPU handoff packaging, GPU runner packaging, transfer
archive packaging, GPU execution readiness probing, returned-result inspection,
GPU-side export-helper packaging, returned-export validation, motion import,
and `import-demo`/`make demo-real` demo regeneration.

On this GPU workstation, the packaged wrapper has also been run against an
ignored Bilibili Baduanjin proof clip. It produced
`outputs/gvhmr-gpu-input-local-bilibili/gvhmr-smplx-joints.json` with schema
`neodojo.gvhmr_smplx_joints.v1`, `fixture_only: false`, 300 frames at 25 fps.
`make real-artifact-intake` imported it through `outputs/real-demo/`, and the
strict audit at `outputs/real-conversion-audit-local-bilibili/manifest.json`
reports `status: real_demo_verified` and `complete: true`.

The live public Pages artifact remains fixture-only unless a guarded real-demo
promotion is explicitly run. The generated local real-demo still uses fixture
components for the G1 visual companion unless an external GMR track and model
descriptor are supplied.

The broader real-conversion completion audit is now executable with
`make real-conversion-audit`. It writes
`outputs/real-conversion-audit/manifest.json` with schema
`neodojo.real_conversion_audit.v1`, the GPU probe status, source/export/demo
checks, and either a missing-artifact blocker or a completed local real-demo
status. Use `make real-conversion-audit REAL_AUDIT_GITHUB_REPO=OWNER/REPO`
when the audit should include the opt-in GitHub runner/secret-count probe. This
target exits successfully for blocker classification. Use
`make real-conversion-audit-strict`, `make verify-real`, or
`neodojo real-conversion audit-completion --require-complete` when automation
should fail unless a real non-fixture demo has been generated.
The default public-demo workflow uploads both the default audit artifact and a
separate opt-in GitHub-route audit artifact for CI evidence.
The operator-facing acquisition preflight is executable with
`make real-gvhmr-acquisition-status`. For a media-containing package archive it
reports `ready_for_external_gpu_operator` before a returned export is attached;
for metadata-only CI smoke artifacts it reports
`operator_package_archive_not_ready_for_gpu`. The default public-demo workflow
also uploads the metadata-only acquisition-status artifact with the nested audit
manifest.
GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/26006485103` uploaded the
`neodojo-real-conversion-audit` artifact and verified the CI state is still
`external_gpu_artifact_missing` with no media/checkpoint files and no recorded
secret values.
GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/26006738133` verified the
strict gate change without making the default fixture CI lane fail; the
downloaded real-conversion audit artifact remains
`external_gpu_artifact_missing`, `complete: false`, and `blocked: true`.
GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/26007158313` verified the
self-hosted return-artifact intake workflow changes without changing the
default fixture CI lane; the downloaded public-demo artifact remains
fixture-only and the downloaded real-conversion audit artifact remains
`external_gpu_artifact_missing`, `complete: false`, and `blocked: true`.
GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/26010670374` verified the
self-hosted workflow package-validation hardening without changing the default
fixture CI lane; the workflow now validates operator-package, run-request, and
Colab-notebook schemas plus archive/request/notebook checksum links for
`gvhmr_operator_package_path`, and the downloaded real-conversion audit artifact
still reports `external_gpu_artifact_missing` with `complete: false` and
`blocked: true`.
GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/26011378922` verified copied
operator-package validation during package creation without changing the default
fixture CI lane. The downloaded public-demo artifact passes
`neodojo demo smoke` and remains fixture-only with SMPL-X scoring and G1
visual-only labels, while the real-conversion audit still reports
`external_gpu_artifact_missing`, `complete: false`, and `blocked: true`.
GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/26012215777` verified the
separate opt-in GitHub-route real-conversion audit artifact without changing
the default fixture CI lane. The artifact records the same
`external_gpu_artifact_missing` blocker and no secret names or values. In CI,
the default integration token could not read runner/secret-count endpoints, so
the nested probe safely recorded GitHub API 403 errors rather than recording
unknown counts as facts.
GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/26013198280` verified the
operator-package archive validator in CI and the downloaded
`neodojo-gvhmr-operator-package-archive-smoke` artifact was revalidated locally
from a moved download directory. The real-conversion audit still reports
`external_gpu_artifact_missing`, `complete: false`, and `blocked: true`.
GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/26013871155` verified the
current default CI lane after command-surface alignment: the downloaded
public-demo artifact passes `neodojo demo smoke`, the downloaded metadata-only
operator package archive revalidates successfully, and the downloaded
real-conversion audit still reports `external_gpu_artifact_missing`,
`complete: false`, and `blocked: true`.
GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/26014431712` verified the
latest default CI lane after clarifying the returned GVHMR export fixture flag:
the downloaded public-demo artifact passes `neodojo demo smoke`, the downloaded
GPU input template records `fixture_only: false`, the downloaded GPU
run-request README and nested operator-package request README explicitly require
the returned `gvhmr-smplx-joints.json` to be the GPU-generated
`neodojo.gvhmr_smplx_joints.v1` export with `fixture_only: false`, the
downloaded operator-package README and archived README record the expected
return fixture flag as `false`, and the downloaded real-conversion audit still
reports `external_gpu_artifact_missing`, `complete: false`, and
`blocked: true`.
GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/26015790002` verified the
metadata-only acquisition-status artifact upload in the default CI lane. The
downloaded `neodojo-real-gvhmr-artifact-acquisition-status` artifact reports
`neodojo.real_gvhmr_artifact_acquisition.v1`, `status:
operator_package_archive_not_ready_for_gpu`, `blocked: true`, `complete:
false`, nested audit status `external_gpu_artifact_missing`, and expected
return `fixture_only: false`. The downloaded operator-package archive
revalidates as `metadata_only_not_ready_for_gpu`, the downloaded public-demo
artifact passes `neodojo demo smoke`, and Pages deployed.
GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/26015918309` verified the
default public-demo workflow. The downloaded
`neodojo-public-demo` artifact passed `neodojo demo smoke` and contained the
CI-generated `index.html`, `scene.json`, `neodojo-demo.rrd`, and
`screenshot.svg` fixture-demo artifacts.

The local high-level media-containing
`make real-gpu-operator-package-archive LOCAL_VIDEO=...` target was run against
an ignored local Bilibili proof candidate with isolated outputs under
`outputs/real-gpu-operator-package-archive-target-smoke/`. It produced a
validated `neodojo.gvhmr_operator_package_archive.v1` archive with `status:
ready_for_external_gpu_operator_package_archive`, `media_included: true`,
`policy.safe_for_git: false`, and archive checksum
`39ff72c8390161b16766eb5d6bb19c3918ce2d958e4739506c358a228433deb2`. That
handoff path remains useful for new source clips, but the Bilibili proof clip
has now completed local GPU execution on this workstation and returned a
non-fixture export.

An optional manual GitHub Actions path now exists at
`.github/workflows/gvhmr-self-hosted-gpu.yml`. It requires a user-managed
self-hosted runner labeled `gpu`, either a runner-local media-containing archive
path or a runner-local GVHMR operator package path, GVHMR
dependencies/checkpoints, and licensed local SMPL-X assets. It is not triggered
by push or pull request events. After the wrapper writes
`gvhmr-smplx-joints.json`, it runs `make real-artifact-intake` and
`real-conversion audit-completion --require-complete` against the returned
artifact. It only uploads returned JSON or generated real-demo/public-demo
artifacts when the operator explicitly enables the relevant upload input.

A second optional manual GitHub Actions path now exists at
`.github/workflows/promote-real-demo-pages.yml`. It is also
`workflow_dispatch` only. It downloads a named `neodojo-self-hosted-real-demo`
artifact from a selected run, revalidates the real-demo manifest, strict audit
manifest, generated public-demo files, SMPL-X scoring boundary, and public-demo
smoke check, then deploys the staged public-demo directory to GitHub Pages only
when `confirm_replace_fixture_pages=true` and the repository variable
`NEODOJO_DEPLOY_REAL_PAGES=true` are both set. It does not run GVHMR and must
not be used to publish raw media, checkpoints, SMPL-X assets, `.pt` files, or
logs.

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

For the current local proof, the commands are:

```bash
make demo-real \
  SOURCE_MATERIALIZATION=outputs/gvhmr-gpu-input-local-bilibili/source-materialization.json \
  GVHMR_JSON=outputs/gvhmr-gpu-input-local-bilibili/gvhmr-smplx-joints.json

make real-artifact-intake \
  REAL_ARTIFACT_SOURCE_MATERIALIZATION=outputs/gvhmr-gpu-input-local-bilibili/source-materialization.json \
  REAL_ARTIFACT_GVHMR_JSON=outputs/gvhmr-gpu-input-local-bilibili/gvhmr-smplx-joints.json
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

This gate's first-artifact stop condition has been met locally: one real
non-fixture GVHMR export imports successfully and regenerates the local
public-demo/capture artifacts. Follow-on work should be tracked as separate
GMR, simulator-rendering, publishing, or full-routine phases.
