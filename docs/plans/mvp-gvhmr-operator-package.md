# MVP GVHMR Operator Package Plan

Status: IMPLEMENTED COLLOCATED OPERATOR PACKAGE; REAL ARTIFACT STILL EXTERNAL

## Goal

Create one copyable operator package directory that collocates the GPU input
archive, generated run request, Colab operator notebook, and a package manifest
for the external GVHMR operator.

The package must not run GVHMR locally, must keep media-containing packages
under ignored outputs, and must preserve the existing checksum, source
provenance, rights, and returned-artifact validation boundaries.

## Dependencies

- [mvp-gvhmr-gpu-transfer-archive.md](mvp-gvhmr-gpu-transfer-archive.md) owns
  the archive and archive manifest.
- [mvp-gvhmr-external-run-request.md](mvp-gvhmr-external-run-request.md) owns
  the generated run request manifest and README.
- [mvp-gvhmr-colab-operator-notebook.md](mvp-gvhmr-colab-operator-notebook.md)
  owns the generated notebook and notebook manifest.
- [mvp-real-gpu-colab-command.md](mvp-real-gpu-colab-command.md) owns the
  local-video wrapper that prepares the archive, request, and notebook.

## Inputs

- A `neodojo.gvhmr_gpu_input_archive.v1` manifest or archive directory.
- A matching `neodojo.gvhmr_gpu_run_request.v1` manifest or request directory.
- A matching `neodojo.gvhmr_colab_operator_notebook.v1` manifest or notebook
  directory.

## Outputs

- `neodojo.gvhmr_operator_package.v1` manifest.
- Package-level `README.md`.
- Copied `archive/neodojo-gvhmr-gpu-input.tar.gz`.
- Copied `request/manifest.json` and `request/README.md`.
- Copied `colab/manifest.json` and `colab/gvhmr-colab-operator.ipynb`.
- CLI command:

  ```bash
  PYTHONPATH=src python -m neodojo real-conversion package-operator \
    --gpu-input-archive outputs/gvhmr-gpu-input-archive \
    --gpu-run-request outputs/gvhmr-gpu-run-request \
    --colab-notebook outputs/gvhmr-colab-operator \
    --out outputs/gvhmr-operator-package
  ```

- Make targets:

  ```bash
  make gvhmr-operator-package \
    GPU_INPUT_ARCHIVE=outputs/gvhmr-gpu-input-archive \
    GVHMR_RUN_REQUEST=outputs/gvhmr-gpu-run-request \
    GVHMR_COLAB_NOTEBOOK=outputs/gvhmr-colab-operator

  make real-gpu-operator-package LOCAL_VIDEO=path/to/local-source.mp4
  make gvhmr-operator-package-smoke
  make gvhmr-operator-package-validate GVHMR_OPERATOR_PACKAGE=outputs/gvhmr-operator-package
  ```

## Execution Tasks

- [x] Add a package writer that validates archive, request, and notebook
  schemas.
- [x] Verify matching archive, request, and notebook checksums before copying
  files.
- [x] Write a package manifest and package README with local return commands.
- [x] Add CLI and Make targets for direct packaging and local-video packaging.
- [x] Include a metadata-only package smoke in `make verify`.
- [x] Add a reusable validator for an already-collocated package before
  external transfer or self-hosted workflow dispatch.
- [x] Upload the metadata-only package smoke artifact from the public-demo
  GitHub Actions workflow.
- [x] Add focused tests for media-including and metadata-only package creation.
- [x] Update README.md, README.zh.md, STATUS.md, the runbook, and the MVP plan
  index without claiming a real GVHMR artifact has been produced.

## Acceptance Evidence

- `make gvhmr-operator-package-smoke` writes
  `outputs/gvhmr-operator-package-smoke/manifest.json`, `README.md`, copied
  archive, request, and notebook files.
- Media-including package tests produce
  `status: ready_for_external_gpu_operator_package` and preserve
  `safe_for_git: false`.
- Metadata-only package tests produce `status: metadata_only_not_ready_for_gpu`
  and preserve `safe_for_git: true`.
- The package manifest records expected return schema
  `neodojo.gvhmr_smplx_joints.v1` and local `make real-artifact-intake` /
  `make verify-real` commands.
- `make verify` includes the operator package smoke target.
- `make gvhmr-operator-package-validate` validates package, request, and
  notebook schemas plus archive/request/notebook checksum links for an existing
  collocated package.
- The public-demo workflow uploads `neodojo-gvhmr-operator-package-smoke`,
  verified by GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26009913491`.

## Non-Goals

- Running GVHMR locally, in CI, or without private GPU/runtime assets.
- Uploading media-containing operator packages to CI artifacts.
- Committing source media, generated archives, checkpoints, `.pt`, `.pkl`,
  `.npz`, returned GVHMR JSON, logs, rendered videos, or generated outputs.
- Replacing the strict returned-artifact gate.

## Stop Condition

Stopped when the archive, run request, and Colab notebook can be collocated into
one validated operator package, with metadata-only CI smoke coverage, leaving the
actual GVHMR execution as the only remaining external step.
