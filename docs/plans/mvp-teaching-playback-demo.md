# MVP Teaching Playback Demo Plan

Status: IMPLEMENTED LOCALLY

## Goal

Create the first user-visible teaching playback experience:

```text
SMPL-X track + G1 visual track + annotations
  -> synchronized multi-view playback
  -> selected joint trajectories
  -> timeline/key-frame navigation
  -> one SMPL-X-based key-frame feedback proof
```

This plan turns validated track artifacts into an inspectable teaching demo. It
must remain honest about which parts are fixture-only, real GVHMR-derived, or
real GMR-derived.

## Dependencies

- [mvp-g1-visual-track.md](mvp-g1-visual-track.md) completed or stable enough
  to provide SMPL-X and G1 track manifests.
- A tiny fixture or generated annotation file for local smoke tests.
- A small manual or detected annotation for one Baduanjin opening-form segment
  when real motion is available.
- Local simulator/rendering dependencies chosen for the first proof.

## Inputs

- SMPL-X teaching-track manifest.
- Unitree G1 visual-track manifest.
- Annotation file with key-frame and geometric constraints.
- Local simulator assets for MuJoCo or Genesis, or a simulator-light fixture
  rendering path.
- Existing fixture HTML demo behavior as the baseline UI shape.

## Outputs

- A documented playback command such as:

  ```bash
  PYTHONPATH=src python -m neodojo demo play --motion-record outputs/motion-contract --g1-track outputs/g1-visual/tracks/g1/manifest.json --out outputs/teaching-demo
  ```

- Front/side/top synchronized playback for SMPL-X and G1.
- Wrist, elbow, and knee trajectory overlays.
- Timeline controls and frame/key-frame navigation.
- One key-frame feedback proof based only on SMPL-X geometry.
- Screenshot or frame evidence for rendering/UI verification.
- Tests for annotation parsing and geometry-constraint calculation.
- Docs updates only after the playback command exists.

## Implemented Local Path

The first implementation uses the simulator-light fixture rendering path. It
does not load a real Unitree G1 mesh, MuJoCo, Genesis, or Viser. The command
loads the SMPL-X motion-record manifest and the derived G1 visual-track
manifest, verifies matching frame counts, keeps `scoring_source: smplx`, and
writes:

- `outputs/teaching-demo/index.html`
- `outputs/teaching-demo/manifest.json`

The manifest records the source manifests, rendered track ids, trajectory
joints, annotation manifest when supplied, key frame, and SMPL-X-based feedback
result.

Local UI verification captured
`outputs/teaching-demo/screenshot.png` with headless Chrome at 1440x1000. The
screenshot shows synchronized SMPL-X teacher and Unitree G1 visual views,
trajectory overlays, timeline controls, and the SMPL-X feedback panel.

## Rendering Path Decision

Choose one path before implementation:

| Option | Best Use | Tradeoff |
| --- | --- | --- |
| MuJoCo | Long-lived minimal dependency and standard robot/simulation ecosystem. | May require more hand-written camera/overlay work. |
| Genesis | Faster multi-camera experimentation and Apple-Silicon-friendly options. | Adds a broader framework dependency earlier. |
| Simulator-light fixture rendering | Keeps local proof tiny and dependency-light. | Does not prove real model rendering. |

The first implementation should avoid ray-traced or full-routine batch
rendering on the local macOS CPU machine.

## Implementation Tasks

- [x] Select the first rendering/playback path and record the reason in the plan or
  implementation notes.
- [x] Add annotation schema for manual key frames and geometric constraints.
- [x] Load SMPL-X and G1 track manifests through the same artifact contracts created
  by earlier plans.
- [x] Render SMPL-X as the primary teaching track and G1 as the visual companion.
- [x] Add synchronized front/side/top views.
- [x] Implement trajectory extraction and polyline overlays for selected joints.
- [x] Add timeline, key-frame navigation, and current-frame readout.
- [x] Compute one deterministic SMPL-X-based feedback result, such as shoulder
  clearance or elbow drop.
- [x] Verify actual frames or screenshots rather than relying only on logs.
- [x] Keep fixture-only and real-artifact labels visible in generated artifacts.
- [x] Update README/STATUS only after the command really exists and proof evidence
  is available.

## Acceptance Evidence

- The playback command starts locally against generated track artifacts.
- The fixture inspection path runs locally without GPU dependencies.
- At least one screenshot or frame shows synchronized SMPL-X and G1 playback.
- The trajectory overlay is visible and frame-aligned.
- One annotated key frame computes a deterministic SMPL-X-based feedback result.
- The demo does not imply webcam comparison, full automation, full-corpus
  support, source-video conversion, or real GMR output unless those artifacts
  are actually present.

## Non-Goals

- Broad automatic key-frame detection beyond the first narrow detector.
- Real-time student webcam comparison.
- LLM-generated motion.
- Video-diffusion multi-view generation.
- Heavy GPU/CUDA rendering or inference on the local macOS CPU machine.
- Sim2real control or physical robot execution.
- Full official video corpus processing.

## Stop Condition

Stop when one local playback path produces verified synchronized multi-view
evidence with trajectory overlays and one SMPL-X-based feedback proof.
