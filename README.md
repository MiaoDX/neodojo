# neodojo

[![CI](https://github.com/MiaoDX/neodojo/actions/workflows/public-demo.yml/badge.svg)](https://github.com/MiaoDX/neodojo/actions/workflows/public-demo.yml)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue)
![uv](https://img.shields.io/badge/uv-ready-7c3aed)
![MuJoCo](https://img.shields.io/badge/MuJoCo-replay-0f766e)
![License](https://img.shields.io/badge/license-MIT-green)

**English** · [中文](README.zh.md)

<img src="docs/assets/neodojo-hero.webp" alt="neodojo SMPL-X and Unitree G1 teaching replay hero" width="100%">

neodojo turns official or user-supplied instructional movement videos into
simulated multi-view teaching playback. The teaching source is SMPL-X motion;
Unitree G1 is a synchronized visual companion, never the scoring source.

## Why It Exists

Instructional videos are easy to watch and hard to inspect. neodojo preserves
the motion as a teaching track, retargets it to a humanoid visual track, and
packages both into reviewable HTML artifacts that can run locally or in CI.

<img src="docs/assets/neodojo-sample.gif" alt="sample Unitree G1 MuJoCo replay from the Baduanjin derived JSON sample" width="420">

## Current Proof

- Fixture public demo: [`https://miaodx.com/neodojo/`](https://miaodx.com/neodojo/)
- CI real-demo artifact: `neodojo-real-demo-public-demo` from the
  [`public-demo` workflow](https://github.com/MiaoDX/neodojo/actions/workflows/public-demo.yml)
- Local real-demo HTML: `outputs/real-demo/public-demo/index.html` after
  `make ci-real-demo`
- Sample input:
  [`samples/baduanjin-03-006-two-hands-80-92`](samples/baduanjin-03-006-two-hands-80-92)

The committed sample contains derived JSON only: source provenance, returned
GVHMR SMPL-X joints, and normalized GMR Unitree G1 joint angles. CI regenerates
the G1 model descriptor, MuJoCo frames, browser smoke capture, and public HTML
from those JSON artifacts. Raw video, checkpoints, pickles, and rendered frame
outputs stay out of git.

## Pipeline

![neodojo architecture](docs/assets/neodojo-architecture.svg)

```text
source video -> GVHMR SMPL-X -> GMR Unitree G1 -> MuJoCo/Genesis -> teaching UI
```

## Run

```bash
make verify
make demo-public-browser
make ci-real-demo
make ci-real-demo \
  CI_REAL_SOURCE_MATERIALIZATION=path/to/source-materialization.json \
  CI_REAL_GVHMR_JSON=path/to/gvhmr-smplx-joints.json \
  CI_REAL_GMR_G1_JSON=path/to/gmr-unitree-g1.json
```

MuJoCo CI/local parity uses `MUJOCO_GL=glfw` under `xvfb-run -a`. `osmesa` is
the CPU headless fallback when system libraries are installed; `egl` is for
GPU/self-hosted runners with working EGL.

## HTML Links

| Target | How to open it |
| --- | --- |
| Live fixture HTML | [`miaodx.com/neodojo`](https://miaodx.com/neodojo/) |
| CI fixture artifact | `neodojo-public-demo` in the [`public-demo` workflow](https://github.com/MiaoDX/neodojo/actions/workflows/public-demo.yml) |
| CI sample-backed real HTML | `neodojo-real-demo-public-demo` in the [`public-demo` workflow](https://github.com/MiaoDX/neodojo/actions/workflows/public-demo.yml) |
| Local fixture HTML | `outputs/public-demo/index.html` after `make demo-public-browser` |
| Local sample-backed real HTML | `outputs/real-demo/public-demo/index.html` after `make ci-real-demo` |

## Status

This repo is still bootstrap-stage. It has fixture motion contracts, a
sample-backed Baduanjin real-demo CI lane, roboharness-style G1 MuJoCo replay,
browser smoke, capture bundles, and local GVHMR/GMR handoff boundaries. It does
not yet ship a checked-in GVHMR/GMR runtime environment, production Viser UI,
published real-demo Pages site, or full simulator runtime pipeline.

Source provenance for the Baduanjin proof is public index item `03-006` in
[`video/original_videos.md`](video/original_videos.md), trim `80s-92s`.

## Docs

- [`STATUS.md`](STATUS.md) - current truth, commands, blockers, CI evidence
- [`ARCHITECTURE.md`](ARCHITECTURE.md) - subsystem boundaries and contracts
- [`docs/runbooks/gvhmr-local-gpu.md`](docs/runbooks/gvhmr-local-gpu.md) - local GPU handoff
- [`docs/technical-roadmap.md`](docs/technical-roadmap.md) - technical research
- [`docs/humanoid-platform-evaluation.md`](docs/humanoid-platform-evaluation.md) - SMPL-X + G1 rationale

## License

MIT. See [`LICENSE`](LICENSE).
