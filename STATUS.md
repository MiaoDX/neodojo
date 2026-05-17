# Status

neodojo is in bootstrap state with one fixture-only local demo.

There is now a minimal checked-in Python package, a `make test` command, and a
`make demo-html` command that writes a self-contained synthetic web demo. There
is still no checked-in GVHMR/GMR/simulator runtime pipeline, install workflow,
lint command, build command, CI gate, generated motion artifact, or UI server.

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
- Immediate local-first smoke path: fixture motion -> motion record -> track
  manifest -> local inspection -> one geometry check.
- Multi-camera offscreen rendering approach, likely reusing roboharness patterns.
- Synchronized SMPL-X and Unitree G1 playback in Viser.
- Key-frame detection and geometry-constrained verbal feedback for terms such as
  "sink the shoulders" and "drop the elbows".
- Fixture-only HTML teaching demo generated under `outputs/html-demo/`, proving
  the intended web playback shape without claiming real reconstruction or
  retargeting.

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
make demo-html
```

`make test` runs the focused Python unit tests for the fixture demo generator.
`make demo-html` writes `outputs/html-demo/index.html` and
`outputs/html-demo/manifest.json`. The generated demo uses synthetic fixture
motion only; it validates UI plumbing, trajectory drawing, timeline sync, and
one SMPL-X-based geometry check, not qigong correctness.

## Next Safe Task

Extend the immediate local-first smoke path from
`docs/plans/mvp-implementation-phases.md`: split the current synthetic demo data
into explicit motion-record and track manifests, then make the HTML demo consume
those manifests through the same contracts that later GVHMR/GMR imports will
use. Defer real GVHMR conversion to the GPU follow-up gate until this local
contract works.

## Background Evidence

- `docs/technical-roadmap.md` is the long technical research report.
- `docs/humanoid-platform-evaluation.md` records the G1 + SMPL-X dual-track
  platform decision.
- `docs/plans/mvp-implementation-phases.md` splits that research into three
  standalone implementation phases.
