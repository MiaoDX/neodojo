# MVP Local Motion Contract Plan

Status: IMPLEMENTED

## Goal

Create the local motion contract that every later slice consumes:

```text
synthetic fixture or imported GVHMR-shaped output
  -> project-owned SMPL-X motion record
  -> SMPL-X teaching track manifest
  -> HTML fixture path consuming the same contract
```

This plan is local-first and GPU-free. It keeps the current synthetic demo
useful while making it look like a future real GVHMR import from the outside.

## Current State

- `make test` runs focused unit tests for the current fixture generator.
- `make demo-html` writes `outputs/html-demo/index.html` and
  `outputs/html-demo/manifest.json`.
- The generated demo is synthetic and marked `fixture_only: true`.
- The SMPL-X and G1-like tracks are generated in memory by
  `src/neodojo/demo_html.py`.
- There is no explicit motion-record manifest or stable import contract yet.

## Inputs

- Current synthetic fixture generation.
- Optional fixture metadata for routine, form, fps, and frame count.
- Optional imported GVHMR-shaped output directory or file, used only for schema
  validation until the later GPU gate produces a real artifact.
- Artifact policy from `AGENTS.md`, `STATUS.md`, and `ARCHITECTURE.md`.

## Outputs

- A documented local command surface for writing a motion record from fixture
  data, such as:

  ```bash
  PYTHONPATH=src python -m neodojo motion-record create --out outputs/motion-contract
  PYTHONPATH=src python -m neodojo motion-record create --from-gvhmr-json path/to/gvhmr-smplx-joints.json --out outputs/motion-contract
  ```

- A project-owned SMPL-X motion-record manifest under ignored `outputs/`.
- A SMPL-X teaching-track manifest under ignored `outputs/`.
- A generated HTML demo that consumes the manifest-shaped data.
- Validation that SMPL-X is the only allowed scoring source.
- Focused tests for manifest writing/loading, scoring-source enforcement,
  artifact-policy checks, and current `make demo-html` behavior.

## Implemented Local Path

The command supports two local CPU-side inputs:

- `--fixture synthetic` writes synthetic fixture motion into the canonical
  motion-record and SMPL-X teaching-track manifests.
- `--from-gvhmr-json <path>` imports an external GVHMR SMPL-X teaching-joints
  JSON export into the same manifests.

The JSON import expects precomputed teaching joints, not a raw GVHMR `.pt`
file. Raw GVHMR execution and raw `.pt` export remain part of the later GPU
gate.

## Implementation Tasks

- Define the minimal motion-record manifest:
  - `fixture_only`
  - `source_type`
  - `routine`
  - `form`
  - `fps`
  - `frame_count`
  - `joint_set`
  - `scoring_source`
  - `provenance`
  - relative data-file paths
- Define the minimal SMPL-X teaching-track manifest:
  - `track_id`
  - `source_motion_record`
  - `role`
  - `scoring_allowed`
  - `frame_count`
  - `fps`
  - relative data-file paths
- Split fixture data generation from HTML rendering so the same data can be
  serialized, loaded, and embedded.
- Keep direct GVHMR execution out of scope; accept only fixture or already
  imported GVHMR-shaped data.
- Add clear validation errors for missing files, unsupported formats, ambiguous
  frame ranges, and unsafe output paths.
- Preserve `make test` and `make demo-html`.
- Update README/STATUS only if a new user-facing command exists or the current
  next safe task changes.

## Acceptance Evidence

- `make test` passes.
- `make demo-html` still writes the self-contained HTML fixture demo.
- A fixture-based command writes a motion-record manifest and SMPL-X
  teaching-track manifest under ignored `outputs/`.
- An external GVHMR teaching-joints JSON export can write the same
  motion-record and SMPL-X teaching-track manifest shape.
- The generated root manifest marks the artifact as `fixture_only: true` and
  `scoring_source: smplx`.
- Tests prove that scoring remains attached to SMPL-X.
- No raw videos, generated `.pkl`/`.npz`, model checkpoints, rendered videos,
  or large outputs are committed.

## Non-Goals

- Real GVHMR conversion or GPU work.
- Unitree G1 model loading.
- GMR retargeting.
- Simulator rendering.
- Viser UI.
- Proving qigong correctness.

## Stop Condition

Stop when the current fixture demo is backed by explicit local motion/track
contracts and those contracts are tested.
