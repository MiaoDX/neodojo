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

The public demo is fixture-only. It is generated in CI by
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
browser-smoke, capture-bundle, local GPU-run preparation, returned GVHMR export
inspection/import, and real-demo audit commands.

It does not yet ship a checked-in local GVHMR/GMR execution environment,
completed simulator runtime pipeline, committed generated motion artifact,
production Viser UI, or published real demo. A local real GVHMR proof exists
only under ignored `outputs/`. Colab, hosted GPU provider, self-hosted Actions
GPU, operator-package, and real-demo Pages-promotion workflows are not supported
by the current command surface.

## Run

```bash
make verify
make demo-public-browser
make real-gpu-prep LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin REAL_DRY_RUN=0
make gvhmr-inspect GVHMR_RESULT=path/to/hmr4d_results.pt
make real-artifact-intake REAL_ARTIFACT_SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json REAL_ARTIFACT_GVHMR_JSON=path/to/gvhmr-smplx-joints.json
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
- Do not use G1 as the scoring source.
