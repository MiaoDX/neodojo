# Status

neodojo is in bootstrap state with one fixture-only local demo.

There is now a minimal checked-in Python package, a `make test` command,
fixture-backed `motion-record`, `robot-model`, `tracks`, and `demo play`
commands, and a `make demo-html` command that writes a self-contained synthetic
web demo. There is still no checked-in GVHMR/GMR/simulator runtime pipeline,
install workflow, lint command, build command, CI gate, real generated motion
artifact, or UI server.

## Current Truth

- Project positioning: convert official instructional movement videos into
  simulated multi-view teaching playback.
- MVP path: official video -> GVHMR SMPL-X output -> GMR retargeting -> SMPL-X
  teaching track plus Unitree G1 visual track -> MuJoCo/Genesis rendering ->
  Viser UI.
- Teaching feedback should be based on the SMPL-X track. The G1 track is for
  visualization, ecosystem fit, and community-facing demos.
- Core non-goals for the MVP: RL policy training, sim2real control,
  text-to-motion generation, and video-diffusion multi-view generation.

## Active Work

- First end-to-end demo for Baduanjin opening form, "Holding Up the Heavens to
  Regulate the Triple Burner".
- Pre-GSD implementation phase split in
  `docs/plans/mvp-implementation-phases.md`.
- Immediate local-first smoke path: fixture motion -> motion record -> SMPL-X
  teaching-track manifest -> fixture G1 visual-track manifest -> local teaching
  playback HTML/manifest -> one geometry check.
- Multi-camera offscreen rendering approach, likely reusing roboharness patterns.
- Synchronized SMPL-X and Unitree G1 playback in Viser.
- Key-frame detection and geometry-constrained verbal feedback for terms such as
  "sink the shoulders" and "drop the elbows".
- Fixture-only HTML teaching demo generated under `outputs/html-demo/`, proving
  the intended web playback shape without claiming real reconstruction or
  retargeting.
- Fixture-backed SMPL-X motion-record and teaching-track manifests, proving the
  local contract shape that later GVHMR/GMR imports should consume.
- Fixture-backed Unitree G1 model descriptor, derived visual-track manifest, and
  comparison report with `g1_scoring_allowed: false`.
- Fixture-only teaching playback HTML generated under `outputs/teaching-demo/`,
  proving that the SMPL-X and G1 manifests can be consumed together while
  preserving the SMPL-X scoring boundary.

## Blockers And Constraints

- Official instructional videos are licensing-sensitive. Prefer local,
  user-supplied source video unless rights are confirmed.
- Do not commit raw videos, generated motion files, model checkpoints, rendered
  videos, logs, or other large outputs.
- The accuracy ceiling is the HMR/SMPL-X reconstruction quality, especially for
  out-of-distribution qigong poses, self-occlusion, feet, and hands.
- Unitree G1 is not the scoring source because its torso and hand DOF cannot
  fully preserve the original human motion.
- Local execution should stay friendly to this macOS Apple Silicon CPU machine:
  use imported GVHMR/HAMER outputs or fixtures instead of running heavy GPU/CUDA
  inference locally.
- Downstream development may use synthetic or PBHC-sourced bootstrap fixtures to
  prove interfaces and playback, but the full MVP still requires a real
  GVHMR-produced Baduanjin artifact before it can be called end-to-end.

## What Can Be Run Now

```bash
make test
PYTHONPATH=src python -m neodojo motion-record create --out outputs/motion-contract
PYTHONPATH=src python -m neodojo robot-model register --robot unitree_g1 --fixture --out outputs/g1-visual
PYTHONPATH=src python -m neodojo tracks build --motion-record outputs/motion-contract --robot unitree_g1 --model-descriptor outputs/g1-visual/robot-models/unitree_g1/manifest.json --out outputs/g1-visual
PYTHONPATH=src python -m neodojo demo play --motion-record outputs/motion-contract --g1-track outputs/g1-visual/tracks/g1/manifest.json --out outputs/teaching-demo
make demo-html
```

`make test` runs the focused Python unit tests for the fixture demo generator
and local motion contract. `neodojo motion-record create` writes fixture-backed
SMPL-X motion-record and teaching-track manifests under the selected ignored
output directory. `neodojo robot-model register` and `neodojo tracks build`
write fixture G1 model/visual-track manifests and a comparison report that keeps
G1 non-scoring. `neodojo demo play` writes `outputs/teaching-demo/index.html`
and a playback manifest from the SMPL-X and G1 manifests. `make demo-html`
writes `outputs/html-demo/index.html`, `outputs/html-demo/manifest.json`, and
the local motion/track manifests it consumes. These artifacts use synthetic
fixture motion only; they validate UI plumbing, trajectory drawing, timeline
sync, the local SMPL-X/G1 scoring boundary, and one SMPL-X-based geometry check,
not qigong correctness.

## Next Safe Task

The next MVP capability is `docs/plans/mvp-real-conversion-gate.md`, but it is
a deliberate GPU/local-dev gate. Do not run GVHMR full-video inference on this
macOS CPU workspace; use a GPU-capable machine or an imported GVHMR artifact,
then import it through the same motion-record contract.

## Background Evidence

- `docs/technical-roadmap.md` is the long technical research report.
- `docs/humanoid-platform-evaluation.md` records the G1 + SMPL-X dual-track
  platform decision.
- `docs/plans/mvp-implementation-phases.md` indexes the four current executable
  MVP plan slices.
