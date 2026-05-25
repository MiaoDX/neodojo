# ADR 0003: Profile-Driven Execution Evidence

Status: Accepted and implemented

Date: 2026-05-22

## Context

neodojo has several G1 evidence paths:

- fixture SVG schematic evidence for dependency-light demos
- registered G1 MuJoCo mesh evidence
- actual G1 MuJoCo replay from imported GMR Unitree G1 joint angles
- public teaching HTML that may consume either schematic evidence or actual
  replay media

Before this decision, the actual-replay boundary depended on a spread of booleans
such as `actual_g1_model_replay`, `model_fixture_only`, `track_fixture_only`,
`changed_frame_check`, and public-demo media fields. Those booleans were useful,
but they made the claim hard to audit as one execution contract.

The project must keep these claims fail-closed:

- SMPL-X remains the teaching and scoring source.
- G1 is visual-only.
- Fixture tracks, fixture descriptors, static mesh renders, and schematic
  canvases must not be accepted as actual Unitree G1 replay evidence.
- Public HTML can claim actual G1 replay only when it consumes replay frames or
  an encoded replay video backed by the render evidence.

## Decision

Use versioned execution profiles in generated manifests. A profile is a compact
claim plus the required checks that prove or reject the claim.

The first schema is `neodojo.execution_profile.v1`. The implemented G1 profiles
are:

- `g1_schematic_evidence`
- `g1_mujoco_mesh_evidence`
- `g1_actual_mujoco_replay_evidence`
- `g1_public_actual_mujoco_replay_evidence`

Render commands now write an `execution_profile` block into the G1 render
manifest. Public teaching HTML writes the public G1 replay profile into
`teaching_html.g1_replay.execution_profile`. The strict real-conversion audit
requires the actual MuJoCo replay render profile and public consumption profile
before reporting `real_demo_verified`.

CLI and Makefile callers may request a profile explicitly. An explicit actual
replay profile fails if the evidence does not satisfy the profile.

## Consequences

Positive:

- The actual G1 replay claim is now a named contract instead of an informal
  combination of manifest fields.
- Strict verification can identify whether the missing piece is the imported GMR
  track, registered MJCF descriptor, MuJoCo replay frame sequence, or public
  media consumption.
- Future renderers can add profiles without weakening the current fail-closed
  G1 boundary.

Tradeoffs:

- Existing hand-written or old generated manifests that claim actual replay but
  lack a satisfied profile are no longer enough for strict verification.
- The profile schema adds duplicate-looking evidence fields, but the duplication
  is deliberate: raw facts stay in renderer/public manifests, while the profile
  states which facts are required for a specific claim.

## Non-Goals

- Using G1 as a scoring source.
- Treating a neutral MuJoCo mesh render as actual replay.
- Requiring MuJoCo, roboharness, GMR, or robot assets for fixture demos.
- Replacing existing public-demo or real-conversion manifest schemas.

## Evidence

Implementation plan:

- [`docs/plans/g1-profile-driven-execution-architecture.md`](../plans/g1-profile-driven-execution-architecture.md)

Primary code:

- `src/neodojo/execution_profiles.py`
- `src/neodojo/g1_render.py`
- `src/neodojo/public_demo.py`
- `src/neodojo/real_conversion.py`
