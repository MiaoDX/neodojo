# MVP Implementation Plan Index

Status: SPLIT INTO EXECUTABLE PLAN FILES

## Purpose

This index keeps the source-video-to-teaching-demo MVP split into small,
executable plan files. Use this file for sequencing, shared constraints, and
handoff routing. Use the linked plan files as the execution source of truth for
each slice.

The current repo is still in bootstrap state. It has a fixture-only HTML demo
generator, `make test`, `make demo-html`, `make demo-public`, versioned local
artifact contracts, a normalized imported-GMR G1 track boundary, native GMR
pickle normalization, an SMPL-X surface proxy, G1 SVG/HTML render evidence,
optional MuJoCo render evidence, optional true Rerun SDK `.rrd` export,
an optional first Viser local runtime, optional source-media probing, local
source-media materialization handoff, a fixture-only static public-demo fallback
artifact, a generated roboharness-style capture bundle boundary, and a GitHub
Actions workflow with verified fixture-only Pages publication plus optional
browser-rendered public-demo screenshot capture. It
does not yet have a checked-in GVHMR/GMR execution pipeline, simulator runtime
pipeline, full licensed SMPL-X mesh generation, hosted/live-client Viser
capture, or broad static-analysis/release gates beyond the minimal `make lint` and
`make build` surface.

## Shared Goal

Move from the current fixture-only demo toward the first local Baduanjin
opening-form proof:

```text
local/user-supplied source video
  -> GVHMR SMPL-X output
  -> project-owned SMPL-X motion record
  -> SMPL-X teaching track
  -> imported or fixture Unitree G1 visual track
  -> real Unitree G1 model rendering
  -> hardened artifact contracts
  -> source clip materialization handoff
  -> Rerun public demo artifact
  -> CI-published fixture demo
  -> generated multi-camera capture bundle
  -> optional browser-rendered public-demo capture
  -> multi-view playback or Viser playback
  -> detected key-frame feedback proof
```

## Plan Sequence

| Order | Plan | Status | Purpose | Stop Condition |
| --- | --- | --- | --- | --- |
| 1 | [mvp-local-motion-contract.md](mvp-local-motion-contract.md) | done | Turn fixture motion and imported GVHMR-shaped outputs into one project-owned SMPL-X motion contract. | Fixture and external GVHMR teaching-joints JSON inputs both write the same SMPL-X motion-record and teaching-track manifests. |
| 2 | [mvp-g1-visual-track.md](mvp-g1-visual-track.md) | done | Add the Unitree G1 visual-track boundary: model provenance, derived track manifest, and scoring separation. | G1 assets/tracks are validated as derived visual artifacts and cannot become the scoring source. |
| 3 | [mvp-gmr-import-track.md](mvp-gmr-import-track.md) | implemented | Import externally produced GMR Unitree G1 JSON into the same non-scoring G1 visual-track contract. | A normalized imported GMR track with joint angles can feed the existing render/playback/public-demo consumers while SMPL-X remains the scoring source. |
| 4 | [mvp-teaching-playback-demo.md](mvp-teaching-playback-demo.md) | done | Create the inspectable multi-view teaching playback with trajectories and one manual feedback proof. | The local `demo play` command consumes SMPL-X/G1 manifests and writes fixture-only HTML playback plus manifest evidence. |
| 5 | [mvp-keyframe-feedback-detection.md](mvp-keyframe-feedback-detection.md) | implemented first detector | Generate an explicit SMPL-X annotation manifest for the opening-form feedback key frame. | `make demo-public` uses generated annotations instead of an implicit last-frame anchor. |
| 6 | [mvp-g1-real-model-rendering.md](mvp-g1-real-model-rendering.md) | implemented local SVG evidence; simulator mesh rendering remains follow-on | Load a user-supplied real Unitree G1 URDF/MJCF and render robot evidence instead of the current canvas skeleton. | A local render manifest and front/side/top SVG frame evidence prove the registered descriptor path remains non-scoring. |
| 7 | [mvp-pipeline-contract-hardening.md](mvp-pipeline-contract-hardening.md) | implemented | Version and validate source, motion, teaching, G1, render, playback, annotation, and public-demo contracts before broader orchestration. | Existing fixture paths and future import paths pass through explicit versioned manifest boundaries with source-media provenance and local video-sync metadata. |
| 8 | [mvp-visualization-and-public-demo.md](mvp-visualization-and-public-demo.md) | implemented with static fallback | Define one internal scene/timeline contract and make a fixture-only public demo artifact. | A fixture-only `.rrd` fallback artifact, static viewer page, public-demo manifest, and SVG screenshot can be generated and visually smoke-tested. |
| 9 | [mvp-devex-ci-surface.md](mvp-devex-ci-surface.md) | implemented with browser capture CI verified | Add one-command public-demo orchestration and CI artifact/Page publishing for the fixture lane. | A clean checkout can regenerate, validate, browser-smoke, upload, and publish the non-GPU fixture demo without tracking generated outputs. |
| 10 | [mvp-lint-build-surface.md](mvp-lint-build-surface.md) | implemented | Add the minimal lint/build command surface and all-in-one local verification target. | `make verify` runs lint, plan quality checks, tests, wheel build, and public-demo generation without tracking generated artifacts. |
| 11 | [mvp-source-media-probing.md](mvp-source-media-probing.md) | implemented metadata probe | Record optional ffprobe metadata for local source videos without copying media. | Source prep records probe success/failure, duration, resolution, codec, and frame-rate metadata when available. |
| 12 | [mvp-source-media-materialization.md](mvp-source-media-materialization.md) | implemented local handoff | Turn source prep plus a local video into a dry-run or ffmpeg-backed trimmed-clip/reference-frame handoff. | A source-materialization manifest records source validation, commands, generated outputs when available, and the GVHMR input handoff path without committing media. |
| 13 | [mvp-roboharness-capture-boundary.md](mvp-roboharness-capture-boundary.md) | implemented generated bundle and browser public-demo capture; CI verified; roboharness/simulator recorder remains follow-on | Collect public-demo, browser capture, Viser preview, and G1 render artifacts into one roboharness-style multi-camera evidence manifest. | `make demo-public` writes a validated generated capture bundle, and `make demo-public-browser` adds optional real browser screenshot evidence without claiming direct roboharness/simulator recording. |
| 14 | [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) | local prep/materialization ready; later GPU gate | Produce the first real GVHMR artifact for a short local Baduanjin clip on a GPU-capable machine. | Local prep writes source/trim metadata and source materialization can prepare the trimmed input; final stop condition still requires a real GVHMR artifact imported through the hardened contracts. |

## Future Gap Plans

These plans are not required to keep the current fixture public-demo lane
working. They turn remaining `STATUS.md` gaps into explicit execution sources
of truth for the next waves.

| Plan | Status | Gap Covered |
| --- | --- | --- |
| [mvp-simulator-mesh-rendering.md](mvp-simulator-mesh-rendering.md) | implemented optional MuJoCo command, real G1 asset smoke, and GMR qpos application | MuJoCo render command, real Unitree G1 mesh proof, and imported GMR joint-angle qpos application. |
| [mvp-native-gmr-runner.md](mvp-native-gmr-runner.md) | implemented first pickle adapter; local GMR execution remains external | Native GMR robot-motion pickle parsing beyond normalized JSON import. |
| [mvp-smplx-body-surface-playback.md](mvp-smplx-body-surface-playback.md) | implemented surface proxy, licensed-asset boundary, and parameter import; full mesh rendering remains follow-on | Dependency-light SMPL-X surface proxy, local-only licensed asset descriptor, imported SMPL-X parameter boundary, and future mesh/body-model playback. |
| [mvp-smplx-licensed-mesh-rendering.md](mvp-smplx-licensed-mesh-rendering.md) | blocked on local licensed assets and renderer choice | Full licensed SMPL-X mesh/body-model playback beyond the capsule proxy, local asset descriptor, and imported parameter boundary. |
| [mvp-viser-multicamera-runtime.md](mvp-viser-multicamera-runtime.md) | implemented first optional server, camera/anchor controls, and generated multi-camera preview evidence | Local Viser runtime, camera/annotation controls, and dependency-light front/side/top visual smoke workflow. |
| [mvp-viser-production-teaching-ui.md](mvp-viser-production-teaching-ui.md) | implemented first production review-loop contract and controls | Production local Viser teaching UX beyond the first optional runtime controls and generated previews. |
| [mvp-rerun-pages-release.md](mvp-rerun-pages-release.md) | implemented optional SDK export and verified live Pages publication | True Rerun SDK `.rrd` export and verified live GitHub Pages URL. |
| [mvp-roboharness-simulator-recorder.md](mvp-roboharness-simulator-recorder.md) | follow-on; needs recorder target decision and local runtime assets | Direct roboharness, simulator, or live-runtime recorder evidence beyond generated capture bundles and public-demo browser screenshots. |
| [mvp-feedback-routine-review.md](mvp-feedback-routine-review.md) | implemented | Broader key-frame/posture feedback and routine-level review. |
| [mvp-gvhmr-source-validation.md](mvp-gvhmr-source-validation.md) | implemented validator; blocked on a real GVHMR export for final proof | Validation that imported GVHMR artifacts match the materialized source clip and trim. |
| [mvp-quality-release-surface.md](mvp-quality-release-surface.md) | implemented first quality gate | Project-owned static quality check for MVP plan links and scaffolding beyond the minimal lint/build commands. |

The numbered plans are semantically independent execution slices, not
necessarily separate GSD phases. The grouping boundary is:

1. local motion contract
2. G1 visual track
3. imported GMR G1 track boundary
4. teaching-playback-demo
5. key-frame feedback detection
6. real Unitree G1 model rendering
7. pipeline contract hardening
8. visualization and public demo publishing
9. developer experience and CI surface
10. lint/build command surface
11. source media probing
12. source media materialization
13. generated multi-camera capture bundle plus optional browser public-demo
    capture
14. later real conversion gate

The current local-first order intentionally puts real G1 model rendering before
the GPU conversion gate, so the right-side robot view can become real while the
source-video pipeline still waits for a GVHMR artifact. The non-GPU hardening,
public-demo, and CI slices also stay before the GPU conversion gate so the real
artifact has stable contracts and a publish lane when it arrives.

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
- optional local source-video ffprobe metadata
- optional local source-video trim and reference-frame materialization
- imported GVHMR output validation
- imported GMR Unitree G1 track validation
- SMPL-X motion-record normalization
- minimal lint/build command checks
- deterministic SMPL-X key-frame annotation detection
- small-fixture forward kinematics and geometry checks
- CPU retargeting with fallback to externally produced GMR output
- lightweight MuJoCo/Genesis/Viser proof work when dependencies are stable
- real Unitree G1 model-load/render smoke tests from user-supplied assets
- low-resolution screenshots or frame verification
- Rerun fixture export, static viewer generation, and GitHub Pages artifact
  staging
- generated multi-camera capture bundle manifests from existing local evidence
- optional browser-rendered public-demo screenshot capture
- CI orchestration for fixture-only tests, generated demo artifacts, and visual
  smoke checks

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

The public demo lane starts from the bootstrap fixture lane. It publishes the
fixture-only public artifact through GitHub Pages at
`https://miaodx.com/neodojo/` and must remain visibly labeled as fixture-only
until a real GVHMR artifact enters the same contracts.

## Shared Compute Notes

GPU work is deliberately later than the local motion contract, G1 visual-track
contract, first playback contract, and G1 render-evidence proof. For the
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
  - path: docs/plans/mvp-gmr-import-track.md
    type: SPEC
  - path: docs/plans/mvp-teaching-playback-demo.md
    type: SPEC
  - path: docs/plans/mvp-keyframe-feedback-detection.md
    type: SPEC
  - path: docs/plans/mvp-g1-real-model-rendering.md
    type: SPEC
  - path: docs/plans/mvp-pipeline-contract-hardening.md
    type: SPEC
  - path: docs/plans/mvp-visualization-and-public-demo.md
    type: SPEC
  - path: docs/plans/mvp-devex-ci-surface.md
    type: SPEC
  - path: docs/plans/mvp-lint-build-surface.md
    type: SPEC
  - path: docs/plans/mvp-source-media-probing.md
    type: SPEC
  - path: docs/plans/mvp-source-media-materialization.md
    type: SPEC
  - path: docs/plans/mvp-real-conversion-gate.md
    type: SPEC
  - path: docs/plans/mvp-simulator-mesh-rendering.md
    type: SPEC
  - path: docs/plans/mvp-native-gmr-runner.md
    type: SPEC
  - path: docs/plans/mvp-smplx-body-surface-playback.md
    type: SPEC
  - path: docs/plans/mvp-smplx-licensed-mesh-rendering.md
    type: SPEC
  - path: docs/plans/mvp-viser-multicamera-runtime.md
    type: SPEC
  - path: docs/plans/mvp-viser-production-teaching-ui.md
    type: SPEC
  - path: docs/plans/mvp-roboharness-capture-boundary.md
    type: SPEC
  - path: docs/plans/mvp-roboharness-simulator-recorder.md
    type: SPEC
  - path: docs/plans/mvp-rerun-pages-release.md
    type: SPEC
  - path: docs/plans/mvp-feedback-routine-review.md
    type: SPEC
  - path: docs/plans/mvp-gvhmr-source-validation.md
    type: SPEC
  - path: docs/plans/mvp-quality-release-surface.md
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
