# Reduce Entropy: Human Docs

Status: DONE

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

- The repo currently has only docs and guidance files tracked.
- No package metadata, tests, build scripts, or CI config exist.
- `README.md`, `README.zh.md`, `docs/technical-roadmap.md`, and
  `docs/humanoid-platform-evaluation.md` carry overlapping current-truth claims.
- `AGENTS.md` correctly warns that the repo is bootstrap/docs-only, but its read
  order points directly to long research docs.

## Checklist

- [x] Create `STATUS.md`.
- [x] Create `ARCHITECTURE.md`.
- [x] Update `README.md`.
- [x] Update `README.zh.md`.
- [x] Update agent startup pointers.
- [x] Verify links and whitespace.

## Parked Items

- Decide whether to add `docs/human/README.md` once there is more human-facing
  material than the root README, status, and architecture docs can carry.
- Resolve local empty `video/` and `videos/` directories against the intended
  `data/raw/` convention before adding any source-video workflow.
- Add package metadata, focused tests, and real command docs in the same change
  that introduces runtime code.
