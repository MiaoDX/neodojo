# MVP GVHMR External GPU Runbook Plan

Status: IMPLEMENTED TRACKED RUNBOOK; LOCAL REAL ARTIFACT VERIFIED

## Goal

Move GVHMR execution instructions out of ignored generated
bundles and into a tracked operator runbook that can be followed on Colab,
RunPod, Modal, Hugging Face Jobs, or another CUDA machine.

This plan does not make the local macOS CPU workspace run GVHMR. It makes the
manual external step concrete enough that the prepared archive can become a
returned `neodojo.gvhmr_smplx_joints.v1` artifact.

## Dependencies

- [mvp-gvhmr-gpu-runner-surface.md](mvp-gvhmr-gpu-runner-surface.md) packages
  `run_gvhmr_neodojo.sh`.
- [mvp-gvhmr-gpu-transfer-archive.md](mvp-gvhmr-gpu-transfer-archive.md)
  packages metadata-only and media-including transfer archives.
- [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) remains the real
  artifact gate after the external GPU run returns.

## Inputs

- A media-including `neodojo.gvhmr_gpu_input_archive.v1` archive.
- A CUDA-capable external machine.
- Licensed local SMPL-X assets and GVHMR checkpoints kept outside git.
- Upstream GVHMR install/demo instructions.

## Outputs

- `docs/runbooks/gvhmr-external-gpu.md`.
- README and README.zh links to the runbook.
- STATUS and plan-index updates noting that the external runbook exists and
  later local proof status is tracked separately.

## Execution Tasks

- [x] Add a tracked external-GPU runbook with preconditions, transfer steps,
  upstream GVHMR setup shape, wrapper invocation, local validation, and failure
  classification.
- [x] Link the runbook from README.md and README.zh.md without claiming GVHMR
  has run.
- [x] Update STATUS.md and the MVP implementation index.
- [x] Keep media, checkpoints, SMPL-X assets, `.pt`, and returned motion files
  out of tracked source.

## Acceptance Evidence

- The runbook names the current ignored local archive path and the generic
  commands for regenerating an archive from another local source.
- The runbook references upstream GVHMR's official repository/install docs and
  keeps checkpoint and SMPL-X asset setup outside this repo.
- The runbook shows the packaged `run_gvhmr_neodojo.sh` invocation and the
  local `make demo-real` validation command.
- The current ignored local archive has been extracted locally and checked for
  the runner, runbook, exporter, template, source metadata, and media.
- `make check` includes this plan through the MVP index and validates the plan
  scaffold.

## Non-Goals

- Running GVHMR locally or in CI.
- Provisioning, paying for, or authenticating to a GPU provider.
- Uploading media-containing archives to CI artifacts or committing them.
- Downloading or committing GVHMR checkpoints or licensed SMPL/SMPL-X assets.
- Marking the real-conversion gate complete before a real export returns.

## Stop Condition

Stopped when the external GPU operator path is tracked in repo docs, linked
from the README surface, and validated by `make check`. A later local GPU proof
produced and validated the non-fixture
`neodojo.gvhmr_smplx_joints.v1` export through ignored `outputs/`.
