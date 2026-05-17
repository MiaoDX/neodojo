# MVP Implementation Phases

Status: DRAFT

## Goal

Turn the research in `docs/technical-roadmap.md` and
`docs/humanoid-platform-evaluation.md` into standalone implementation phases
that can be executed without claiming a runtime pipeline before it exists.

The first milestone remains one local Baduanjin opening-form clip moving through
the smallest useful path:

```text
local source video
  -> GVHMR SMPL-X output
  -> shared motion record
  -> SMPL-X teaching track
  -> GMR Unitree G1 visual track
  -> multi-view rendering or Viser playback
  -> manual key-frame feedback proof
```

## Source Decisions

- SMPL-X is the teaching accuracy source.
- Unitree G1 is a derived visual and ecosystem track, not the scoring source.
- The MVP is kinematic playback only: no RL, sim2real, text-to-motion
  generation, or video-diffusion multi-view generation.
- Local development targets a macOS Apple Silicon CPU machine. Heavy GPU/CUDA
  work must be offloaded or represented by imported artifacts unless explicitly
  approved for a different machine.
- Official videos are licensing-sensitive. Runtime commands should work with
  local/user-supplied video paths and should not commit source or generated
  media.
- The repo is currently docs-only. Each code phase must introduce its own
  command surface, focused tests, and docs updates.

## Local macOS CPU Policy

The current local machine is suitable for orchestration, schema validation,
manifest generation, lightweight kinematics, CPU retargeting, annotation
parsing, geometry checks, Viser playback, and low-resolution screenshots.

The current local machine should not run these workloads by default:

- GVHMR full video inference.
- HAMER or other hand-refinement inference.
- text-to-motion, video diffusion, or generative multi-view models.
- RL training, sim2real policy work, or physics policy training.
- high-quality ray-traced rendering or full-routine batch rendering.

Any phase that depends on one of those workloads must support an import path for
precomputed external artifacts and a dry-run or fixture mode for local tests.

## Compute Requirements Matrix

| Workload | GPU Need | Local macOS CPU Role | GPU Machine Role | MVP Decision |
| --- | --- | --- | --- | --- |
| Package layout, CLI, config, schemas, manifests, tests | None | Primary development target | Optional CI mirror | Run locally. |
| Local video path validation, metadata, frame-range checks | None | Primary development target | Optional | Run locally without committing video. |
| GVHMR full video inference | Strongly GPU-recommended; CUDA/NVIDIA is the practical target | Import and validate precomputed output only | Run inference and export SMPL-X artifacts | Offload by default. Do not make local GVHMR inference a required acceptance step. |
| GVHMR training or benchmark reproduction | GPU required and out of MVP scope | None | Research-only | Do not include in MVP. |
| DPVO visual odometry inside GVHMR | CUDA-oriented optional dependency | Avoid by default; prefer static-camera skip path when valid | Only if camera motion requires it | Not part of the first Baduanjin proof. |
| HAMER or other hand-refinement inference | GPU-recommended | Import only if a follow-up artifact exists | Run inference for hand-detail follow-up | Park until after the first demo. |
| SMPL-X motion-record normalization | None once GVHMR output exists | Primary development target | Optional | Run locally. |
| SMPL-X forward kinematics and geometry constraints | None for small fixtures/demo clips | Primary development target | Optional for batch jobs | Run locally. |
| GMR retargeting to Unitree G1 | CPU-suitable; upstream reports CPU retargeting speed | Try locally, with external-output import fallback | Useful if macOS dependency issues appear | Prefer local CPU execution, but do not block on macOS-only dependency failures. |
| MuJoCo lightweight playback and screenshots | No discrete GPU required, but uses local graphics/OpenGL context | Primary target for low-resolution verification | Optional for Linux parity | Run locally for smoke/demo proof. |
| Genesis lightweight simulation/rendering | Optional; supports CPU and Apple Metal, GPU helps speed | Allowed for small scenes if dependencies are stable | Better for heavy simulation/rendering | Use only CPU/Apple-Silicon-friendly settings locally. |
| Viser synchronized playback UI | None | Primary development target | Optional | Run locally. |
| Full-routine batch rendering or high-quality ray tracing | GPU or GPU workstation strongly preferred | Avoid | Run batch render jobs | Do not require for MVP acceptance. |
| Text-to-motion, video diffusion, or generative multi-view models | GPU required | None | Research-only | Excluded from MVP. |
| RL training, sim2real control, policy learning | GPU required | None | Research-only | Excluded from MVP. |

## Development Machine Recommendation

Keep the core development loop on this macOS machine for now. The current MVP
phases are deliberately structured so that the Mac owns code quality,
interfaces, tests, manifests, imported-artifact validation, CPU retargeting,
Viser playback, and low-resolution visual proof.

Use a GPU machine as an artifact producer when one of these becomes active:

- repeatedly generating GVHMR outputs from source videos;
- debugging GVHMR/HAMER internals instead of only importing their outputs;
- processing multiple full routines instead of one short proof clip;
- producing high-resolution rendered videos;
- validating Linux/CUDA dependency compatibility before release.

Move the whole development task to a GPU machine only if the next execution
slice is primarily GVHMR/HAMER integration or batch rendering. For Phase 1 and
most of Phase 2, moving the whole repo would add environment churn without
removing much risk. A hybrid workflow is cleaner: GPU machine produces
artifact directories, this repo validates and consumes them.

## GPU Artifact Platform Options

There is no confirmed official Modal, RunPod, or Replicate template dedicated to
GVHMR or HaMeR. Treat those platforms as generic GPU execution backends that can
run a project-owned wrapper.

| Platform | Official/Ready-Made Fit | Best Use In This Project | Caveats |
| --- | --- | --- | --- |
| GVHMR Colab linked from upstream README | Closest official quick-start path for GVHMR | Manual one-off proof that a local source clip can produce SMPL-X artifacts | Notebook workflow, not a durable artifact API. Needs care around video/model licensing and artifact export. |
| GVHMR Hugging Face Space linked from upstream README | Upstream-linked demo, but currently not a reliable backend | Only useful as a reference for setup/download steps | Current Space page shows runtime error; do not make it an execution dependency. |
| HaMeR Hugging Face Space by the HaMeR author | Author-published demo, but currently not a reliable backend | Reference setup for later hand-refinement follow-up | Current Space page shows build error; HaMeR is parked after the first demo. |
| Modal | No GVHMR-specific official template found; official GPU functions and custom images are available | Best candidate for a small Python GPU artifact function: input video/artifact path -> output GVHMR result directory | We must write and own the Modal app, dependency image, persistent volume layout, and artifact contract. |
| RunPod Pod | No GVHMR-specific official template found; official PyTorch and ComfyUI templates exist | Good for interactive debugging on Ubuntu/CUDA, especially when upstream repos need shell access | Pod lifecycle and storage must be managed; dependency drift between GPU types is possible. |
| RunPod Serverless | No GVHMR-specific official endpoint found; custom Docker worker is supported | Useful after the wrapper is stable and we want an API for batch artifact production | Requires packaging a custom worker/container and handling cold starts plus large video/model artifacts. |
| RunPod ComfyUI + community ComfyUI-MotionCapture | Official ComfyUI base, community GVHMR node | Fast manual experiment if a visual node workflow is desired | Community node, not a stable project contract; adds ComfyUI/SAM workflow complexity not needed for Phase 1. |
| Replicate | No public GVHMR/HaMeR model found; custom Cog models are supported | Possible API wrapper once the artifact contract is stable | We must build a Cog model; less convenient for iterative shell debugging than a GPU pod. |
| Hugging Face Spaces GPU | Official GPU Spaces infrastructure; GVHMR and HaMeR have upstream/author Spaces, but both currently show errors | Useful for public demos after the pipeline is stable, or as setup references | Spaces are demo-oriented; default disk is ephemeral unless storage is attached. Do not rely on the existing Spaces as CI/production artifact runners. |
| Hugging Face Jobs | Official one-off job runner with CPU/GPU hardware flavors and Docker/Space images | Good fit for batch artifact production once wrapped as a script | Newer workflow; still requires our wrapper, artifact storage convention, and credentials. |
| Hugging Face Inference Endpoints | Official dedicated endpoints with custom containers and GPU hardware | Possible private API once the artifact contract is stable | Better for serving repeated requests than ad-hoc research debugging; custom container work still required. |

Recommended order:

1. For first artifact: use GVHMR's upstream Colab or a short-lived RunPod
   PyTorch pod and manually export the GVHMR result directory.
2. For repeatable development: create a project-owned Modal function, RunPod
   custom worker, or Hugging Face Job that writes the exact Phase 1 import
   artifact shape.
3. For production-style API: consider Replicate, RunPod Serverless, or Hugging
   Face Inference Endpoints only after the input/output contract is stable.

## Motion Artifact Bootstrap Strategy

The video-to-motion conversion must not disappear from the plan. It is the
product-critical bridge from source video to SMPL-X teaching data. It should not
block every downstream engineer, either.

Use two lanes:

| Lane | Purpose | Artifact Source | Acceptance Role |
| --- | --- | --- | --- |
| Bootstrap fixture lane | Unblock motion-record, retargeting, rendering, UI, and geometry-feedback development before a GPU machine is ready | Synthetic tiny JSON fixtures, PBHC example motion files, or other explicitly external sample artifacts | Validates interfaces and playback behavior only. It cannot prove qigong correctness. |
| Real conversion lane | Prove neodojo can convert a local instructional clip into the canonical SMPL-X teaching record | GVHMR run on Colab, RunPod, Modal, Hugging Face Jobs, or another GPU machine | Required before calling the MVP an end-to-end neodojo proof. |

PBHC is a good bootstrap source because its official repo includes small example
motion files under `example/motion_data/` and visualization/processing tools
under `robot_motion_process/`. These files are not qigong standards and the
repo is CC BY-NC 4.0, so treat them as development fixtures only:

- do not commit copied `.pkl` or `.npz` files into this repo;
- record source URL, license, checksum, and local path in a manifest;
- store downloaded samples only in ignored local artifact directories;
- keep user-facing claims clear that PBHC fixtures are placeholder motion data,
  not neodojo's teaching source.

The first real conversion gate should be deliberately small:

```text
one short local Baduanjin clip
  -> GVHMR on GPU
  -> exported SMPL-X artifact directory
  -> imported by `neodojo motion-record create`
  -> same downstream commands already proven by fixture lane
```

Do not wait for the real conversion gate before building the downstream command
surface. Do require the real conversion gate before marking the full
source-video-to-teaching-demo milestone complete.

## Immediate Local-First Execution Slice

Before setting up GPU infrastructure, make the flow runnable on this macOS
machine with fixture artifacts. This is a Phase 1/2/3 smoke path, not a separate
GSD phase.

### Local Goal

Prove the project command surface and artifact contracts end to end without
running heavy GPU inference locally:

```text
synthetic or PBHC-sourced fixture manifest
  -> neodojo motion record manifest
  -> SMPL-X/robot-track placeholder or imported track manifest
  -> local playback/inspection smoke command
  -> one geometry-feedback calculation on fixture joints
```

### Local Tasks

- Add the minimal package, CLI, and test command.
- Add a fixture import mode that can read a tiny synthetic fixture first.
- Add an optional PBHC sample manifest path for externally downloaded examples,
  with URL/license/checksum recorded and no `.pkl`/`.npz` committed.
- Generate a project-owned motion-record manifest from fixture input.
- Generate a project-owned track manifest from fixture or imported track input.
- Add a local smoke playback/inspection command that works with small fixture
  arrays and does not require simulator-heavy rendering.
- Add one deterministic geometry check against fixture joints.
- Document that this smoke path validates plumbing only, not qigong accuracy.

### Local Acceptance Evidence

- A project-specific test command exists and passes on this Mac.
- A fixture-based command writes motion-record and track manifests under an
  ignored output directory.
- A local playback/inspection smoke command can load those manifests.
- One geometry-feedback calculation runs from fixture data.
- No raw videos, model checkpoints, generated `.pkl`/`.npz`, rendered videos, or
  large outputs are committed.

### GPU Follow-Up Gate

After the local fixture path works, produce the first real external artifact on
a GPU machine:

```text
short local Baduanjin clip
  -> GVHMR runner on GPU
  -> exported SMPL-X artifact directory
  -> `neodojo motion-record create --gvhmr-output ...`
  -> same local track/playback commands
```

The GPU gate should reuse the same import contract proven by the local fixture
path. If the GPU artifact requires changing downstream code, the local contract
was too narrow and must be fixed before continuing.

## Phase Granularity

Use three coherent delivery phases rather than one phase per subsystem:

1. `motion-record-proof` creates the first reproducible command surface and
   canonical SMPL-X motion contract.
2. `dual-track-playback-proof` proves SMPL-X and G1 can be derived from the same
   motion record while preserving the scoring boundary.
3. `teaching-playback-demo` turns the tracks into an inspectable teaching
   experience with multi-view playback and a small manual feedback proof.

Work that would create extra phases is kept as tasks inside these phases or
parked until after the first end-to-end demo.

## Phase 1: Motion Record Proof

### Goal

Create the first runnable, reproducible pipeline entrypoint for one local source
clip and normalize GVHMR output into a project-owned SMPL-X motion record.

### Inputs

- A local user-supplied video path.
- Optional clip metadata for routine name, form name, fps, and frame range.
- A documented external GVHMR output path. Local GVHMR execution is optional and
  must be guarded so it is not the default path on the macOS CPU machine.
- Optional bootstrap fixture manifest for synthetic or PBHC-sourced sample
  motion data, used only to unblock local interface and playback development.

### Outputs

- Package metadata and a documented command, for example:

  ```bash
  neodojo motion-record create --video <local.mp4> --out <motion-dir>
  ```

- A small motion-record manifest that points to generated artifacts without
  committing them.
- A schema or typed data model for the canonical SMPL-X teaching record.
- A fixture import mode that can validate placeholder/sample motion artifacts
  without pretending they are qigong teaching data.
- A local smoke path that works before GPU artifacts exist.
- Validation that rejects missing files, unsupported formats, ambiguous frame
  ranges, and output paths under git-tracked source directories.
- README/STATUS updates that describe only the command that actually exists.

### Implementation Tasks

- Add minimal Python package layout and CLI entrypoint.
- Add config handling for local external-tool paths without hard-coding machine
  locations.
- Add an adapter that imports an existing GVHMR result by default, with any
  direct GVHMR invocation behind an explicit opt-in flag.
- Add a bootstrap fixture importer for tiny synthetic fixtures or externally
  downloaded PBHC sample motion manifests.
- Normalize GVHMR output into a stable internal record shape.
- Build the local smoke path first, using fixture data to exercise the same
  manifest and validation contracts the real GVHMR import will use.
- Define the first real conversion gate: one short local Baduanjin clip
  converted on a GPU machine and imported through the same interface.
- Add artifact-policy checks so raw videos, generated motions, logs, and large
  outputs stay out of git.
- Add focused tests for validation, schema loading, and artifact-policy
  behavior.

### Acceptance Evidence

- A narrow test command passes for the new module.
- A dry-run or fixture-based run writes a manifest and validates the expected
  record shape.
- The fixture smoke path runs on the macOS machine without GPU dependencies.
- A real GVHMR import contract is documented well enough that a GPU-produced
  artifact directory can be dropped in later without changing downstream code.
- Docs state the command, inputs, outputs, and artifact policy without claiming
  rendering, UI, or scoring exists.

### Non-Goals

- G1 retargeting.
- Simulator rendering.
- Viser UI.
- Local full-video GVHMR inference on the macOS CPU machine.
- Treating PBHC or synthetic fixtures as qigong teaching data.
- Full official video corpus processing.
- Automated qigong feedback.

## Phase 2: Dual-Track Playback Proof

### Goal

Prove that one canonical SMPL-X motion record can drive both the SMPL-X teaching
track and the Unitree G1 visual track while keeping scoring logic attached only
to SMPL-X.

### Inputs

- A validated Phase 1 motion record.
- Locally installed GMR for CPU retargeting, or a documented external GMR output
  path if local installation is unavailable.
- Fixture track input for the local-first smoke path before GMR or GPU artifacts
  are ready.
- Local SMPL-X/UHC and Unitree G1 model assets as user-provided dependencies.

### Outputs

- A documented command, for example:

  ```bash
  neodojo tracks build --motion-record <motion-dir> --out <tracks-dir>
  ```

- A SMPL-X teaching-track artifact or manifest.
- A GMR-derived Unitree G1 visual-track artifact or manifest.
- A fixture-track manifest mode for local plumbing tests.
- A lightweight comparison report with frame counts, fps, joint coverage,
  dropped-frame status, and known loss points such as torso and hand DOF.
- Tests for track manifest creation and scoring-boundary enforcement.

### Implementation Tasks

- Add SMPL-X teaching-track loader and forward-kinematics boundary.
- Add GMR adapter for `unitree_g1` retargeting.
- Add fixture-track manifest generation before requiring GMR installation.
- Record provenance for external model assets and command versions.
- Add validation that G1 artifacts cannot be used as the teaching scoring
  source.
- Add basic foot/contact and hand-coverage diagnostics from the research docs.
- Keep local execution bounded to CPU retargeting, manifest/report generation,
  and small fixtures.
- Update docs with the exact new command and the SMPL-X/G1 responsibility split.

### Acceptance Evidence

- A focused test command passes for track building and manifest validation.
- A local fixture or dry-run can build both track manifests from one motion
  record.
- The fixture track path is marked non-authoritative and cannot be used as
  qigong teaching evidence.
- The report explicitly shows SMPL-X as canonical and G1 as derived.

### Non-Goals

- Multi-camera rendered videos.
- Browser UI.
- Real-time webcam comparison.
- HAMER hand refinement.
- GPU model inference or training.
- Changing the humanoid platform decision.

## Phase 3: Teaching Playback Demo

### Goal

Create the first user-visible teaching demo: synchronized SMPL-X and G1 playback
with multi-view inspection, trajectory overlays, and a small manually anchored
feedback proof.

### Inputs

- Phase 2 SMPL-X and G1 track manifests.
- Local simulator assets for MuJoCo or Genesis, using CPU/Apple-Silicon-friendly
  settings and low-resolution verification output.
- A small manual annotation file for one Baduanjin opening-form segment.
- A tiny fixture annotation file for the local-first smoke path.

### Outputs

- A documented playback command, for example:

  ```bash
  neodojo demo play --tracks <tracks-dir> --annotations <annotations.json>
  ```

- Front/side/top synchronized playback for SMPL-X and G1.
- Wrist, elbow, and knee trajectory overlays.
- Timeline controls and frame/key-frame navigation.
- One manual key-frame feedback proof based on SMPL-X geometry, such as
  shoulder height or elbow drop.
- A simulator-light fixture inspection path that can run before full rendering
  is available.
- Screenshot or frame evidence for rendering/UI verification.

### Implementation Tasks

- Choose the first rendering path for the demo: MuJoCo for long-lived minimal
  dependency, or Genesis if multi-camera setup speed dominates. Avoid
  ray-traced or full-routine batch rendering on the local macOS CPU machine.
- Add Viser playback for synchronized views and timeline controls.
- Render SMPL-X as the primary teaching track and G1 as the visual companion.
- Implement trajectory extraction and polyline overlays for selected joints.
- Add a minimal annotation schema for manual key frames and geometric
  constraints.
- Add a fixture-only inspection command before requiring full simulator assets.
- Add tests for annotation parsing and geometry-constraint calculations.
- Verify actual frames or screenshots rather than relying only on logs.
- Update README/STATUS only after the demo command really exists.

### Acceptance Evidence

- The playback command starts locally against generated Phase 2 artifacts.
- The fixture inspection command runs locally without GPU dependencies.
- At least one screenshot or frame shows synchronized SMPL-X and G1 playback.
- The trajectory overlay is visible and frame-aligned.
- One manually annotated key frame computes a deterministic SMPL-X-based
  feedback result.
- Docs do not imply webcam comparison, full automation, or full-corpus support.

### Non-Goals

- Automatic key-frame detection.
- Real-time student webcam comparison.
- LLM-generated motion.
- Video-diffusion multi-view generation.
- Heavy GPU/CUDA rendering or inference on the local macOS CPU machine.
- Sim2real control or physical robot execution.

## Parked Follow-Ups

- Full official routine corpus processing after licensing and artifact policy
  are clarified.
- HAMER or other hand-specific refinement for gestures such as hook hand and
  standing palm.
- Automatic term-to-geometry dictionary expansion beyond one manually anchored
  proof.
- Online/student comparison mode.
- GitHub issue split if multiple agents need independently grabbable work.
- GSD handoff after this plan is reviewed and accepted.

## Suggested GSD Handoff

No `.planning/` directory exists yet. After review, use an ingest manifest
instead of manually creating `.planning/` files:

```yaml
docs:
  - path: docs/plans/mvp-implementation-phases.md
    type: PRD
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

If the GSD roadmap creates more than one phase from this plan, preserve the
three delivery phases above as the grouping boundary and keep smaller subsystem
work as tasks inside those phases.
