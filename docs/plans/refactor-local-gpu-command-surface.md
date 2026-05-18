---
refactor_scope: local-gpu-command-surface
status: DONE
accepted_severities:
  - P1
  - P2
last_verified: 2026-05-18
---

# Refactor Scope: Local GPU Command Surface

## Status

DONE

## Target

Make the public Makefile and `neodojo real-conversion` surface match the current
local-machine GPU posture. The repo should keep local source preparation,
returned GVHMR export inspection, returned artifact import, and real-demo audit
commands, but should not advertise or maintain Colab, online GPU provider,
external operator-package, self-hosted workflow, or real Pages-promotion
support.

## Accepted Severities

- P1: Public commands, CI lanes, or docs that claim online/external GPU support
  exists as a maintained path.
- P2: Target-local helper APIs, tests, and docs that only exist to support the
  removed online/operator command surface.

## Accepted Cleanup Checklist

- [x] Remove online/operator Make targets and variables while keeping local
      source prep, returned artifact intake, inspection, and audit targets.
- [x] Remove matching CLI subcommands and Python helper APIs for GPU input
      archive, run-request, Colab notebook, operator package, self-hosted route
      probe, acquisition preflight, and Pages promotion.
- [x] Remove CI workflow steps and workflow files for self-hosted GVHMR and real
      Pages promotion.
- [x] Update focused tests to cover the kept local GPU-prep/import/audit path and
      to assert the removed command names stay gone.
- [x] Update English and Chinese current docs so command lists and status claims
      match the reduced surface.

## Parked Cross-Seam / Future Ideas

- Add a true local GVHMR execution command once the repo owns a checked-in local
  runtime contract.
- Shrink the root README pair as part of the existing human-docs refactor gate.
- Rewrite historical MVP plan documents only if the project decides to treat
  completed planning records as mutable current documentation.

## Evidence Ladder

- L0 static: `make` target list, command-name search, syntax compile.
- L1 unit: focused `tests/test_demo_html.py` coverage for real-conversion local
  prep/import/audit and removed command names.
- L2 contract: `make check` and `make verify` after the reduced CI/Make surface
  is updated.

## Stop Condition

Stop when `make` exposes only the kept local commands, removed online/operator
command names no longer appear as supported Makefile/CLI/CI surfaces, focused
unit tests and project checks pass, and skipped gates are recorded here.

## Execution Log

- 2026-05-18: Opened for cleanup requested through `$intuitive-refactor`; scope
  accepted by user prompt to remove unnecessary Make commands, especially Colab
  and online GPU platform support.
- 2026-05-18: Removed Colab, hosted/provider, operator-package, self-hosted GPU,
  and real Pages-promotion Make/CLI/CI surfaces. Replaced the external runbook
  with `docs/runbooks/gvhmr-local-gpu.md`. Verified:
  `make lint`, `make test`, `make check`, `make verify`, and
  `PYTHONPATH=src .venv/bin/python -m neodojo real-conversion --help`.
- 2026-05-18: Rechecked the final public target list and strict local real gate.
  Verified: `make lint`, `make check`, `make test`, `make verify`,
  `make verify-real`, and
  `PYTHONPATH=src .venv/bin/python -m neodojo real-conversion prepare-gpu-run --help`.
- 2026-05-18: Tightened generated local GPU workspace wording so the README no
  longer calls the kept local run path a "GPU Handoff". Reverified:
  `make lint`, `make test`, `make verify`, and `make verify-real`.
