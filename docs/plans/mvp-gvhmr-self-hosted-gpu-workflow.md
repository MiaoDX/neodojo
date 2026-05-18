# MVP GVHMR Self-Hosted GPU Workflow Plan

Status: IMPLEMENTED OPTIONAL WORKFLOW; REAL ARTIFACT STILL EXTERNAL

## Goal

Turn the remaining external GVHMR execution step into an optional, tracked
GitHub Actions workflow for a user-managed self-hosted GPU runner.

This does not make the default GitHub-hosted CI lane run GVHMR. It adds a
manual `workflow_dispatch` path that can unpack a prepared neodojo GPU input
archive on a runner labeled `self-hosted` and `gpu`, run the packaged
`run_gvhmr_neodojo.sh` wrapper, and optionally upload only the returned
`gvhmr-smplx-joints.json` export.

## Dependencies

- [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) owns the real
  artifact gate and import validation.
- [mvp-gvhmr-gpu-runner-surface.md](mvp-gvhmr-gpu-runner-surface.md) packages
  `run_gvhmr_neodojo.sh`.
- [mvp-gvhmr-gpu-transfer-archive.md](mvp-gvhmr-gpu-transfer-archive.md)
  packages the media-including archive that the self-hosted runner consumes.
- [mvp-gvhmr-external-gpu-runbook.md](mvp-gvhmr-external-gpu-runbook.md)
  remains the durable operator checklist.

## Inputs

- A media-including `neodojo-gvhmr-gpu-input.tar.gz` archive already present on
  the self-hosted GPU runner.
- A self-hosted GitHub Actions runner labeled `gpu`.
- A GVHMR checkout or permission to clone/install GVHMR on that runner.
- Licensed local SMPL-X assets and GVHMR checkpoints kept outside git.
- Rights approval for the selected source clip.

## Outputs

- `.github/workflows/gvhmr-self-hosted-gpu.yml`.
- A manual `gvhmr-self-hosted-gpu` workflow that is not triggered by push or
  pull request events.
- Optional short-lived `neodojo-gvhmr-smplx-joints` artifact containing only
  `gvhmr-smplx-joints.json`.
- README, README.zh, STATUS, runbook, and implementation-index updates.

## Execution Tasks

- [x] Add a workflow-dispatch-only GitHub Actions workflow for self-hosted GPU
  runners labeled `[self-hosted, gpu]`.
- [x] Require the media-containing archive path as a runner-local input instead
  of uploading media through default CI.
- [x] Require explicit SMPL-X model directory and GVHMR repo inputs.
- [x] Support running full GVHMR or exporting from an existing
  `hmr4d_results.pt` with `skip_gvhmr`.
- [x] Upload only `gvhmr-smplx-joints.json` when the operator explicitly opts
  into `upload_neodojo_export`.
- [x] Add focused tests/smoke checks that the workflow is manual, self-hosted,
  and does not upload media or checkpoint/model files.
- [x] Update README.md, README.zh.md, STATUS.md, the runbook, and the plan
  index without claiming a real GVHMR artifact has been produced.

## Acceptance Evidence

- The workflow contains `workflow_dispatch` and no push or pull-request trigger.
- The workflow runs only on `[self-hosted, gpu]`.
- The workflow validates the archive, runner script, exporter, template, and
  source materialization before executing the wrapper.
- The only uploaded path in the workflow is
  `outputs/self-hosted-gvhmr-run/gvhmr-smplx-joints.json`, and upload is
  controlled by `upload_neodojo_export`.
- `make test` covers the workflow shape and upload boundary.
- `make check` includes this plan through the MVP index.

## Non-Goals

- Running GVHMR on the local macOS CPU workspace.
- Running GVHMR on the default GitHub-hosted `ubuntu-latest` CI runner.
- Provisioning, paying for, or registering the self-hosted GPU runner.
- Uploading source videos, trimmed clips, checkpoints, SMPL-X assets, `.pt`
  files, rendered videos, logs, or full result directories as artifacts.
- Marking the real-conversion gate complete before the returned export is
  validated and imported locally.

## Stop Condition

Stopped when the optional self-hosted GPU workflow is tracked, documented,
smoke-tested as a manual GPU-only path, and the remaining real-conversion
blocker is still the actual GPU-produced
`neodojo.gvhmr_smplx_joints.v1` export.
