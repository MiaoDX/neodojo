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
The same workflow also runs `make ci-real-demo` and uploads
`outputs/real-demo/public-demo/index.html` as the
`neodojo-real-demo-public-demo` artifact. By default that CI real-demo artifact
uses the committed derived JSON sample in
[`samples/baduanjin-03-006-two-hands-80-92`](samples/baduanjin-03-006-two-hands-80-92):
source provenance, returned GVHMR SMPL-X joints, and normalized GMR Unitree G1
joint angles. CI regenerates the G1 model descriptor, MuJoCo frames, and public
HTML from those JSON artifacts; raw source video and rendered outputs remain
out of git.

- Live fixture-only demo: [`https://miaodx.com/neodojo/`](https://miaodx.com/neodojo/)
- Generated files: `index.html`, `manifest.json`, `scene.json`,
  `screenshot.svg`, `neodojo-demo.rrd`
- Current CI evidence: [`STATUS.md`](STATUS.md) records the verified GitHub
  Actions runs and the fixture-only Pages state.
- Real-demo source provenance can be documented by pointing to the public
  source-video index. The local Baduanjin proof uses source `03-006`
  (`5八段锦两手托天理三焦`) from [`video/original_videos.md`](video/original_videos.md),
  trim `80s-92s`; the demo publishes derived skeleton/robot playback, not the
  source video.

![Fixture-only neodojo public demo screenshot](https://miaodx.com/neodojo/screenshot.svg)

## Current State

This repo is still in bootstrap state. It has fixture-backed motion,
annotation, SMPL-X surface, G1 visual-track, local render-evidence, public-demo,
browser-smoke, capture-bundle, local GPU-run preparation, local GMR run
handoff/normalization, roboharness G1 descriptor registration, returned GVHMR
export inspection/import, real-demo audit commands, and a public two-panel
teaching HTML profile.

It does not yet ship a checked-in local GVHMR/GMR execution environment,
completed simulator runtime pipeline, production Viser UI, or published real
demo. The repo now includes a small derived JSON Baduanjin sample for CI, while
raw video, native checkpoints, pickles, rendered PNGs, and large generated
outputs remain ignored. A local ignored Baduanjin proof for the `80s-92s`
visible-motion clip now passes
`make verify-real` with imported/native GMR Unitree G1 joint angles, a
non-fixture roboharness/robot_descriptions MJCF descriptor, a nonblank/changing
MuJoCo PNG frame sequence, and public HTML consumption of those frames. Colab,
hosted GPU provider, self-hosted Actions GPU, operator-package, and real-demo
Pages-promotion workflows are not supported by the current command surface. CI
does upload a sample-backed real-demo public HTML artifact from committed
derived JSON. The local and CI real-demo audits also check that returned GVHMR
frames contain visible motion, so a static intro trim is not accepted as a
completed teaching replay.

## Run

```bash
make verify
make demo-public-browser
make ci-real-demo
make ci-real-demo \
  CI_REAL_SOURCE_MATERIALIZATION=path/to/source-materialization.json \
  CI_REAL_GVHMR_JSON=path/to/gvhmr-smplx-joints.json \
  CI_REAL_GMR_G1_JSON=path/to/gmr-unitree-g1.json \
  CI_REAL_VERIFY_STRICT=1
make real-gpu-prep LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin REAL_DRY_RUN=0
make gvhmr-inspect GVHMR_RESULT=path/to/hmr4d_results.pt
make real-artifact-intake REAL_ARTIFACT_SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json REAL_ARTIFACT_GVHMR_JSON=path/to/gvhmr-smplx-joints.json
uv pip install -e '.[real-g1-replay]'
uv pip install -e path/to/GMR
PYTHONPATH=src python -m neodojo robot-model register-roboharness-g1 --out outputs/g1-visual
PYTHONPATH=src python -m neodojo tracks run-gmr-g1 --motion-record outputs/real-demo/motion-contract --gvhmr-result path/to/hmr4d_results.pt --gmr-repo path/to/GMR --body-models path/to/GMR/assets/body_models --out outputs/gmr-native-run --execute
make mujoco-g1-render MODEL_DESCRIPTOR=outputs/g1-visual/robot-models/unitree_g1/manifest.json G1_TRACK=outputs/g1-visual/tracks/g1/manifest.json
make roboharness-g1-report MODEL_DESCRIPTOR=outputs/g1-visual/robot-models/unitree_g1/manifest.json G1_TRACK=outputs/g1-visual/tracks/g1/manifest.json
make verify-real
make smoke-public
```

The default MuJoCo G1 render uses the roboharness `g1-reach` visual style:
the wrapped G1 MJCF scene, blue skybox gradient, gray/white checker floor,
roboharness lights, original G1 materials, and named cameras tuned for the
raised-hands qigong replay. The render target uses the CI-compatible OpenGL
path `MUJOCO_GL=glfw` under `xvfb-run -a`, at `1280x960`, writing
`outputs/g1-mujoco-render`. GitHub Actions has a focused smoke test for this
same backend path.

`make roboharness-g1-report` writes
`outputs/g1-roboharness-report/neodojo_g1_replay_report.html`, a sampled
roboharness checkpoint report with `start`, `early`, `middle`, `late`, and
`finish` stages from the imported G1 track.

`MUJOCO_GL=osmesa` remains the CPU software headless fallback when OSMesa system
libraries are installed. `MUJOCO_GL=egl` is best reserved for GPU/self-hosted
runners with working EGL.
To review visible differences and setup failures in one file, run:

```bash
make mujoco-backend-compare MODEL_DESCRIPTOR=outputs/g1-visual/robot-models/unitree_g1/manifest.json G1_TRACK=outputs/g1-visual/tracks/g1/manifest.json
```

This writes `outputs/g1-mujoco-backend-comparison/index.html`.
For a repeated timing benchmark, run:

```bash
make mujoco-backend-benchmark MODEL_DESCRIPTOR=outputs/g1-visual/robot-models/unitree_g1/manifest.json G1_TRACK=outputs/g1-visual/tracks/g1/manifest.json
```

This writes `outputs/g1-mujoco-backend-benchmark/benchmark.md` plus a full
`manifest.json`.

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
- Keep public source-video provenance in docs/manifests for real demos; do not
  publish raw source videos from this repo.
- Do not treat the fixture demo as real GVHMR/GMR/simulator proof.
- Do not label schematic right-panel evidence as actual G1 model replay.
- Do not use G1 as the scoring source.
