# MVP GVHMR GPU Transfer Archive Plan

Status: IMPLEMENTED CI-SAFE TRANSFER ARCHIVE; REAL ARTIFACT STILL EXTERNAL

## Goal

Turn the generated GVHMR GPU input bundle into one ignored transfer archive so
the remaining external GPU step can be moved to Colab, RunPod, Modal, or another
CUDA machine with a single upload.

The archive command must be safe for CI when the source bundle is metadata-only
and must preserve the media-safety boundary when the bundle explicitly includes
`source/trimmed-clip.mp4`.

## Dependencies

- [mvp-source-media-materialization.md](mvp-source-media-materialization.md)
  creates the source materialization handoff.
- [mvp-gvhmr-gpu-runner-surface.md](mvp-gvhmr-gpu-runner-surface.md) packages
  `run_gvhmr_neodojo.sh` in the GPU input bundle.
- [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) remains the real
  artifact gate after the archive is transferred to a GPU environment.

## Inputs

- A `neodojo.gvhmr_gpu_input_bundle.v1` bundle directory or manifest.
- Optional media already present inside that ignored bundle.
- An output directory under ignored `outputs/`.

## Outputs

- `neodojo.gvhmr_gpu_input_archive.v1` manifest with archive hash, source
  bundle hash, member list, media-included flag, and safe-for-git policy.
- `neodojo-gvhmr-gpu-input.tar.gz` containing the bundle files needed by the
  GPU operator.
- `make gpu-input-archive` and `make gpu-input-archive-smoke`.
- CI artifact for the metadata-only archive smoke.

## Execution Tasks

- [x] Add an archive writer that validates the GPU input bundle schema.
- [x] Include all bundle files in a `.tar.gz` while keeping generated archives
  out of the archive itself.
- [x] Record member hashes and archive hash in a new manifest.
- [x] Add CLI and Make targets for archive creation and metadata-only smoke.
- [x] Include the smoke in `make verify`.
- [x] Add focused tests for metadata-only and media-including archives.
- [x] Upload a metadata-only archive artifact from CI without source media.
- [x] Update README, README.zh, STATUS, and the plan index.

## Acceptance Evidence

- `make gpu-input-archive-smoke` writes
  `outputs/gvhmr-gpu-input-archive-smoke/neodojo-gvhmr-gpu-input.tar.gz`.
- The smoke archive contains `RUN_ON_GPU.md`, `export_neodojo_gvhmr.py`,
  `run_gvhmr_neodojo.sh`, the export template, and source-materialization
  metadata.
- The smoke archive does not contain source media.
- Unit tests cover both metadata-only and media-including archive manifests.
- CI uploads only the metadata-only archive.

## Non-Goals

- Running GVHMR locally or in CI.
- Uploading media-containing archives to CI artifacts.
- Providing a paid GPU provider integration.
- Committing generated archives, videos, model checkpoints, `.pt`, `.pkl`,
  `.npz`, or generated motion artifacts.

## Stop Condition

Stopped when a GPU input bundle can be turned into a single ignored archive,
the metadata-only archive is smoke-tested locally and in CI, and the only
remaining real-conversion blocker is still the external GPU-produced
`neodojo.gvhmr_smplx_joints.v1` export.
