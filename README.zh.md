# neodojo

[![CI](https://github.com/MiaoDX/neodojo/actions/workflows/public-demo.yml/badge.svg)](https://github.com/MiaoDX/neodojo/actions/workflows/public-demo.yml)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue)
![uv](https://img.shields.io/badge/uv-ready-7c3aed)
![MuJoCo](https://img.shields.io/badge/MuJoCo-replay-0f766e)
![License](https://img.shields.io/badge/license-MIT-green)

[English](README.md) · **中文**

<img src="docs/assets/neodojo-code-dojo.webp" alt="green-code dojo with a robot and motion skeleton training together" width="100%">

> "This is the Construct. It's our loading program. We can load anything, from clothing, to equipment, weapons, training simulations..."
>
> — Morpheus, *The Matrix* (1999)

**I know kung fu.**

二十七年后，我们终于可以做一个真实的 Construct。

不是用来加载武器，也不是加载战斗程序。这个 Construct 加载 Baduanjin、Wu Qin
Xi、Yi Jin Jing，最终也可以加载任何需要看清标准动作的人体练习。

neodojo 是一个面向广义 kung fu 的 simulation training dojo：qigong、taichi、
traditional martial arts、daoyin、康复动作，以及更多。它把教学视频转成 motion
tracks，重定向到仿真 humanoid，再从多角度渲染，并叠加 joint paths 与同步回放。

你看到一个动作的 standard shadow，然后把这个 shadow 装进自己的训练循环里。

<img src="docs/assets/neodojo-sample.gif" alt="Baduanjin preview with original video, SMPL-X skeleton, and MuJoCo G1 replay panels" width="100%">

## 可以打开什么

| Artifact | Link |
| --- | --- |
| 在线 fixture demo | [`miaodx.com/neodojo`](https://miaodx.com/neodojo/) |
| CI fixture HTML | [`public-demo` workflow](https://github.com/MiaoDX/neodojo/actions/workflows/public-demo.yml) 里的 `neodojo-public-demo` |
| CI sample-backed real HTML | 同一 workflow 里的 `neodojo-real-demo-public-demo` |
| 本地 sample-backed real HTML | `make ci-real-demo` 后的 `outputs/real-demo/public-demo/index.html` |
| 本地整套套路 HTML | 运行 routine split/assemble 命令后的 `outputs/routines/<routine>/html/index.html` |

提交的 Baduanjin sample 包含一个小的 trimmed source clip，以及重建 demo 所需的
GVHMR/GMR 派生 JSON。更大的 source videos 后续用 helper scripts 下载到本地测试，
不直接放进 git。

## Pipeline

![neodojo architecture](docs/assets/neodojo-architecture.svg)

`source video -> GVHMR SMPL-X -> GMR Unitree G1 -> MuJoCo/Genesis -> teaching UI`

SMPL-X 是教学与评分来源。Unitree G1 是视觉伴随轨道，不作为评分来源。

## 试一下

用 `make ci-real-demo` 生成 sample-backed real HTML，用 `make verify` 检查
bootstrap verification surface。更完整的命令在 [`STATUS.md`](STATUS.md)。

三个已记录的 Bilibili source 可以走本地 routine orchestration 路径：

```bash
make bilibili-download BILIBILI_DRY_RUN=1
make bilibili-download BILIBILI_DRY_RUN=0 BILIBILI_COOKIES_FROM_BROWSER=chrome
make routine-split ROUTINE=baduanjin ROUTINE_SOURCE_VIDEO=video/bilibili/01_baduanjin-complete-routine-with-breathing-cues.mp4 ROUTINE_DRY_RUN=0
make routine-prepare-gpu ROUTINE=baduanjin
make routine-assemble ROUTINE=baduanjin
make routine-smoke ROUTINE=baduanjin
```

这条路径会准备本地 phase clips 和逐 phase 的 GVHMR/GMR handoff。它不表示仓库已经
内置或运行 GVHMR、GMR、checkpoints、MuJoCo/Genesis mesh rendering，或已经发布真实
整套套路 demo。

## Contributing

The dojo is not the place. The dojo is the practice.

Issues、PRs、ideas、field notes 都欢迎。现在还很早，每一条反馈都有价值。

- 练 qigong、taichi、martial arts 的人：老师会讲、但平面视频看不出来的细节，
  正是这个项目最需要的东西。
- HMR / humanoid researchers：欢迎 review roadmap，建议更好的 reconstruction、
  retargeting、rendering 或 evaluation 方法。
- roboharness / AI-coding-agent builders：这是一个开放的 agent-assisted
  simulation tooling 实验。

**Show me.**

## 文档

- [`STATUS.md`](STATUS.md) - 当前事实、命令、blockers、CI evidence
- [`ARCHITECTURE.md`](ARCHITECTURE.md) - subsystem boundaries 和 contracts
- [`docs/runbooks/gvhmr-local-gpu.md`](docs/runbooks/gvhmr-local-gpu.md) - local GPU handoff
- [`docs/technical-roadmap.md`](docs/technical-roadmap.md) - technical research
- [`docs/humanoid-platform-evaluation.md`](docs/humanoid-platform-evaluation.md) - SMPL-X + G1 rationale

## License

MIT. See [`LICENSE`](LICENSE).
