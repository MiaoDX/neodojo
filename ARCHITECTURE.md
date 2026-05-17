# Architecture

neodojo is intended to turn a single official instructional movement video into
simulated teaching playback that can be inspected from multiple views.

The architecture is currently a target design, not an implemented runtime. The
repo currently contains only a fixture-first HTML demo generator, not the
GVHMR/GMR/simulator runtime pipeline.

## MVP Data Flow

```text
official/user-supplied source video
  -> GVHMR SMPL-X reconstruction
  -> shared SMPL-X motion record
  -> SMPL-X teaching track
  -> GMR retargeting
  -> Unitree G1 visual track
  -> MuJoCo or Genesis rendering
  -> Viser synchronized teaching UI
```

## Subsystems

Source video intake owns local video selection, licensing boundaries, clip
metadata, and routine segmentation. The repo should not commit source video.

Human motion reconstruction owns GVHMR execution and normalization into a shared
SMPL-X motion record. This record is the canonical motion source for teaching
feedback.

Teaching track playback owns SMPL-X kinematic playback, joint trajectories,
key-frame anchors, and geometric feedback checks. This is the accuracy path.

Humanoid visual track owns retargeting from SMPL-X to Unitree G1 through GMR and
rendering the robot as a visual companion. This path may lose motion detail and
must not be used as the scoring source.

Rendering owns MuJoCo/Genesis scene setup, synchronized cameras, offscreen frame
capture, and trajectory overlays.

Web playback owns the Viser UI: synchronized views, timeline control, overlays,
and later user-practice comparison.

## Core Contracts

- SMPL-X motion is the canonical teaching representation.
- G1 retargeted motion is a derived visualization artifact.
- Raw videos, checkpoints, rendered videos, generated motion files, logs, and
  large outputs stay out of git.
- Official videos are treated as licensing-sensitive; reproducible workflows
  should work with local/user-supplied files.
- Project docs must not describe install, test, lint, build, or demo commands
  until those commands actually exist.

## Non-Goals For The MVP

- RL policy training.
- Sim2real deployment.
- Text-to-motion generation.
- Video-diffusion multi-view generation.
- Using Unitree G1 as the source of teaching accuracy.

## Extension Points

- HMR backends can change if they still produce a compatible SMPL-X teaching
  record.
- Retargeting can support additional humanoids while keeping SMPL-X as the
  scoring source.
- Rendering can start with MuJoCo or Genesis and later share reusable camera and
  overlay patterns with roboharness.
- Teaching feedback can begin with manually anchored key frames and later add
  automated term-to-geometry checks.

## Proof Boundaries

The first proof should demonstrate one local Baduanjin clip moving through the
pipeline far enough to inspect synchronized SMPL-X and G1 playback. It does not
need real-time webcam comparison, sim2real control, or full-routine automation.

Background rationale and model comparisons live in:

- `docs/technical-roadmap.md`
- `docs/humanoid-platform-evaluation.md`
