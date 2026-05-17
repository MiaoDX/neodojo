# MVP Teaching Playback Demo Plan

Status: QUEUED AFTER G1 VISUAL TRACK

## Goal

Create the first user-visible teaching playback experience:

```text
SMPL-X track + G1 visual track + annotations
  -> synchronized multi-view playback
  -> selected joint trajectories
  -> timeline/key-frame navigation
  -> one SMPL-X-based manual feedback proof
```

This plan turns validated track artifacts into an inspectable teaching demo. It
must remain honest about which parts are fixture-only, real GVHMR-derived, or
real GMR-derived.

## Dependencies

- [mvp-g1-visual-track.md](mvp-g1-visual-track.md) completed or stable enough
  to provide SMPL-X and G1 track manifests.
- A tiny fixture annotation file for local smoke tests.
- A small manual annotation for one Baduanjin opening-form segment when real
  motion is available.
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
  neodojo demo play --tracks <tracks-dir> --annotations <annotations.json>
  ```

- Front/side/top synchronized playback for SMPL-X and G1.
- Wrist, elbow, and knee trajectory overlays.
- Timeline controls and frame/key-frame navigation.
- One manual key-frame feedback proof based only on SMPL-X geometry.
- Screenshot or frame evidence for rendering/UI verification.
- Tests for annotation parsing and geometry-constraint calculation.
- Docs updates only after the playback command exists.

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

- Select the first rendering/playback path and record the reason in the plan or
  implementation notes.
- Add annotation schema for manual key frames and geometric constraints.
- Load SMPL-X and G1 track manifests through the same artifact contracts created
  by earlier plans.
- Render SMPL-X as the primary teaching track and G1 as the visual companion.
- Add synchronized front/side/top views.
- Implement trajectory extraction and polyline overlays for selected joints.
- Add timeline, key-frame navigation, and current-frame readout.
- Compute one deterministic SMPL-X-based feedback result, such as shoulder
  clearance or elbow drop.
- Verify actual frames or screenshots rather than relying only on logs.
- Keep fixture-only and real-artifact labels visible in generated artifacts.
- Update README/STATUS only after the command really exists and proof evidence
  is available.

## Acceptance Evidence

- The playback command starts locally against generated track artifacts.
- The fixture inspection path runs locally without GPU dependencies.
- At least one screenshot or frame shows synchronized SMPL-X and G1 playback.
- The trajectory overlay is visible and frame-aligned.
- One manually annotated key frame computes a deterministic SMPL-X-based
  feedback result.
- The demo does not imply webcam comparison, full automation, full-corpus
  support, source-video conversion, or real GMR output unless those artifacts
  are actually present.

## Non-Goals

- Automatic key-frame detection.
- Real-time student webcam comparison.
- LLM-generated motion.
- Video-diffusion multi-view generation.
- Heavy GPU/CUDA rendering or inference on the local macOS CPU machine.
- Sim2real control or physical robot execution.
- Full official video corpus processing.

## Stop Condition

Stop when one local playback path produces verified synchronized multi-view
evidence with trajectory overlays and one SMPL-X-based feedback proof.
