# MVP Real Demo Pages Promotion Plan

Status: IMPLEMENTED GUARDED MANUAL PROMOTION; REAL ARTIFACT STILL EXTERNAL

## Goal

Add a guarded manual path for replacing the fixture-only GitHub Pages demo with
a validated real-demo artifact after the self-hosted GPU workflow has produced
and uploaded that artifact.

This closes the publication gap after
`mvp-gvhmr-self-hosted-real-demo-intake.md`: the real demo can be promoted
without copying media, checkpoints, SMPL-X assets, logs, or raw GVHMR result
files into Pages. The default push/PR public-demo workflow stays fixture-only
until a human explicitly promotes a verified real artifact.

## Dependencies

- [mvp-gvhmr-self-hosted-gpu-workflow.md](mvp-gvhmr-self-hosted-gpu-workflow.md)
  can run the packaged GVHMR wrapper on a user-managed GPU runner.
- [mvp-gvhmr-self-hosted-real-demo-intake.md](mvp-gvhmr-self-hosted-real-demo-intake.md)
  can validate/import the returned GVHMR export, run the strict audit, and
  upload `neodojo-self-hosted-real-demo`.
- [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) owns the real
  artifact completion criteria and strict audit semantics.
- [mvp-rerun-pages-release.md](mvp-rerun-pages-release.md) owns the existing
  fixture Pages publication lane and live URL.

## Inputs

- A successful self-hosted GPU workflow run ID.
- The short-lived `neodojo-self-hosted-real-demo` artifact from that run.
- Repository variable `NEODOJO_DEPLOY_REAL_PAGES=true`.
- Manual workflow confirmation that replacing the fixture Pages artifact is
  intended.

## Outputs

- `.github/workflows/promote-real-demo-pages.yml`, a `workflow_dispatch`-only
  promotion workflow.
- A staged Pages artifact copied from the validated real-demo `public-demo/`
  directory.
- `promotion-manifest.json` inside the staged Pages artifact, recording source
  run ID, artifact name, real GVHMR import proof, strict audit proof, and the
  public-demo aggregate fixture flag.

## Execution Tasks

- [x] Add a manual `promote-real-demo-pages` workflow with no push or pull
  request triggers.
- [x] Require `source_run_id`, a real-demo artifact name, explicit
  `confirm_replace_fixture_pages`, and `NEODOJO_DEPLOY_REAL_PAGES=true`.
- [x] Download the named artifact from the selected run with read-only Actions
  access.
- [x] Validate the downloaded artifact before upload:
  - real-demo manifest schema is `neodojo.real_conversion_demo.v1`;
  - `real_gvhmr_artifact_imported` is true;
  - source materialization and GVHMR export are not fixture-only;
  - strict audit manifest schema is `neodojo.real_conversion_audit.v1`;
  - strict audit reports `status: real_demo_verified`, `complete: true`, and
    `blocked: false`;
  - public-demo manifest keeps SMPL-X as the scoring source and disallows G1
    scoring;
  - expected HTML, scene, `.rrd`, and screenshot files exist and are nonblank.
- [x] Re-run `neodojo demo smoke` against the staged public-demo before upload.
- [x] Reject promotion inputs whose paths include media, checkpoints, SMPL-X
  asset markers, `.pt`, `.pkl`, or `.npz` files.
- [x] Add focused tests that the promotion workflow is manual, gated, validates
  real-artifact evidence, and avoids unsafe upload paths.
- [x] Update STATUS, README, README.zh, the external GPU runbook, and the MVP
  plan index without claiming that a real artifact exists.

## Acceptance Evidence

- The workflow has only `workflow_dispatch` triggers.
- Promotion cannot run unless both `confirm_replace_fixture_pages` and
  `NEODOJO_DEPLOY_REAL_PAGES=true` are set.
- The workflow validates real-demo, public-demo, and strict audit manifests
  before uploading a Pages artifact.
- The workflow runs `PYTHONPATH=src python -m neodojo demo smoke` against the
  staged real-demo Pages directory.
- The workflow upload path is the generated public-demo directory only, with a
  promotion manifest added for auditability.
- `make test` covers the workflow trigger, gating, validation, and unsafe path
  exclusions.
- `make check` includes this plan through the MVP index.

## Non-Goals

- Running GVHMR from the promotion workflow.
- Publishing any artifact that has not already passed the self-hosted
  returned-artifact intake and strict audit.
- Automatically replacing fixture Pages from push, pull request, or the
  self-hosted GPU workflow.
- Requiring a non-fixture G1 companion before a real SMPL-X/GVHMR teaching
  artifact can be promoted. The staged `promotion-manifest.json` records when
  the aggregate public-demo fixture flag remains true because the visual G1
  companion still uses fixture-derived assets.
- Uploading raw source media, trimmed clips, checkpoints, SMPL-X assets,
  `hmr4d_results.pt`, logs, rendered videos, `.pkl`, `.npz`, or full GVHMR
  result directories.

## Stop Condition

Stopped when a manually dispatched workflow can download the validated
self-hosted real-demo artifact, prove the real GVHMR import and strict audit,
smoke-check the staged public demo, and deploy only that generated public-demo
directory to GitHub Pages when the operator explicitly enables replacement.
