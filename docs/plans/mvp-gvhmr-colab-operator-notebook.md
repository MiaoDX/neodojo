# MVP GVHMR Colab Operator Notebook Plan

Status: IMPLEMENTED GENERATED NOTEBOOK; REAL ARTIFACT STILL EXTERNAL

## Goal

Make the remaining external GVHMR run easier for operators who do not have a
self-hosted GitHub GPU runner by generating a Colab-ready notebook from the
existing GPU run-request manifest.

The notebook is a handoff artifact only. It does not run GVHMR locally, bundle
media, include checkpoints, include SMPL-X assets, or replace the strict
returned-artifact gate.

## Dependencies

- [mvp-gvhmr-external-run-request.md](mvp-gvhmr-external-run-request.md)
  produces the request manifest with archive hash, expected return schema, and
  local return commands.
- [mvp-gvhmr-external-gpu-runbook.md](mvp-gvhmr-external-gpu-runbook.md)
  remains the detailed operator checklist.
- [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) owns the returned
  artifact import and strict completion audit.

## Inputs

- A `neodojo.gvhmr_gpu_run_request.v1` manifest or request directory.
- A GPU notebook runtime where the operator can upload the prepared archive and
  provide private GVHMR checkpoints plus licensed local SMPL-X assets.

## Outputs

- `neodojo.gvhmr_colab_operator_notebook.v1` manifest.
- `gvhmr-colab-operator.ipynb` containing archive checksum verification,
  archive unpacking, runner help validation, guarded GVHMR execution, returned
  JSON download, and local `make real-artifact-intake` / `make verify-real`
  commands.
- CLI command:

  ```bash
  PYTHONPATH=src python -m neodojo real-conversion write-colab-notebook \
    --gpu-run-request outputs/gvhmr-gpu-run-request \
    --out outputs/gvhmr-colab-operator
  ```

- Make targets:

  ```bash
  make gvhmr-colab-notebook GVHMR_RUN_REQUEST=outputs/gvhmr-gpu-run-request
  make gvhmr-colab-notebook-smoke
  ```

## Execution Tasks

- [x] Add a notebook writer that validates the run-request schema.
- [x] Generate notebook cells for upload/mount guidance, archive checksum
  verification, archive unpacking, runner help validation, guarded execution,
  returned JSON download, and local validation commands.
- [x] Write a sidecar manifest with notebook hash, source run-request hash,
  expected return schema, media policy, and readiness status.
- [x] Add CLI and Make targets for notebook generation and metadata-only smoke.
- [x] Include the smoke target in `make verify`.
- [x] Upload the metadata-only notebook smoke artifact from the public-demo
  GitHub Actions workflow.
- [x] Add focused tests for media-including and metadata-only run requests.
- [x] Update README.md, README.zh.md, STATUS.md, the runbook, and the MVP plan
  index without claiming a real GVHMR artifact has been produced.

## Acceptance Evidence

- `make gvhmr-colab-notebook-smoke` writes
  `outputs/gvhmr-colab-operator-smoke/manifest.json` and
  `gvhmr-colab-operator.ipynb`.
- Media-including run-request tests produce `status: ready_for_colab_operator`
  and preserve `safe_for_git: false`.
- Metadata-only run-request tests produce
  `status: metadata_only_not_ready_for_gpu` and preserve `safe_for_git: true`.
- The generated notebook includes the archive SHA-256 and keeps GVHMR execution
  guarded behind `RUN_GVHMR = False` by default.
- `make verify` includes the notebook smoke target.
- The public-demo workflow uploads `neodojo-gvhmr-colab-operator-smoke`.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26009044473` passed and the
  downloaded notebook smoke artifact reports
  `neodojo.gvhmr_colab_operator_notebook.v1`,
  `status: metadata_only_not_ready_for_gpu`, `safe_for_git: true`, checksum
  verification, guarded `RUN_GVHMR = False`, safe archive-member validation,
  and local return commands.

## Non-Goals

- Running GVHMR on the local macOS CPU workspace.
- Provisioning Colab, a paid GPU provider, or a self-hosted runner.
- Uploading media-containing archives to CI artifacts.
- Committing source media, generated archives, checkpoints, `.pt`, `.pkl`,
  `.npz`, returned GVHMR JSON, logs, or rendered videos.
- Replacing the self-hosted GPU workflow or the detailed external GPU runbook.

## Stop Condition

Stopped when an existing GPU run request can generate a Colab-ready operator
notebook that is smoke-tested locally and included in `make verify`, leaving
the actual GVHMR execution as the only remaining external step.
