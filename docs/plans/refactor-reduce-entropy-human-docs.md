---
refactor_scope: reduce-entropy-human-docs
status: DONE
accepted_severities:
  - P1
  - P2
last_verified: 2026-05-18
---

# Reduce Entropy: Human Docs

## Status

DONE

## Goal

Make the current project truth easy to find without requiring humans or agents to
re-read the full research notes on every visit.

## Scope

- Add a compact root `STATUS.md` for current state, runnable commands, blockers,
  and next work.
- Add a compact root `ARCHITECTURE.md` for the intended MVP pipeline, subsystem
  boundaries, data policy, and proof boundaries.
- Link the new current-truth docs from both README files.
- Reclassify the long technical docs as background research/evidence.
- Update agent startup pointers so future agents start from the compact human
  surface before deep research notes.

## Out Of Scope

- Runtime package layout.
- Install, test, lint, or CI command creation.
- Moving existing research docs.
- Creating data, generated motions, rendered assets, or model artifacts.

## Evidence

- `README.md` was 717 lines and `README.zh.md` was 610 lines before this pass,
  mostly because they duplicated current status, command runbooks, CI evidence,
  and implementation details already tracked in `STATUS.md`.
- `STATUS.md`, `ARCHITECTURE.md`, `.github/workflows/public-demo.yml`, and
  `Makefile` are the current evidence for README claims about bootstrap state,
  CI-generated fixture demo artifacts, and runnable commands.
- `README.md` already linked the fixture-only Pages demo, but did not present it
  as a compact CI-generated demo surface.

## Checklist

- [x] Create `STATUS.md`.
- [x] Create `ARCHITECTURE.md`.
- [x] Update `README.md`.
- [x] Update `README.zh.md`.
- [x] Update agent startup pointers.
- [x] Verify links and whitespace.
- [x] Shrink `README.md` into a compact L0 orientation page.
- [x] Keep the CI-generated fixture demo link/screenshot explicit in
      `README.md`.
- [x] Align `README.zh.md` with the smaller English README.

## Parked Items

- Decide whether to add `docs/human/README.md` once there is more human-facing
  material than the root README, status, and architecture docs can carry.
- Resolve local empty `video/` and `videos/` directories against the intended
  `data/raw/` convention before adding any source-video workflow.
- Add package metadata, focused tests, and real command docs in the same change
  that introduces runtime code.

## Evidence Ladder

- L0 static docs: README links, headings, and drift against `STATUS.md`,
  `ARCHITECTURE.md`, `.github/workflows/public-demo.yml`, and `Makefile`.

## Stop Condition

The English and Chinese README files are compact L0 orientation docs, both
mention the CI-generated fixture demo, and static link/command-name checks pass.

## Execution Log

- 2026-05-18: Reopened for the README shrink requested through
  `$intuitive-refactor`.
- 2026-05-18: Replaced `README.md` and `README.zh.md` with compact L0
  orientation docs, keeping the CI-generated fixture demo link, generated
  artifact list, screenshot, and bootstrap caveats.
- 2026-05-18: Verified with `make check`, README reference grep, Make target
  grep, and local file existence checks for linked docs and workflow.
