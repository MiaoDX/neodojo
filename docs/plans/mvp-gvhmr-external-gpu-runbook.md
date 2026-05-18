# MVP GVHMR Local GPU Runbook Plan

Status: SUPERSEDED BY LOCAL GPU RUNBOOK; LOCAL REAL ARTIFACT VERIFIED

## Goal

Move GVHMR execution instructions out of ignored generated
bundles and into a tracked local GPU runbook.

The current command surface supports local-machine GPU execution only. Colab,
hosted GPU providers, self-hosted Actions runners, and external operator
packages are parked.

## Dependencies

- [mvp-gvhmr-gpu-runner-surface.md](mvp-gvhmr-gpu-runner-surface.md) packages
  `run_gvhmr_neodojo.sh`.
- [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) remains the real
  artifact gate after the local GPU run returns.

## Inputs

- A local GPU run workspace from `make real-gpu-prep`.
- A CUDA-capable local machine.
- Licensed local SMPL-X assets and GVHMR checkpoints kept outside git.
- Upstream GVHMR install/demo instructions.

## Outputs

- `docs/runbooks/gvhmr-local-gpu.md`.
- README and README.zh links to the runbook.
- STATUS and plan-index updates noting that the local runbook exists and
  later local proof status is tracked separately.

## Execution Tasks

- [x] Add a tracked local-GPU runbook with preconditions, preparation steps,
  upstream GVHMR setup shape, wrapper invocation, local validation, and failure
  classification.
- [x] Link the runbook from README.md and README.zh.md without claiming GVHMR
  has run.
- [x] Update STATUS.md and the MVP implementation index.
- [x] Keep media, checkpoints, SMPL-X assets, `.pt`, and returned motion files
  out of tracked source.

## Acceptance Evidence

- The runbook names the current `make real-gpu-prep` path and the generic
  commands for preparing another local source.
- The runbook references upstream GVHMR's official repository/install docs and
  keeps checkpoint and SMPL-X asset setup outside this repo.
- The runbook shows the packaged `run_gvhmr_neodojo.sh` invocation and the
  local `make demo-real` validation command.
- The current ignored local GPU workspace has been checked for the runner,
  runbook, exporter, template, source metadata, and media references.
- `make check` includes this plan through the MVP index and validates the plan
  scaffold.

## Non-Goals

- Running GVHMR in CI.
- Provisioning, paying for, or authenticating to a GPU provider.
- Uploading media-containing outputs to CI artifacts or committing them.
- Downloading or committing GVHMR checkpoints or licensed SMPL/SMPL-X assets.
- Marking the real-conversion gate complete before a real export returns.

## Stop Condition

Stopped when the local GPU run path is tracked in repo docs, linked from the
README surface, and validated by `make check`. A later local GPU proof
produced and validated the non-fixture
`neodojo.gvhmr_smplx_joints.v1` export through ignored `outputs/`.
