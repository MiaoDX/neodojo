# G1 Profile-Driven Execution Architecture

Status: Implemented

## Goal

Make G1 execution evidence profile-driven so the repo can distinguish these
claims in code and generated artifacts:

```text
fixture schematic evidence
  != registered MuJoCo mesh evidence
  != actual Unitree G1 MuJoCo replay from imported GMR joint angles
  != public HTML consumption of that actual replay
```

The architecture must preserve the core neodojo boundary: SMPL-X is the
teaching/scoring source, and G1 is a visual companion.

## Source Evidence

- [`docs/adr/0003-profile-driven-execution-evidence.md`](../adr/0003-profile-driven-execution-evidence.md)
- [`docs/plans/refactor-real-g1-model-replay.md`](refactor-real-g1-model-replay.md)
- [`docs/plans/mvp-simulator-mesh-rendering.md`](mvp-simulator-mesh-rendering.md)
- [`docs/plans/two-panel-teaching-replay.md`](two-panel-teaching-replay.md)
- [`ARCHITECTURE.md`](../../ARCHITECTURE.md)
- [`STATUS.md`](../../STATUS.md)

## Intuitive-Flow Route

Current state: the named ADR and plan were absent from the current worktree, but
the surrounding G1 replay/render/audit code existed.

Selected path: reconstruct the missing docs as the source of truth, then
implement the bounded command/manifest/test surface inline.

Autoplan precheck: no existing autoplan artifact or canonical plan body existed
for these file names. This plan records the accepted scope directly and keeps
the implementation bounded to the existing G1 evidence blast radius.

GSD handoff: not used. The repo has no `.planning/` tree, and this is a bounded
local implementation over existing modules rather than a new milestone phase.

## Requirements

1. Define a versioned execution-profile schema for G1 evidence claims.
2. Add named profiles for schematic evidence, MuJoCo mesh evidence, actual
   MuJoCo replay evidence, and public actual-replay consumption.
3. Write the render execution profile into G1 render manifests.
4. Allow CLI/Make callers to request an explicit profile and fail when required
   evidence is missing.
5. Propagate the public G1 replay profile into the public-demo manifest.
6. Require satisfied actual-replay profiles in the strict real-conversion audit.
7. Keep fixture/demo lanes dependency-light.
8. Keep SMPL-X as `scoring_source` and `g1_scoring_allowed: false`.

## Implementation

Added `src/neodojo/execution_profiles.py` with:

- `neodojo.execution_profile.v1`
- `g1_schematic_evidence`
- `g1_mujoco_mesh_evidence`
- `g1_actual_mujoco_replay_evidence`
- `g1_public_actual_mujoco_replay_evidence`
- shared profile builders and a strict satisfaction helper

Updated G1 rendering:

- `neodojo render g1 --execution-profile ...`
- `neodojo render mujoco-g1 --execution-profile ...`
- MuJoCo render manifests now include `execution_profile`.
- Explicit actual replay requests fail unless the manifest proves a non-fixture
  model, non-fixture imported GMR track, imported joint-angle qpos application,
  nonblank changing replay frames, and SMPL-X scoring boundary.

Updated public and real-demo evidence:

- `teaching_html.g1_replay.execution_profile` records whether the public page is
  schematic or actual replay consumption.
- `real-conversion import-demo --g1-execution-profile ...` passes the requested
  profile into generated render evidence.
- `make mujoco-g1-render G1_EXECUTION_PROFILE=...` and `make demo-real
  G1_EXECUTION_PROFILE=...` expose the same profile boundary.

Updated strict audit:

- `make verify-real` now treats old actual-replay-shaped manifests without a
  satisfied actual replay execution profile as incomplete.
- The audit manifest surfaces `render_execution_profile_satisfied` and
  `public_execution_profile_satisfied`.

## Acceptance Criteria

- G1 render manifests contain `execution_profile`.
- Public-demo manifests contain `teaching_html.g1_replay.execution_profile`.
- A public demo cannot claim actual G1 replay from a render manifest that lacks
  a satisfied actual replay profile.
- Strict real-conversion audit requires satisfied render and public actual replay
  profiles before `real_demo_verified`.
- Fixture-only public-demo generation remains valid and schematic.
- No raw videos, model assets, checkpoints, generated motion files, rendered
  frames, logs, or large outputs are committed.

## Verification

Focused tests:

```bash
PYTHONPATH=src python -m unittest tests.test_demo_html
```

Project syntax/import check:

```bash
make lint
```

Broader verification remains:

```bash
make test
make verify
make verify-real REAL_ARTIFACT_SOURCE_MATERIALIZATION=... REAL_ARTIFACT_GVHMR_JSON=... REAL_ARTIFACT_OUT=...
```

Implementation evidence from this workspace:

- `make test` passes 105 unit tests.
- `make verify` passes lint, quality check, unit tests, wheel build,
  fixture public-demo generation/smoke, real GPU-prep smoke, real artifact
  intake smoke, and non-strict real-conversion audit.
- The generated fixture `outputs/g1-render/manifest.json`,
  `outputs/public-demo/manifest.json`, and `outputs/public-demo/scene.json`
  contain satisfied `g1_schematic_evidence` execution profiles.
- An explicit fixture request for
  `--execution-profile g1_actual_mujoco_replay_evidence` fails with the missing
  actual-replay checks listed by the profile validator.

## Parked Work

- Add separate profiles for roboharness checkpoint reports if those reports
  become strict publication evidence.
- Add Genesis-specific profile IDs when a Genesis renderer exists.
- Add profile summaries to routine overview pages if users need to compare many
  phase reports by evidence class.
