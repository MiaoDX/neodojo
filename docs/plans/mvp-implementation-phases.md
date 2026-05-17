# MVP Implementation Plan Index

Status: SPLIT INTO EXECUTABLE PLAN FILES

## Purpose

This index keeps the source-video-to-teaching-demo MVP split into small,
executable plan files. Use this file for sequencing, shared constraints, and
handoff routing. Use the linked plan files as the execution source of truth for
each slice.

The current repo is still in bootstrap state. It has a fixture-only HTML demo
generator, `make test`, and `make demo-html`. It does not yet have a checked-in
GVHMR/GMR/simulator runtime pipeline, real Unitree G1 rendering, Viser UI,
install workflow, lint command, build command, or CI gate.

## Shared Goal

Move from the current fixture-only demo toward the first local Baduanjin
opening-form proof:

```text
local/user-supplied source video
  -> GVHMR SMPL-X output
  -> project-owned SMPL-X motion record
  -> SMPL-X teaching track
  -> GMR Unitree G1 visual track
  -> real Unitree G1 model rendering
  -> multi-view playback or Viser playback
  -> manual key-frame feedback proof
```

## Plan Sequence

| Order | Plan | Status | Purpose | Stop Condition |
| --- | --- | --- | --- | --- |
| 1 | [mvp-local-motion-contract.md](mvp-local-motion-contract.md) | done | Turn fixture motion and imported GVHMR-shaped outputs into one project-owned SMPL-X motion contract. | Fixture and external GVHMR teaching-joints JSON inputs both write the same SMPL-X motion-record and teaching-track manifests. |
| 2 | [mvp-g1-visual-track.md](mvp-g1-visual-track.md) | done | Add the Unitree G1 visual-track boundary: model provenance, derived track manifest, and scoring separation. | G1 assets/tracks are validated as derived visual artifacts and cannot become the scoring source. |
| 3 | [mvp-teaching-playback-demo.md](mvp-teaching-playback-demo.md) | done | Create the inspectable multi-view teaching playback with trajectories and one manual feedback proof. | The local `demo play` command consumes SMPL-X/G1 manifests and writes fixture-only HTML playback plus manifest evidence. |
| 4 | [mvp-g1-real-model-rendering.md](mvp-g1-real-model-rendering.md) | planned local non-GPU slice | Load a user-supplied real Unitree G1 URDF/MJCF and render robot evidence instead of the current canvas skeleton. | A local render manifest and screenshot/frame prove the real G1 model loads and remains non-scoring. |
| 5 | [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) | local prep ready; later GPU gate | Produce the first real GVHMR artifact for a short local Baduanjin clip on a GPU-capable machine. | Local prep writes source/trim metadata; final stop condition still requires a real GVHMR artifact imported through the same contracts. |

The numbered plans are semantically independent execution slices, not
necessarily separate GSD phases. The grouping boundary is:

1. local motion contract
2. G1 visual track
3. teaching-playback-demo
4. real Unitree G1 model rendering
5. later real conversion gate

The current local-first order intentionally puts real G1 model rendering before
the GPU conversion gate, so the right-side robot view can become real while the
source-video pipeline still waits for a GVHMR artifact.

## Shared Decisions

- SMPL-X is the teaching accuracy source.
- Unitree G1 is a derived visual and ecosystem track, not the scoring source.
- The MVP is kinematic playback only: no RL, sim2real, text-to-motion
  generation, or video-diffusion multi-view generation.
- Runtime commands must work with local/user-supplied video paths and must not
  commit source video, generated motion files, model checkpoints, rendered
  video, logs, or other large outputs.
- Official instructional videos are licensing-sensitive. Store source metadata
  and local paths, not bundled raw media.
- Local development targets a macOS Apple Silicon CPU machine. Heavy GPU/CUDA
  work must be represented by imported artifacts unless explicitly moved to a
  GPU machine.
- Each implementation slice that adds code must add its own command surface,
  focused tests, and docs updates.

## Local macOS CPU Policy

Allowed locally:

- package layout, CLI, config, schemas, manifests, and tests
- local video path validation, metadata, and frame-range checks
- imported GVHMR output validation
- SMPL-X motion-record normalization
- small-fixture forward kinematics and geometry checks
- CPU retargeting with fallback to externally produced GMR output
- lightweight MuJoCo/Genesis/Viser proof work when dependencies are stable
- real Unitree G1 model-load/render smoke tests from user-supplied assets
- low-resolution screenshots or frame verification

Not default local work:

- GVHMR full-video inference
- HAMER or other hand-refinement inference
- text-to-motion, video diffusion, or generative multi-view models
- RL training, sim2real policy work, or physics policy training
- high-quality ray-traced rendering or full-routine batch rendering

Any plan that depends on non-local work must provide an import path and a
fixture/dry-run mode.

## Bootstrap And Real-Artifact Lanes

Use two lanes throughout the MVP:

| Lane | Purpose | Artifact Source | Acceptance Role |
| --- | --- | --- | --- |
| Bootstrap fixture lane | Unblock schemas, manifests, retargeting, playback, and feedback before a GPU artifact exists. | Synthetic JSON fixtures, PBHC sample motion references, or other explicitly external sample artifacts. | Validates interfaces and playback behavior only. It cannot prove qigong correctness. |
| Real conversion lane | Prove neodojo can convert a local instructional clip into the canonical SMPL-X teaching record. | GVHMR run on Colab, RunPod, Modal, Hugging Face Jobs, or another GPU machine. | Required before calling the MVP an end-to-end neodojo proof. |

PBHC fixtures may be useful bootstrap data, but only as externally referenced
development samples. Do not commit copied `.pkl` or `.npz` files. Record source
URL, license, checksum, and local path in a manifest.

## Shared Compute Notes

GPU work is deliberately later than the local motion contract, G1 visual-track
contract, first playback contract, and real G1 model-rendering proof. For the
first real artifact, prefer GVHMR's upstream Colab or a short-lived
RunPod/PyTorch pod and manually export the result directory. For repeatable
development, create a project-owned Modal function, RunPod worker, or Hugging
Face Job that writes the exact import artifact shape. Treat production-style
APIs such as Replicate, RunPod Serverless, or Hugging Face Inference Endpoints
as later packaging decisions after the artifact contract is stable.

## GSD Handoff

No `.planning/` directory exists yet. After these plan files are reviewed and
accepted, use a manifest instead of manually creating `.planning/` files:

```yaml
docs:
  - path: docs/plans/mvp-implementation-phases.md
    type: PRD
  - path: docs/plans/mvp-local-motion-contract.md
    type: SPEC
  - path: docs/plans/mvp-g1-visual-track.md
    type: SPEC
  - path: docs/plans/mvp-teaching-playback-demo.md
    type: SPEC
  - path: docs/plans/mvp-g1-real-model-rendering.md
    type: SPEC
  - path: docs/plans/mvp-real-conversion-gate.md
    type: SPEC
  - path: docs/technical-roadmap.md
    type: DOC
  - path: docs/humanoid-platform-evaluation.md
    type: ADR
```

Then run:

```bash
gsd-ingest-docs --manifest <manifest> --mode new
gsd-plan-phase <created-phase> --prd docs/plans/mvp-implementation-phases.md
```

If GSD creates more than one phase, preserve the semantic grouping listed above
and keep subsystem details as tasks inside those phases.
