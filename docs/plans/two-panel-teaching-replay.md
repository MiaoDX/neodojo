---
status: IN_PROGRESS
created: 2026-05-18
last_verified: null
---

# Two-Panel Teaching Replay

## Goal

Publish a teaching HTML artifact for the Baduanjin real-conversion path where
the left half is the SMPL-X skeleton teaching track and the right half is the
Unitree G1 robot replay, both driven by the same synchronized timeline.

## Success Criteria

- `make demo-public` and `make demo-real` produce a public `index.html` whose
  first screen is an interactive split replay, not a static screenshot-only
  landing page.
- The HTML contains:
  - left panel: `SMPL-X skeleton teaching track`;
  - right panel: `Unitree G1 robot model replay`;
  - one shared timeline slider and play/pause control;
  - explicit SMPL-X scoring and G1 non-scoring labels.
- The public-demo manifest records a two-panel teaching HTML profile and enough
  metadata to tell whether the G1 replay uses a fixture-derived track, imported
  GMR track, fixture model descriptor, registered model descriptor, or MuJoCo
  render evidence.
- The smoke checker fails if the public HTML regresses to a non-interactive
  screenshot-only page.
- `make verify` passes.

## Current Inputs

- The repo can already import a returned GVHMR SMPL-X JSON export and generate a
  real-demo artifact under ignored `outputs/real-demo`.
- The current default G1 track is fixture-derived from SMPL-X, not true GMR.
- The current default G1 model descriptor is fixture-only unless the caller
  passes a registered model descriptor.
- The current render evidence is SVG schematic unless a local MuJoCo render path
  is explicitly used.

## Phases

1. Local GVHMR result intake: keep the current local GPU/import path and do not
   reintroduce hosted or Colab support.
2. SMPL-X teaching track: use the imported GVHMR motion record as the scoring
   source.
3. G1 replay input: support both the existing fixture-derived G1 visual track
   and caller-supplied imported GMR track; label the source honestly.
4. Teaching HTML: make the public artifact an interactive left/right replay
   with shared timeline controls.
5. Publication readiness: keep raw video and generated artifacts out of git,
   update docs/status, and verify with unit tests plus `make verify`.

## Non-Goals

- Do not claim a checked-in local GVHMR runtime exists until the repo owns that
  command and its dependencies.
- Do not claim GMR retargeting ran when the G1 track is fixture-derived.
- Do not claim MuJoCo/Genesis mesh rendering when the render backend is SVG
  schematic.
- Do not publish raw instructional video unless rights are confirmed.

## Verification

- Focused unit test for public-demo HTML labels, two-panel profile metadata,
  and smoke-check regression behavior.
- `make lint`
- `make test`
- `make verify`

## Execution Log

- 2026-05-18: Plan opened through `$intuitive-flow` for the requested completion
  standard: left SMPL-X skeleton teaching track, right Unitree G1 robot model
  replay, synchronized teaching HTML.
