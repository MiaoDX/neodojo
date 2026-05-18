---
refactor_scope: two-panel-teaching-replay
status: DONE
accepted_severities:
  - P0
  - P1
  - P2
created: 2026-05-18
last_verified: 2026-05-18
---

# Two-Panel Teaching Replay

## Status

DONE

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

## Target

The public teaching replay artifact produced by the local demo and real-demo
artifact-intake paths:

- `outputs/public-demo/index.html`
- `outputs/real-demo/public-demo/index.html`

## Accepted Severities

- P0: false-green public-demo verification that would pass without a two-panel
  teaching replay.
- P1: manifest or documentation drift that hides whether the G1 panel is
  fixture-derived, imported from GMR, or rendered by a real simulator.
- P2: stale public-demo layout code or command guidance that makes the static
  screenshot artifact look like the canonical teaching UI.

## Accepted Cleanup Checklist

- Public demo HTML is an interactive two-panel replay with SMPL-X on the left,
  G1 on the right, and one shared timeline.
- Public-demo manifest records the two-panel teaching HTML profile, panel
  layout, synchronization contract, and G1 source metadata.
- Smoke checks fail when the HTML falls back to the old screenshot-only shape.
- Real-demo and strict-audit manifests surface the same teaching HTML contract.
- README, Chinese README, and status documentation describe the current state
  without claiming true checked-in GVHMR/GMR/MuJoCo runtime support.

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

## Parked Cross-Seam / Future Ideas

- Add a first-class local GVHMR runner command instead of only importing a
  returned GVHMR SMPL-X JSON export.
- Add true local GMR retargeting as the default G1 replay source.
- Add MuJoCo or Genesis mesh-render evidence for the G1 panel.
- Publish the generated static artifact to a live Pages URL after Pages is
  configured and verified.

## Evidence Ladder

- L1/L2: focused unit tests for public-demo HTML labels, two-panel profile
  metadata, manifest contracts, strict-audit behavior, and smoke-check
  regression behavior.
- L2: project commands for fixture public-demo and real-demo artifact contracts.
- L3: browser smoke capture that loads the generated HTML and confirms both
  replay canvases render non-background pixels.

## Stop Condition

Stop when the accepted cleanup checklist is complete, `make verify`,
`make verify-real`, and `make demo-public-browser` pass, and no uncommitted
source changes remain except ignored generated artifacts.

## Verification

- Focused unit test for public-demo HTML labels, two-panel profile metadata,
  and smoke-check regression behavior.
- `make lint`
- `make test`
- `make verify`
- `make verify-real`
- `make demo-public-browser`

## Execution Log

- 2026-05-18: Plan opened through `$intuitive-flow` for the requested completion
  standard: left SMPL-X skeleton teaching track, right Unitree G1 robot model
  replay, synchronized teaching HTML.
- 2026-05-18: Implemented the public artifact as a two-panel canvas replay with
  synchronized play/pause and timeline controls.
- 2026-05-18: Added manifest metadata for the teaching HTML profile, panel
  layout, synchronization contract, and G1 replay/model/render provenance.
- 2026-05-18: Updated strict real-conversion audit and browser smoke checks to
  require the two-panel replay contract instead of accepting screenshot-only
  output.
- 2026-05-18: Updated README, README.zh.md, and STATUS.md to state that the
  teaching HTML exists while true checked-in GVHMR/GMR/MuJoCo runtime support
  remains future work.
- 2026-05-18: Verified with `make lint`, `make test`, `make check`,
  `make verify`, `make verify-real`, and `make demo-public-browser`.
