# Status

neodojo is in bootstrap/docs-only state.

There is no checked-in runtime pipeline yet: no package layout, install command,
test command, lint command, build command, CI gate, demo entrypoint, generated
motion artifact, or UI server is currently part of the repo.

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
- Multi-camera offscreen rendering approach, likely reusing roboharness patterns.
- Synchronized SMPL-X and Unitree G1 playback in Viser.
- Key-frame detection and geometry-constrained verbal feedback for terms such as
  "sink the shoulders" and "drop the elbows".

## Blockers And Constraints

- Official instructional videos are licensing-sensitive. Prefer local,
  user-supplied source video unless rights are confirmed.
- Do not commit raw videos, generated motion files, model checkpoints, rendered
  videos, logs, or other large outputs.
- The accuracy ceiling is the HMR/SMPL-X reconstruction quality, especially for
  out-of-distribution qigong poses, self-occlusion, feet, and hands.
- Unitree G1 is not the scoring source because its torso and hand DOF cannot
  fully preserve the original human motion.

## What Can Be Run Now

Nothing project-specific yet. Future code changes should add the command surface
they introduce: package metadata, scripts or Make targets, focused tests, and
README/status updates.

## Next Safe Task

Add the smallest reproducible pipeline entrypoint for one local source clip:
validate inputs, call or wrap GVHMR/GMR in a clearly documented way, and produce
a small non-image motion artifact suitable for later rendering work.

## Background Evidence

- `docs/technical-roadmap.md` is the long technical research report.
- `docs/humanoid-platform-evaluation.md` records the G1 + SMPL-X dual-track
  platform decision.
