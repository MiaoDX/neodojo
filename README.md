# neodojo

**English** · [中文](README.zh.md)

neodojo converts official or user-supplied instructional movement videos into
simulated multi-view teaching playback.

Intended MVP path:

```text
source video
  -> GVHMR SMPL-X output
  -> GMR retargeting
  -> SMPL-X teaching track + Unitree G1 visual track
  -> MuJoCo / Genesis rendering
  -> Viser teaching UI
```

SMPL-X is the teaching and scoring source. Unitree G1 is a visual and ecosystem
track only.

## CI-Generated Demo

The public demo is fixture-only. Its `index.html` is an interactive two-panel
teaching replay: SMPL-X skeleton teaching track on the left, Unitree G1
schematic evidence on the right, one synchronized timeline, and SMPL-X-only
scoring. The right panel is labeled as actual Unitree G1 MuJoCo model replay
only when a non-fixture imported GMR joint-angle track and MuJoCo PNG frame
sequence are supplied.
It is generated in CI by
[`.github/workflows/public-demo.yml`](.github/workflows/public-demo.yml) through
`make demo-public-browser`, uploaded as the `neodojo-public-demo` artifact, and
published to GitHub Pages from `main` when `NEODOJO_DEPLOY_PAGES=true`.

- Live fixture-only demo: [`https://miaodx.com/neodojo/`](https://miaodx.com/neodojo/)
- Generated files: `index.html`, `manifest.json`, `scene.json`,
  `screenshot.svg`, `neodojo-demo.rrd`
- Current CI evidence: [`STATUS.md`](STATUS.md) records the verified GitHub
  Actions runs and the fixture-only Pages state.

![Fixture-only neodojo public demo screenshot](https://miaodx.com/neodojo/screenshot.svg)

## Current State

This repo is still in bootstrap state. It has fixture-backed motion,
annotation, SMPL-X surface, G1 visual-track, local render-evidence, public-demo,
browser-smoke, capture-bundle, local GPU-run preparation, local GMR run
handoff/normalization, roboharness G1 descriptor registration, returned GVHMR
export inspection/import, real-demo audit commands, and a public two-panel
teaching HTML profile.

It does not yet ship a checked-in local GVHMR/GMR execution environment, true
GMR-derived default G1 replay, completed simulator runtime pipeline, committed
generated motion artifact, production Viser UI, or published real demo. A local
ignored Baduanjin proof for the `80s-92s` visible-motion clip now passes
`make verify-real` with imported/native GMR Unitree G1 joint angles, a
non-fixture roboharness/robot_descriptions MJCF descriptor, a nonblank/changing
MuJoCo PNG frame sequence, and public HTML consumption of those frames. Colab,
hosted GPU provider, self-hosted Actions GPU, operator-package, and real-demo
Pages-promotion workflows are not supported by the current command surface. The
local real-demo audit also checks that returned GVHMR frames contain visible
motion, so a static intro trim is not accepted as a completed teaching replay.

## Run

```bash
make verify
make demo-public-browser
make real-gpu-prep LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin REAL_DRY_RUN=0
make gvhmr-inspect GVHMR_RESULT=path/to/hmr4d_results.pt
make real-artifact-intake REAL_ARTIFACT_SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json REAL_ARTIFACT_GVHMR_JSON=path/to/gvhmr-smplx-joints.json
uv pip install -e '.[real-g1-replay]'
uv pip install -e path/to/GMR
PYTHONPATH=src python -m neodojo robot-model register-roboharness-g1 --out outputs/g1-visual
PYTHONPATH=src python -m neodojo tracks run-gmr-g1 --motion-record outputs/real-demo/motion-contract --gvhmr-result path/to/hmr4d_results.pt --gmr-repo path/to/GMR --body-models path/to/GMR/assets/body_models --out outputs/gmr-native-run --execute
PYTHONPATH=src python -m neodojo render mujoco-g1 --model-descriptor outputs/g1-visual/robot-models/unitree_g1/manifest.json --g1-track outputs/g1-visual/tracks/g1/manifest.json --width 1280 --height 960 --out outputs/g1-mujoco-render
make verify-real
make smoke-public
```

See [`STATUS.md`](STATUS.md) for the full command list, blockers, and next safe
task.

## Project Docs

- [`STATUS.md`](STATUS.md) — current truth, runnable commands, blockers, and CI
  evidence
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — MVP data flow, subsystem boundaries,
  contracts, and proof boundaries
- [`docs/technical-roadmap.md`](docs/technical-roadmap.md) — background
  technical research
- [`docs/humanoid-platform-evaluation.md`](docs/humanoid-platform-evaluation.md)
  — why the MVP uses SMPL-X plus G1 dual tracks
- [`docs/runbooks/gvhmr-local-gpu.md`](docs/runbooks/gvhmr-local-gpu.md) —
  current local-machine GVHMR run path

## Constraints

- Do not commit raw videos, generated motion files, rendered videos,
  checkpoints, logs, or large outputs.
- Treat official instructional videos as licensing-sensitive; prefer local or
  user-supplied source media unless rights are confirmed.
- Do not treat the fixture demo as real GVHMR/GMR/simulator proof.
- Do not label schematic right-panel evidence as actual G1 model replay.
- Do not use G1 as the scoring source.
