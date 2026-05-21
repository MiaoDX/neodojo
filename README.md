# neodojo

[![CI](https://github.com/MiaoDX/neodojo/actions/workflows/public-demo.yml/badge.svg)](https://github.com/MiaoDX/neodojo/actions/workflows/public-demo.yml)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue)
![uv](https://img.shields.io/badge/uv-ready-7c3aed)
![MuJoCo](https://img.shields.io/badge/MuJoCo-replay-0f766e)
![License](https://img.shields.io/badge/license-MIT-green)

**English** · [中文](README.zh.md)

<img src="docs/assets/neodojo-code-dojo.webp" alt="green-code dojo with a robot and motion skeleton training together" width="100%">

> "This is the Construct. It's our loading program. We can load anything, from clothing, to equipment, weapons, training simulations..."
>
> — Morpheus, *The Matrix* (1999)

**I know kung fu.**

Twenty-seven years later, we can build a real Construct.

Not for loading weapons. Not for loading combat programs. This Construct loads
Baduanjin, Wu Qin Xi, Yi Jin Jing, and eventually any human movement practice
that benefits from seeing the standard form.

neodojo is a simulation training dojo for kung fu in its broadest sense:
qigong, taichi, traditional martial arts, daoyin, rehabilitation drills, and
beyond. It converts instructional videos into motion tracks, retargets them to
a humanoid in simulation, and renders the result from multiple angles with
joint paths and synchronized playback.

You see the standard shadow of a move, then load that shadow into your own
training loop.

<img src="docs/assets/neodojo-sample.gif" alt="Baduanjin preview with original video, SMPL-X skeleton, and MuJoCo G1 replay panels" width="100%">

## What You Can Open

| Artifact | Link |
| --- | --- |
| Live full routine gallery | [`miaodx.com/neodojo`](https://miaodx.com/neodojo/) |
| Full Baduanjin report | [`baduanjin/html`](https://miaodx.com/neodojo/baduanjin/html/) |
| Full Wu Qin Xi report | [`wuqinxi/html`](https://miaodx.com/neodojo/wuqinxi/html/) |
| Full Yi Jin Jing report | [`yijinjing/html`](https://miaodx.com/neodojo/yijinjing/html/) |
| Fixture demo | [`miaodx.com/neodojo/fixture`](https://miaodx.com/neodojo/fixture/) |
| Full routine gallery mirror | [`miaodx.com/neodojo/samples/routines`](https://miaodx.com/neodojo/samples/routines/) |
| CI fixture HTML | `neodojo-public-demo` in the [`public-demo` workflow](https://github.com/MiaoDX/neodojo/actions/workflows/public-demo.yml) |
| CI sample-backed real HTML | `neodojo-real-demo-public-demo` in the same workflow |
| Local sample-backed real HTML | `outputs/real-demo/public-demo/index.html` after `make ci-real-demo` |
| Local routine HTML | `outputs/routines/<routine>/html/index.html` after the routine split/assemble commands |

The committed full routine samples live under [`samples/routines`](samples/routines)
and are published as the Pages homepage, with a compatibility mirror at
`/samples/routines/`. They are lean self-contained reports: Original video
clips, SMPL-X Teaching Track, and 5 fps Unitree G1 Model Replay MP4 media for
each selected round.

The committed Baduanjin sample includes a small trimmed source clip plus the
derived GVHMR/GMR JSON needed to rebuild the demo. Larger source videos should
stay out of git and be fetched by helper scripts for local testing.

## Pipeline

![neodojo architecture](docs/assets/neodojo-architecture.svg)

`source video -> GVHMR SMPL-X -> GMR Unitree G1 -> MuJoCo/Genesis -> teaching UI`

SMPL-X is the teaching and scoring source. Unitree G1 is the visual companion,
not the judge.

## Try It

Use `make ci-real-demo` for the sample-backed real HTML and `make verify` for
the bootstrap verification surface. Full command details live in
[`STATUS.md`](STATUS.md).

For the three tracked Bilibili sources, the local routine orchestration path is:

```bash
make bilibili-download BILIBILI_DRY_RUN=1
make bilibili-download BILIBILI_DRY_RUN=0 BILIBILI_COOKIES_FROM_BROWSER=chrome
make routine-split ROUTINE=baduanjin ROUTINE_SOURCE_VIDEO=video/bilibili/01_baduanjin-complete-routine-with-breathing-cues.mp4 ROUTINE_DRY_RUN=0
make routine-prepare-gpu ROUTINE=baduanjin
make routine-assemble ROUTINE=baduanjin
make routine-smoke ROUTINE=baduanjin
```

This prepares local one-round phase clips and per-phase GVHMR/GMR handoffs.
The tracked Baduanjin, Wu Qin Xi, and Yi Jin Jing boundaries are visually
inspected representative rounds, not fixed-duration placeholder blocks or full
repeated practice sets.
When current returned artifacts are present, `routine assemble` writes a
self-contained report directory: an overview `index.html` plus one synchronized
phase report per selected round with Original video, SMPL-X Teaching Track, and
G1 visual evidence. Add `ROUTINE_MODEL_DESCRIPTOR=... ROUTINE_RENDER_MUJOCO=1`
to build actual G1 Model Replay media from imported GMR tracks. MuJoCo G1 replay
is sampled at 5 fps by default and encoded to per-phase MP4 for HTML playback,
so the Original video, SMPL-X canvas, and G1 replay advance on the same sampled
timeline; set `ROUTINE_G1_REPLAY_FPS=10` or CLI `--g1-replay-fps 10` to change
that. By default routine assembly keeps those phase reports self-contained but
prunes bulky full-evidence artifacts such as duplicate scene JSON, Rerun
fallback files, validation copies, Viser runtime output, and capture bundles;
set `ROUTINE_PRESERVE_PHASE_EVIDENCE=1` or CLI
`--preserve-phase-evidence` when debugging the full artifact tree. Use
`ROUTINE_INDEX_ONLY=1` or CLI
`--index-only` for the old compact artifact-status index. The repo still does
not vendor GVHMR, GMR, checkpoints, MuJoCo/Genesis assets, or a live published
real routine demo.

## Contributing

The dojo is not the place. The dojo is the practice.

Issues, PRs, ideas, and field notes are welcome. At this stage, every piece of
feedback can shape the project.

- Practitioners: the details your teacher can say but a flat video cannot show
  are exactly what this project needs.
- HMR and humanoid researchers: review the roadmap and suggest better
  reconstruction, retargeting, rendering, or evaluation approaches.
- roboharness and AI-coding-agent builders: this is an open experiment in
  agent-assisted simulation tooling.

**Show me.**

## Docs

- [`STATUS.md`](STATUS.md) - current truth, commands, blockers, CI evidence
- [`ARCHITECTURE.md`](ARCHITECTURE.md) - subsystem boundaries and contracts
- [`docs/runbooks/gvhmr-local-gpu.md`](docs/runbooks/gvhmr-local-gpu.md) - local GPU handoff
- [`docs/technical-roadmap.md`](docs/technical-roadmap.md) - technical research
- [`docs/humanoid-platform-evaluation.md`](docs/humanoid-platform-evaluation.md) - SMPL-X + G1 rationale

## License

MIT. See [`LICENSE`](LICENSE).
