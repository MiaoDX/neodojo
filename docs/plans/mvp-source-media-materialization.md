# MVP Source Media Materialization Plan

Status: IMPLEMENTED LOCAL HANDOFF

## Goal

Turn a prepared local source-video manifest into an ignored, GPU-ready source
handoff:

```text
real-conversion-prep manifest
  -> local/user-supplied video validation
  -> optional ffmpeg trim
  -> optional reference-frame extraction
  -> source-materialization manifest
  -> GVHMR input handoff command
  -> optional copyable GPU input bundle with media
```

This closes the gap between metadata-only source prep and a concrete trimmed
clip path that a GPU-capable GVHMR environment can consume. The command must
not download media, commit media, or imply that GVHMR has run.

## Dependencies

- [mvp-source-media-probing.md](mvp-source-media-probing.md) records local file
  checksum and advisory ffprobe metadata.
- [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) owns the later GPU
  GVHMR run and imported SMPL-X artifact.
- [mvp-pipeline-contract-hardening.md](mvp-pipeline-contract-hardening.md)
  defines local-only source-media policy and manifest versioning.

## Inputs

- A `neodojo.real_conversion_prep.v1` manifest from
  `neodojo real-conversion prepare`, either from an official source-index row
  or a custom local/user-supplied source created with `--local-source-id`.
- A local/user-supplied source video path, either in the prep manifest or passed
  with `--local-video`.
- A trim window from the prep manifest.
- Local `ffmpeg` and `ffprobe` when actual materialization is desired.

## Outputs

- `outputs/real-conversion-source/source-materialization.json` using schema
  `neodojo.real_conversion_source_materialization.v1`.
- Ignored `source/trimmed-clip.mp4` when ffmpeg materialization runs.
- Ignored `source/frames/frame-*.jpg` reference frames when extraction runs.
- Recorded ffmpeg trim/extract commands for dry-run and GPU handoff.
- Duration validation for the trimmed clip when ffprobe can inspect it.
- A `neodojo.gvhmr_input_handoff.v1` block that names the trimmed clip argument
  for the later GPU run.
- Optional ignored `outputs/gvhmr-gpu-input/` bundle with `RUN_ON_GPU.md`,
  handoff metadata, exporter helper, template, and the materialized trimmed
  clip when explicit media inclusion is requested.

## Execution Tasks

1. Add source materialization command.
   - [x] Add `neodojo real-conversion materialize-source`.
   - [x] Accept `--prep`, optional `--local-video`, `--frame-rate`, `--dry-run`,
     and `--out`.
   - [x] Require local file validation before materialization or dry-run.

2. Add ffmpeg handoff behavior.
   - [x] Write a dry-run manifest with exact trim and frame-extraction commands.
   - [x] Run ffmpeg trim and frame extraction when `--dry-run` is not used and
     ffmpeg is available.
   - [x] Fail clearly when ffmpeg is missing and actual processing was
     requested.

3. Preserve source and output policy.
   - [x] Keep generated clips and frames under ignored `outputs/`.
   - [x] Record checksums and paths, not committed media.
   - [x] Preserve rights notes and source-prep provenance.
   - [x] Preserve custom local-source id/title provenance through
     source-materialization and GPU handoff manifests.
   - [x] Add a separate `package-gpu-input` / `make gpu-input-bundle` step so
     media inclusion is explicit and remains under ignored outputs.

4. Verify.
   - [x] Unit-test dry-run manifest generation.
   - [x] Materialize a local ignored Bilibili Baduanjin candidate with ffmpeg
     under `outputs/real-handoff-local-bilibili/` and package a `ready_for_gpu`
     handoff while keeping rights unconfirmed.
   - [x] Package `outputs/gvhmr-gpu-input-local-bilibili/` with
     `GPU_INPUT_INCLUDE_MEDIA=1`; manifest reports `ready_for_gpu_with_media`.
   - [x] Keep `make verify` independent from real videos and ffmpeg.

## Acceptance Evidence

- `make test` covers dry-run source materialization and handoff metadata.
- `neodojo real-conversion materialize-source --dry-run ...` writes the
  source-materialization manifest without processing media.
- When ffmpeg is installed and a local video is supplied, the command writes a
  trimmed clip, extracts reference frames, and records duration validation.
- `make real-handoff ... REAL_LOCAL_SOURCE_ID=... REAL_DRY_RUN=0` can produce a
  materialized, checksum-validated, `ready_for_gpu` handoff from an ignored
  local source candidate.
- `make gpu-input-bundle GPU_HANDOFF=... GPU_INPUT_INCLUDE_MEDIA=1` can package
  that handoff plus the trimmed clip into an ignored transfer directory.
- Generated media stays under ignored output directories.

## Non-Goals

- Downloading official videos.
- Running GVHMR locally.
- Requiring ffmpeg or source videos in CI.
- Committing trimmed clips, frames, or videos.
- Validating qigong motion correctness.
- Parsing native GVHMR outputs.

## Stop Condition

Stopped when a local source-prep manifest can produce either a dry-run GPU
handoff manifest or an actual ignored trimmed-clip/reference-frame bundle for a
later GVHMR run.
