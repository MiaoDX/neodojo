# Architecture

neodojo is intended to turn a single official instructional movement video into
simulated teaching playback that can be inspected from multiple views.

The architecture is currently a target design, not a fully implemented runtime.
The tracked repo contains fixture-first motion contracts, G1 visual-track manifests,
an imported-GMR G1 track boundary, local G1 SVG/HTML render evidence, optional
MuJoCo mesh render evidence with matching imported-GMR qpos application,
teaching playback HTML, public-demo artifacts, an optional first Viser local
runtime, real-conversion prep, and local source-media materialization handoff.
This workspace also has a local ignored GPU proof that produced a non-fixture
GVHMR SMPL-X teaching-joints export and imported it through `outputs/real-demo/`.
The tracked repo does not contain a checked-in GVHMR/GMR/simulator runtime
pipeline, production teaching UI, committed generated motion artifact, or
published real demo.

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
metadata, trim handoff, reference-frame extraction, and routine segmentation.
The repo should not commit source video.

Human motion reconstruction owns GVHMR execution and normalization into a shared
SMPL-X motion record. This record is the canonical motion source for teaching
feedback.

Teaching track playback owns SMPL-X kinematic playback, joint trajectories,
key-frame anchors, deterministic annotation detection, and geometric feedback
checks. This is the accuracy path. The current surface layer is a joint-derived
capsule proxy; licensed SMPL-X model assets can be described locally, but full
mesh generation waits for mesh-ready SMPL-X pose/shape parameters and a future
renderer.

Humanoid visual track owns retargeting from SMPL-X to Unitree G1 through GMR and
rendering the robot as a visual companion. The current repo can import a
normalized external GMR Unitree G1 JSON export, but does not run GMR locally.
When MuJoCo assets are supplied, matching imported GMR joint angles can be
applied to robot `qpos` for render evidence. This path may lose motion detail
and must not be used as the scoring source.

Rendering owns MuJoCo/Genesis scene setup, synchronized cameras, offscreen frame
capture, and trajectory overlays.

Web playback owns the Viser UI: synchronized views, timeline control, overlays,
and later user-practice comparison. The current optional Viser slice consumes
the public-demo scene contract and proves synchronized SMPL-X/G1 tracks with a
frame slider, camera preset controls, annotation-anchor navigation, and
generated front/side/top preview screenshots; richer production teaching polish
remains follow-on work.

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
