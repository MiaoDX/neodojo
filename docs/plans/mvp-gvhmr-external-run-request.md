# MVP GVHMR External Run Request Plan

Status: IMPLEMENTED GENERATED RUN REQUEST; REAL ARTIFACT STILL EXTERNAL

## Goal

Make the final external GVHMR step easier to execute by generating one concise
operator request from an existing GPU input archive.

The repo already creates a media-containing archive and durable runbook. This
slice adds a small, auditable request artifact that records the archive path,
hash, source, trim, required GPU assets, manual commands, self-hosted workflow
option, and local return commands. It still does not run GVHMR locally.

## Dependencies

- [mvp-gvhmr-gpu-transfer-archive.md](mvp-gvhmr-gpu-transfer-archive.md)
  produces the GPU input archive and manifest.
- [mvp-gvhmr-external-gpu-runbook.md](mvp-gvhmr-external-gpu-runbook.md)
  remains the detailed operator checklist.
- [mvp-gvhmr-self-hosted-gpu-workflow.md](mvp-gvhmr-self-hosted-gpu-workflow.md)
  remains the optional GitHub Actions route when a runner exists.
- [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) owns the final
  returned-artifact import and strict completion gate.

## Inputs

- A `neodojo.gvhmr_gpu_input_archive.v1` manifest or archive directory.
- The archive file referenced by that manifest.
- Optional existing runbook and self-hosted workflow paths.

## Outputs

- `neodojo.gvhmr_gpu_run_request.v1` manifest.
- Operator `README.md` with unpack, run, return, and verification commands.
- CLI command:

  ```bash
  PYTHONPATH=src python -m neodojo real-conversion write-gpu-run-request \
    --gpu-input-archive outputs/gvhmr-gpu-input-archive \
    --out outputs/gvhmr-gpu-run-request
  ```

- Make targets:

  ```bash
  make gvhmr-run-request GPU_INPUT_ARCHIVE=outputs/gvhmr-gpu-input-archive
  make real-gpu-run-request LOCAL_VIDEO=path/to/local-source.mp4
  make gvhmr-run-request-smoke
  ```

## Execution Tasks

- [x] Add a run-request writer that validates the archive manifest schema and
  archive checksum.
- [x] Record archive filename/path/hash, source metadata, trim metadata, safety
  policy, required GPU assets, expected return artifact schema, manual GPU
  commands, local import command, and strict verification command.
- [x] Write a concise operator README next to the request manifest.
- [x] Add CLI and Make targets for request generation and metadata-only smoke.
- [x] Add a one-command local media archive plus request target for operator
  handoff preparation.
- [x] Include the smoke target in `make verify`.
- [x] Upload the metadata-only run-request smoke artifact from the public-demo
  GitHub Actions workflow.
- [x] Add focused tests for media-including and metadata-only archives.
- [x] Update README.md, README.zh.md, STATUS.md, the runbook, and the MVP plan
  index without claiming the real artifact has been produced.

## Acceptance Evidence

- `make gvhmr-run-request-smoke` writes a metadata-only
  `outputs/gvhmr-gpu-run-request-smoke/manifest.json` and `README.md`.
- Media-including archive tests produce `status: ready_for_external_gpu` and
  preserve `safe_for_git: false`.
- Metadata-only archive tests produce `status: metadata_only_not_ready_for_gpu`
  and preserve `safe_for_git: true`.
- The request manifest records `expected_return_artifact.schema:
  neodojo.gvhmr_smplx_joints.v1`.
- The generated README tells the operator that the returned
  `gvhmr-smplx-joints.json` must be the GPU-generated
  `neodojo.gvhmr_smplx_joints.v1` export with `fixture_only: false`, not the
  template or fixture smoke JSON.
- `make real-gpu-run-request LOCAL_VIDEO=...` writes both a media-containing
  archive and a matching request manifest/README under ignored outputs.
- `make verify` includes the run-request smoke target.
- The public-demo workflow uploads `neodojo-gpu-run-request-smoke`; the
  downloaded artifact from run `26014431712` verified the non-fixture return
  wording.

## Non-Goals

- Running GVHMR on the local macOS CPU workspace.
- Provisioning a GPU provider or self-hosted runner.
- Uploading media-containing archives to CI artifacts.
- Committing source media, generated archives, checkpoints, `.pt`, `.pkl`,
  `.npz`, returned GVHMR JSON, logs, or rendered videos.
- Replacing the detailed external GPU runbook.

## Stop Condition

Stopped when an existing GPU input archive can be turned into a concise
operator request artifact that is smoke-tested locally and included in
`make verify`, leaving the actual GVHMR execution as the only remaining
external step.
