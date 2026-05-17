# Status

neodojo is in bootstrap state with one fixture-only local demo.

There is now a minimal checked-in Python package, a `make test` command,
fixture-backed and external-JSON `motion-record` paths, `robot-model`,
`tracks`, `render g1`, `demo play`, and `real-conversion prepare` commands, and
a `make demo-html` command that writes a self-contained synthetic web demo.
There is still no checked-in GVHMR/GMR/simulator runtime pipeline,
MuJoCo/Genesis real mesh rendering, install workflow, lint command, build
command, CI gate, real generated motion artifact, or UI server.

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
- External GVHMR SMPL-X teaching-joints JSON import into the same motion-record
  contract. This is an import boundary only, not local GVHMR execution or raw
  `.pt` parsing.
- Fixture-backed Unitree G1 model descriptor, derived visual-track manifest, and
  comparison report with `g1_scoring_allowed: false`.
- Local G1 SVG/HTML render evidence generated under `outputs/g1-render/`,
  proving the render manifest, front/side/top frame evidence, and G1
  non-scoring boundary. Fixture descriptors require explicit
  `--allow-fixture-model`.
- Fixture-only teaching playback HTML generated under `outputs/teaching-demo/`,
  proving that the SMPL-X and G1 manifests can be consumed together while
  preserving the SMPL-X scoring boundary.
- The local non-GPU G1 render evidence slice in
  `docs/plans/mvp-g1-real-model-rendering.md` has landed as an SVG/HTML
  descriptor/track render path. MuJoCo/Genesis mesh rendering remains a later
  gap.
- Real-conversion source prep manifest generated under
  `outputs/real-conversion-gate/`, selecting source `03-006` metadata and a
  short trim window for a later GPU run.

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
PYTHONPATH=src python -m neodojo motion-record create --from-gvhmr-json path/to/gvhmr-smplx-joints.json --out outputs/motion-contract
PYTHONPATH=src python -m neodojo robot-model register --robot unitree_g1 --fixture --out outputs/g1-visual
PYTHONPATH=src python -m neodojo tracks build --motion-record outputs/motion-contract --robot unitree_g1 --model-descriptor outputs/g1-visual/robot-models/unitree_g1/manifest.json --out outputs/g1-visual
PYTHONPATH=src python -m neodojo render g1 --model-descriptor outputs/g1-visual/robot-models/unitree_g1/manifest.json --g1-track outputs/g1-visual/tracks/g1/manifest.json --allow-fixture-model --out outputs/g1-render
PYTHONPATH=src python -m neodojo demo play --motion-record outputs/motion-contract --g1-track outputs/g1-visual/tracks/g1/manifest.json --out outputs/teaching-demo
PYTHONPATH=src python -m neodojo real-conversion prepare --id 03-006 --start 0 --end 12 --out outputs/real-conversion-gate
make demo-html
```

`make test` runs the focused Python unit tests for the fixture demo generator
and local motion contract. `neodojo motion-record create` writes fixture-backed
SMPL-X motion-record and teaching-track manifests under the selected ignored
output directory, or imports an external GVHMR teaching-joints JSON export with
`--from-gvhmr-json`. `neodojo robot-model register` and `neodojo tracks build`
write fixture G1 model/visual-track manifests and a comparison report that
keeps G1 non-scoring. `neodojo render g1` writes local SVG/HTML front/side/top
render evidence and a render manifest from a G1 model descriptor plus G1 track;
fixture model descriptors require explicit `--allow-fixture-model`, and this is
not MuJoCo/Genesis simulator mesh rendering. `neodojo demo play` writes
`outputs/teaching-demo/index.html` and a playback manifest from the SMPL-X and
G1 manifests. `make demo-html`
writes `outputs/html-demo/index.html`, `outputs/html-demo/manifest.json`, and
the local motion/track manifests it consumes. These artifacts use synthetic
fixture motion only; they validate UI plumbing, trajectory drawing, timeline
sync, the local SMPL-X/G1 scoring boundary, and one SMPL-X-based geometry check,
not qigong correctness.

`neodojo real-conversion prepare` writes ignored source/trim metadata for the
later GPU run and does not download video or execute GVHMR.

## Remaining Non-GPU Gaps

- MuJoCo/Genesis real Unitree G1 mesh rendering from local URDF/MJCF plus
  meshes.
- A pose source compatible with real G1 joints: imported GMR joint angles or a
  clearly marked deterministic G1 joint-angle fixture. The current G1 track is
  still a derived visual skeleton.
- SMPL-X mesh/body-surface playback; current demos draw joints and bones.
- Simulator/Viser runtime integration and multi-camera offscreen capture.
- Feedback beyond the first fixture geometry check: automatic key-frame
  detection, more posture terms, and routine-level review.
- Rights-preserving source media handling beyond metadata and trim prep.
- Install, lint, build, and CI command surfaces.

## Next Safe Task

The next MVP capability is the non-GPU contract/public-demo/CI sequence:
`docs/plans/mvp-pipeline-contract-hardening.md`,
`docs/plans/mvp-visualization-and-public-demo.md`, and
`docs/plans/mvp-devex-ci-surface.md` before returning to
`docs/plans/mvp-real-conversion-gate.md`. Do not run GVHMR full-video inference
on this macOS CPU workspace; use a GPU-capable machine to export a GVHMR SMPL-X
teaching-joints JSON artifact, then import it through
`neodojo motion-record create --from-gvhmr-json`.

## Background Evidence

- `docs/technical-roadmap.md` is the long technical research report.
- `docs/humanoid-platform-evaluation.md` records the G1 + SMPL-X dual-track
  platform decision.
- `docs/plans/mvp-implementation-phases.md` indexes the current executable MVP
  plan slices.
