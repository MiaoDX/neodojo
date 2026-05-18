# MVP GVHMR Self-Hosted Real Demo Intake Plan

Status: IMPLEMENTED OPTIONAL WORKFLOW INTAKE; LOCAL REAL ARTIFACT VERIFIED; WORKFLOW REMAINS OPTIONAL

## Goal

Close the handoff gap after the optional self-hosted GVHMR workflow produces
`gvhmr-smplx-joints.json`: run the returned artifact through neodojo's own
validation, import-demo, and strict audit steps in the same workflow.

This keeps the default fixture CI lane unchanged. The optional workflow path
still requires a user-managed GPU runner and a real GVHMR export, but the repo
also documents a separate local GPU proof that already passed the strict real
gate through ignored `outputs/`.

## Dependencies

- [mvp-gvhmr-self-hosted-gpu-workflow.md](mvp-gvhmr-self-hosted-gpu-workflow.md)
  provides the manual self-hosted GPU workflow.
- [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) owns the real
  artifact gate and strict audit.
- [mvp-devex-ci-surface.md](mvp-devex-ci-surface.md) owns the fixture public
  demo lane and upload conventions.

## Inputs

- `outputs/self-hosted-gvhmr-run/source-materialization.json` unpacked from the
  GPU input archive.
- `outputs/self-hosted-gvhmr-run/gvhmr-smplx-joints.json` produced by the GPU
  wrapper.
- Python environment on the self-hosted runner capable of installing the local
  neodojo package.

## Outputs

- `outputs/self-hosted-real-demo/manifest.json`.
- `outputs/self-hosted-real-demo/public-demo/index.html`.
- `outputs/self-hosted-real-demo/public-demo/manifest.json`.
- `outputs/self-hosted-real-demo/capture/manifest.json`.
- `outputs/self-hosted-real-audit/manifest.json` with `complete: true` when the
  returned artifact is real and imported successfully.
- Optional short-lived `neodojo-self-hosted-real-demo` artifact containing only
  generated manifests/public-demo/capture evidence, not source media or model
  checkpoints.

## Execution Tasks

- [x] Install the local neodojo package in the manual self-hosted GPU workflow
  after the GVHMR wrapper writes the returned JSON.
- [x] Run `make real-artifact-intake` against the unpacked
  `source-materialization.json` and returned `gvhmr-smplx-joints.json`.
- [x] Run `real-conversion audit-completion --require-complete` against the
  generated self-hosted real-demo output.
- [x] Add an opt-in `upload_real_demo` artifact containing only generated
  real-demo/public-demo/capture/audit files.
- [x] Add focused tests/smoke checks that the workflow runs the intake/audit
  commands and does not upload media, checkpoints, SMPL-X assets, or `.pt`
  files.
- [x] Update README.md, README.zh.md, STATUS.md, the runbook, and the plan
  index with intake boundaries; local real-artifact status is documented
  separately after proof.

## Acceptance Evidence

- The workflow runs `make real-artifact-intake` with
  `outputs/self-hosted-gvhmr-run/source-materialization.json` and
  `outputs/self-hosted-gvhmr-run/gvhmr-smplx-joints.json`.
- The workflow runs `neodojo real-conversion audit-completion
  --require-complete` against `outputs/self-hosted-real-demo`.
- The optional real-demo upload path includes generated public-demo/capture
  evidence and the strict audit manifest.
- The workflow upload paths do not include source media, checkpoints,
  SMPL-X assets, `.pt`, `.pkl`, `.npz`, or rendered videos.
- `make test` covers the workflow intake and upload boundary.
- `make check` includes this plan through the MVP index.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26007158313` verified the
  default fixture CI lane still passes and deploys after this workflow change;
  the downloaded public-demo artifact remains fixture-only. That historical CI
  artifact predates the local GPU proof, so its real-conversion audit still
  reported the missing returned export.

## Non-Goals

- Running GVHMR on the local macOS CPU workspace.
- Running the self-hosted GPU workflow on default GitHub-hosted CI.
- Publishing the real generated demo to GitHub Pages automatically.
- Uploading raw source video, trimmed clips, GVHMR checkpoints, SMPL-X assets,
  full GVHMR result directories, `.pt` files, logs, or rendered videos.
- Marking the real-conversion gate complete before an actual workflow run or
  local import proves `complete: true`.

## Stop Condition

Stopped when the optional self-hosted GPU workflow can validate/import the
returned JSON, run the strict audit, and optionally upload a generated real-demo
HTML artifact set. A later local GPU proof produced and validated the
non-fixture returned export through ignored `outputs/`; the workflow remains an
optional rerun/promotion path.
