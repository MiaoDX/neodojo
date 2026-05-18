# MVP Real GPU Archive Command Plan

Status: IMPLEMENTED ONE-COMMAND MEDIA ARCHIVE PREP; REAL ARTIFACT STILL EXTERNAL

## Goal

Provide one local make target that turns a local/user-supplied source video into
the ignored media-containing GPU transfer archive needed by the external GVHMR
operator.

The target must not run GVHMR locally, must keep media under ignored outputs,
and must preserve the existing source provenance, runner, exporter, and archive
validation boundaries.

## Dependencies

- [mvp-source-media-materialization.md](mvp-source-media-materialization.md)
  owns source prep and ffmpeg-backed materialization.
- [mvp-gvhmr-gpu-runner-surface.md](mvp-gvhmr-gpu-runner-surface.md) owns the
  packaged GPU runner.
- [mvp-gvhmr-gpu-transfer-archive.md](mvp-gvhmr-gpu-transfer-archive.md) owns
  archive validation and metadata.
- [mvp-gvhmr-external-gpu-runbook.md](mvp-gvhmr-external-gpu-runbook.md)
  explains the external GPU operator handoff.

## Inputs

- `LOCAL_VIDEO=path/to/local-source.mp4`.
- Optional `REAL_LOCAL_SOURCE_ID`, `REAL_LOCAL_TITLE`, trim, rights, and output
  variables already supported by `make real-handoff`.
- Local `ffmpeg` for actual trim/reference-frame materialization.

## Outputs

- `make real-gpu-archive`.
- `make real-gpu-run-request` as the archive plus operator-request wrapper.
- An ignored `outputs/gvhmr-gpu-input-archive/neodojo-gvhmr-gpu-input.tar.gz`
  by default, or a caller-specified `GPU_INPUT_ARCHIVE_OUT`.
- Docs and runbook updates showing the single command.

## Execution Tasks

- [x] Add `real-gpu-archive` to the Makefile.
- [x] Add `real-gpu-run-request` to chain archive creation and request
  generation.
- [x] Chain source prep, non-dry-run materialization, GPU input bundle creation
  with media, and transfer archive creation.
- [x] Preserve existing output override variables.
- [x] Document the command in README.md, README.zh.md, STATUS.md, and the GPU
  runbook.
- [x] Verify the command against an ignored local Bilibili candidate without
  committing media.

## Acceptance Evidence

- `make real-gpu-archive LOCAL_VIDEO=... REAL_DRY_RUN=0` writes a
  media-containing ignored archive.
- The archive manifest reports `archive_with_media`, `media_included: true`,
  and `safe_for_git: false`.
- `make real-gpu-run-request LOCAL_VIDEO=...` writes
  `outputs/gvhmr-gpu-run-request/manifest.json` with
  `status: ready_for_external_gpu`.
- The local smoke artifact at
  `outputs/real-gpu-archive-command-smoke/gpu-input-archive/manifest.json`
  records `source_id: local-archive-command-smoke`, a 2-second trim, and
  `ready_for_gpu_with_media` input status.
- Extracting the archive shows the trimmed clip, `RUN_ON_GPU.md`,
  `run_gvhmr_neodojo.sh`, `export_neodojo_gvhmr.py`, the export template, and
  source metadata.
- `make check` includes this plan through the MVP index.

## Non-Goals

- Running GVHMR locally or in CI.
- Uploading media-containing archives to CI artifacts.
- Committing source media, generated archives, checkpoints, `.pt`, `.pkl`,
  `.npz`, rendered videos, logs, or returned motion artifacts.
- Replacing the metadata-only CI smoke lane.

## Stop Condition

Stopped when one make command can produce the complete ignored media archive for
external GPU transfer and the only remaining real-conversion blocker is still
the external GPU-produced `neodojo.gvhmr_smplx_joints.v1` export.
