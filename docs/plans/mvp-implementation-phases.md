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
an optional first Viser local runtime, optional source-media probing with
custom local-source provenance, local source-media materialization handoff, a
copyable ignored GPU input bundle with explicit media inclusion, a CI-safe
GPU-side runner script for external GVHMR execution, a metadata-only GPU input
transfer archive smoke, a one-command local media archive prep target, a
reproducible local/provider GPU execution probe, a
tracked external-GPU operator runbook, a fixture-only static public-demo
fallback artifact, a generated roboharness-style capture bundle boundary,
optional MuJoCo simulator recorder-capture integration, and a GitHub Actions
workflow with verified fixture-only Pages publication, optional browser-rendered
public-demo screenshot capture, metadata-only real-handoff smoke artifact
upload, metadata-only GPU input bundle/archive smoke upload, and a
real-conversion completion audit artifact, plus an opt-in strict
`make verify-real` completion gate and an optional manual self-hosted GPU
workflow for external GVHMR execution plus returned-artifact intake, and an
optional guarded manual workflow for promoting a validated real-demo artifact to
GitHub Pages, plus generated external GPU run-request and Colab operator
notebook artifacts. It
does not yet have a checked-in local GVHMR/GMR execution environment, completed
simulator runtime pipeline, built-in official SMPL-X body-model renderer,
hosted/live-client Viser capture, or broad static-analysis/release gates beyond
the minimal `make lint` and `make build` surface.

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
| 9 | [mvp-devex-ci-surface.md](mvp-devex-ci-surface.md) | implemented with browser capture and real/GPU smoke artifact CI verified | Add one-command public-demo orchestration and CI artifact/Page publishing for the fixture lane. | A clean checkout can regenerate, validate, browser-smoke, upload, and publish the non-GPU fixture demo, plus upload metadata-only real-handoff/GPU input/GPU run-request/GPU probe artifacts, fixture-only real-artifact intake smoke outputs, and real-conversion audit status without tracking generated outputs. |
| 10 | [mvp-lint-build-surface.md](mvp-lint-build-surface.md) | implemented | Add the minimal lint/build command surface and all-in-one local verification target. | `make verify` runs lint, plan quality checks, tests, wheel build, public-demo generation, dry-run real-handoff smoke, GPU bundle/archive/run-request/Colab-notebook/probe smoke, fixture-only real-artifact intake smoke, and real-conversion completion audit without tracking generated artifacts. |
| 11 | [mvp-source-media-probing.md](mvp-source-media-probing.md) | implemented metadata probe and custom local-source prep | Record optional ffprobe metadata for local source videos without copying media. | Source prep records probe success/failure, duration, resolution, codec, and frame-rate metadata when available, and custom local sources can derive source duration/resolution without an official source-index row. |
| 12 | [mvp-source-media-materialization.md](mvp-source-media-materialization.md) | implemented local handoff, materialized local candidate, and GPU input bundle | Turn source prep plus a local video into a dry-run or ffmpeg-backed trimmed-clip/reference-frame handoff. | A source-materialization manifest records source validation, commands, generated outputs when available, and the GVHMR input handoff path without committing media; an ignored local Bilibili candidate handoff reports `ready_for_gpu`, and a transfer bundle reports `ready_for_gpu_with_media`. |
| 13 | [mvp-roboharness-capture-boundary.md](mvp-roboharness-capture-boundary.md) | implemented generated bundle and browser public-demo capture; CI verified | Collect public-demo, browser capture, Viser preview, G1 render, and optional recorder artifacts into one roboharness-style multi-camera evidence manifest. | `make demo-public` writes a validated generated capture bundle, and `make demo-public-browser` adds optional real browser screenshot evidence without claiming direct roboharness integration. |
| 14 | [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) | local prep/materialization/custom-source handoff/gpu-input/gpu-runner/transfer-archive/run-request/Colab-notebook/operator-package/gpu-execution-probe/export-helper/result-inspection/validation/import-demo/intake-smoke/audit ready; later GPU gate | Produce the first real GVHMR artifact for a short local Baduanjin clip on a GPU-capable machine. | Local prep writes source/trim metadata, source materialization can prepare the trimmed input, `make real-handoff` can build the local GPU handoff in one command for official-index or custom local sources, `make gpu-handoff` can repackage existing materialization with the GPU-side exporter helper and runner, `make gpu-input-bundle` and `make gpu-input-archive` can package transfer files plus media when explicit, `make real-gpu-run-request` can prepare both the ignored transfer archive and operator request from a local video, `make real-gpu-colab-notebook` can prepare the archive/request/notebook handoff together, `make real-gpu-operator-package` can collocate the archive/request/notebook into one operator package, `make gpu-execution-probe` can classify local/provider GPU readiness without running GVHMR, `make gvhmr-inspect` can inspect returned result structure, `make demo-real` / `make real-artifact-intake` can validate/import a returned export, `make real-artifact-intake-smoke` covers that wrapper with fixture-only inputs, `make real-conversion-audit` records the incomplete external-artifact blocker, and `make verify-real` fails until the real non-fixture demo exists; final stop condition still requires a real GVHMR artifact from a GPU run. |

## Future Gap Plans

These plans are not required to keep the current fixture public-demo lane
working. They turn remaining `STATUS.md` gaps into explicit execution sources
of truth for the next waves.

| Plan | Status | Gap Covered |
| --- | --- | --- |
| [mvp-simulator-mesh-rendering.md](mvp-simulator-mesh-rendering.md) | implemented optional MuJoCo command, real G1 asset smoke, and GMR qpos application | MuJoCo render command, real Unitree G1 mesh proof, and imported GMR joint-angle qpos application. |
| [mvp-native-gmr-runner.md](mvp-native-gmr-runner.md) | implemented first pickle adapter; local GMR execution remains external | Native GMR robot-motion pickle parsing beyond normalized JSON import. |
| [mvp-smplx-body-surface-playback.md](mvp-smplx-body-surface-playback.md) | implemented surface proxy, licensed-asset boundary, parameter import, and external mesh-frame import | Dependency-light SMPL-X surface proxy, local-only licensed asset descriptor, imported SMPL-X parameter boundary, and optional mesh surface playback. |
| [mvp-smplx-licensed-mesh-rendering.md](mvp-smplx-licensed-mesh-rendering.md) | implemented external licensed mesh-frame import; official body-model execution remains external | Licensed SMPL-X mesh surface playback through local externally generated mesh-frame evidence. |
| [mvp-viser-multicamera-runtime.md](mvp-viser-multicamera-runtime.md) | implemented first optional server, camera/anchor controls, and generated multi-camera preview evidence | Local Viser runtime, camera/annotation controls, and dependency-light front/side/top visual smoke workflow. |
| [mvp-viser-production-teaching-ui.md](mvp-viser-production-teaching-ui.md) | implemented first production review-loop contract and controls | Production local Viser teaching UX beyond the first optional runtime controls and generated previews. |
| [mvp-rerun-pages-release.md](mvp-rerun-pages-release.md) | implemented optional SDK export and verified live Pages publication | True Rerun SDK `.rrd` export and verified live GitHub Pages URL. |
| [mvp-roboharness-simulator-recorder.md](mvp-roboharness-simulator-recorder.md) | implemented first MuJoCo simulator recorder contract | Direct roboharness, simulator, or live-runtime recorder evidence beyond generated capture bundles and public-demo browser screenshots. |
| [mvp-feedback-routine-review.md](mvp-feedback-routine-review.md) | implemented | Broader key-frame/posture feedback and routine-level review. |
| [mvp-gvhmr-source-validation.md](mvp-gvhmr-source-validation.md) | implemented validator; blocked on a real GVHMR export for final proof | Validation that imported GVHMR artifacts match the materialized source clip and trim. |
| [mvp-gvhmr-export-adapter.md](mvp-gvhmr-export-adapter.md) | implemented GPU-side export helper; real artifact still external | Standalone GPU-side helper packaged with the handoff to convert GVHMR `hmr4d_results.pt` plus licensed SMPL-X assets into the neodojo import schema. |
| [mvp-gvhmr-gpu-runner-surface.md](mvp-gvhmr-gpu-runner-surface.md) | implemented CI-safe GPU runner packaging; real artifact still external | Executable GPU-side runner script packaged with handoff/input bundles and smoke-tested without media or GVHMR execution. |
| [mvp-gvhmr-gpu-transfer-archive.md](mvp-gvhmr-gpu-transfer-archive.md) | implemented CI-safe transfer archive; real artifact still external | Metadata-only and media-including GPU input bundle archives for transfer to the external GPU machine. |
| [mvp-real-gpu-archive-command.md](mvp-real-gpu-archive-command.md) | implemented one-command media archive/request prep; real artifact still external | Single local make target that prepares the ignored media-containing GPU transfer archive from a local source video, plus a wrapper that also writes the generated operator request. |
| [mvp-real-gpu-colab-command.md](mvp-real-gpu-colab-command.md) | implemented one-command archive/request/Colab prep; real artifact still external | Single local make target that prepares the ignored transfer archive, generated operator request, and Colab operator notebook from a local source video. |
| [mvp-gvhmr-external-gpu-runbook.md](mvp-gvhmr-external-gpu-runbook.md) | implemented tracked runbook; real artifact still external | Durable operator checklist for unpacking the archive, running GVHMR on a CUDA machine, and validating the returned export locally. |
| [mvp-gvhmr-external-run-request.md](mvp-gvhmr-external-run-request.md) | implemented generated run request; real artifact still external | Concise generated operator request manifest/README from an existing GPU input archive, with archive hash, required GPU assets, return commands, a one-command archive/request wrapper, and smoke coverage. |
| [mvp-gvhmr-colab-operator-notebook.md](mvp-gvhmr-colab-operator-notebook.md) | implemented generated notebook; real artifact still external | Colab-ready operator notebook generated from a run-request manifest, with checksum verification, guarded GVHMR execution, returned JSON download, and smoke coverage. |
| [mvp-gvhmr-operator-package.md](mvp-gvhmr-operator-package.md) | implemented collocated package and package archive; real artifact still external | Validated package directory and single-file transfer archive that collocate the archive, run request, Colab notebook, and package README/manifest for the external GPU operator. |
| [mvp-gvhmr-self-hosted-gpu-workflow.md](mvp-gvhmr-self-hosted-gpu-workflow.md) | implemented optional workflow; real artifact still external | Manual GitHub Actions workflow for user-managed self-hosted GPU runners that can run the packaged GVHMR wrapper from a prepared archive or collocated operator package. |
| [mvp-gvhmr-self-hosted-real-demo-intake.md](mvp-gvhmr-self-hosted-real-demo-intake.md) | implemented optional workflow intake; real artifact still external | Same manual self-hosted workflow validates/imports the returned export, runs the strict audit, and can upload generated real-demo evidence. |
| [mvp-real-demo-pages-promotion.md](mvp-real-demo-pages-promotion.md) | implemented guarded manual promotion; real artifact still external | Manual GitHub Pages replacement workflow that downloads a validated self-hosted real-demo artifact, revalidates real GVHMR and strict audit evidence, smoke-checks the staged public demo, and deploys only when explicitly confirmed. |
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
  - path: docs/plans/mvp-gvhmr-export-adapter.md
    type: SPEC
  - path: docs/plans/mvp-gvhmr-gpu-runner-surface.md
    type: SPEC
  - path: docs/plans/mvp-gvhmr-gpu-transfer-archive.md
    type: SPEC
  - path: docs/plans/mvp-real-gpu-archive-command.md
    type: SPEC
  - path: docs/plans/mvp-real-gpu-colab-command.md
    type: SPEC
  - path: docs/plans/mvp-gvhmr-external-gpu-runbook.md
    type: SPEC
  - path: docs/plans/mvp-gvhmr-external-run-request.md
    type: SPEC
  - path: docs/plans/mvp-gvhmr-colab-operator-notebook.md
    type: SPEC
  - path: docs/plans/mvp-gvhmr-operator-package.md
    type: SPEC
  - path: docs/plans/mvp-gvhmr-self-hosted-gpu-workflow.md
    type: SPEC
  - path: docs/plans/mvp-gvhmr-self-hosted-real-demo-intake.md
    type: SPEC
  - path: docs/plans/mvp-real-demo-pages-promotion.md
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
