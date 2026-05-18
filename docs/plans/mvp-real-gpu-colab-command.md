# MVP Real GPU Colab Command Plan

Status: IMPLEMENTED ONE-COMMAND ARCHIVE, REQUEST, AND COLAB HANDOFF; REAL ARTIFACT STILL EXTERNAL

## Goal

Provide one local make target that turns a local/user-supplied source video into
the ignored media-containing GPU transfer archive, generated operator request,
and Colab-ready notebook needed by a notebook-based external GVHMR operator.

The target must not run GVHMR locally, must keep media and generated archives
under ignored outputs, and must preserve the existing source provenance,
checksum, runner, exporter, and returned-artifact validation boundaries.

## Dependencies

- [mvp-real-gpu-archive-command.md](mvp-real-gpu-archive-command.md) owns the
  local media archive and generated run-request wrappers.
- [mvp-gvhmr-colab-operator-notebook.md](mvp-gvhmr-colab-operator-notebook.md)
  owns the request-to-notebook writer and smoke coverage.
- [mvp-gvhmr-external-gpu-runbook.md](mvp-gvhmr-external-gpu-runbook.md)
  explains the external GPU operator handoff.
- [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) owns returned
  artifact validation and the strict completion gate.
- [mvp-gvhmr-operator-package.md](mvp-gvhmr-operator-package.md) extends this
  handoff by collocating the archive, request, and notebook into one copyable
  ignored operator package.

## Inputs

- `LOCAL_VIDEO=path/to/local-source.mp4`.
- Optional `REAL_LOCAL_SOURCE_ID`, `REAL_LOCAL_TITLE`, trim, rights, and output
  variables already supported by `make real-handoff`.
- Local `ffmpeg` for actual trim/reference-frame materialization.

## Outputs

- `make real-gpu-colab-notebook`.
- An ignored media-containing GPU input archive under `GPU_INPUT_ARCHIVE_OUT`.
- A generated `neodojo.gvhmr_gpu_run_request.v1` manifest and README under
  `GVHMR_RUN_REQUEST_OUT`.
- A generated `neodojo.gvhmr_colab_operator_notebook.v1` manifest and
  `gvhmr-colab-operator.ipynb` under `GVHMR_COLAB_NOTEBOOK_OUT`.

## Execution Tasks

- [x] Add `real-gpu-colab-notebook` to the Makefile.
- [x] Chain `real-gpu-run-request` and `gvhmr-colab-notebook` while preserving
  existing output override variables.
- [x] Document the command in README.md, README.zh.md, STATUS.md, the GPU
  runbook, and the MVP plan index.
- [x] Verify the command against an ignored local Bilibili candidate without
  committing media.

## Acceptance Evidence

- `make real-gpu-colab-notebook LOCAL_VIDEO=...` writes a media-containing
  ignored archive, generated run request, and Colab operator notebook.
- The generated notebook manifest reports
  `schema: neodojo.gvhmr_colab_operator_notebook.v1`,
  `status: ready_for_colab_operator`, `media_included: true`, and
  `safe_for_git: false`.
- The local smoke artifact at
  `outputs/real-gpu-colab-command-smoke/colab-operator/manifest.json` records
  `source_id: local-colab-command-smoke`, a 2-second trim, and
  `status: ready_for_colab_operator`.
- The generated request manifest reports
  `schema: neodojo.gvhmr_gpu_run_request.v1`,
  `status: ready_for_external_gpu`, and expected return schema
  `neodojo.gvhmr_smplx_joints.v1`.
- `make check` includes this plan through the MVP index.

## Non-Goals

- Running GVHMR locally, in CI, or without a GPU-capable notebook runtime.
- Uploading media-containing archives or notebooks to CI artifacts.
- Committing source media, generated archives, checkpoints, `.pt`, `.pkl`,
  `.npz`, returned GVHMR JSON, logs, rendered videos, or generated outputs.
- Replacing the metadata-only CI smoke lane.

## Stop Condition

Stopped when one make command can produce the complete ignored Colab handoff
for external GPU execution and the only remaining real-conversion blocker is
still the external GPU-produced `neodojo.gvhmr_smplx_joints.v1` export.
