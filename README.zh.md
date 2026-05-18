# neodojo

[English](README.md) · **中文**

neodojo 会把官方或用户提供的教学动作视频转成可多视角检查的仿真教学回放。

目标 MVP 路径：

```text
source video
  -> GVHMR SMPL-X output
  -> GMR retargeting
  -> SMPL-X teaching track + Unitree G1 visual track
  -> MuJoCo / Genesis rendering
  -> Viser teaching UI
```

SMPL-X 是教学与评分来源。Unitree G1 只负责视觉展示和生态对齐。

## CI 生成演示

当前 public demo 是 fixture-only。它由
[`.github/workflows/public-demo.yml`](.github/workflows/public-demo.yml) 在 CI
中通过 `make demo-public-browser` 生成，上传为 `neodojo-public-demo` artifact，
并在 `main` 分支设置 `NEODOJO_DEPLOY_PAGES=true` 时发布到 GitHub Pages。

- 在线 fixture-only demo: [`https://miaodx.com/neodojo/`](https://miaodx.com/neodojo/)
- 生成文件：`index.html`、`manifest.json`、`scene.json`、`screenshot.svg`、
  `neodojo-demo.rrd`
- 当前 CI 证据：[`STATUS.md`](STATUS.md) 记录已验证的 GitHub Actions runs 和
  fixture-only Pages 状态。

![Fixture-only neodojo public demo screenshot](https://miaodx.com/neodojo/screenshot.svg)

## 当前状态

这个 repo 仍处于 bootstrap 状态。它已经有 fixture-backed motion、annotation、
SMPL-X surface、G1 visual-track、本地 render evidence、public-demo、
browser-smoke、capture-bundle，以及 metadata-only GPU handoff/operator-package
命令。

它还没有提交到仓库的本地 GVHMR/GMR execution environment、完整 simulator runtime
pipeline、已提交 generated motion artifact、production Viser UI，或已发布 real demo。
本机 real GVHMR proof 只存在于 ignored `outputs/` 下。

## 运行

```bash
make verify
make demo-public-browser
make smoke-public
```

完整命令列表、blockers 和下一步安全任务见 [`STATUS.md`](STATUS.md)。

## 项目文档

- [`STATUS.md`](STATUS.md) — 当前事实、可运行命令、blockers 和 CI 证据
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — MVP 数据流、子系统边界、contracts 和验证边界
- [`docs/technical-roadmap.md`](docs/technical-roadmap.md) — 背景技术调研
- [`docs/humanoid-platform-evaluation.md`](docs/humanoid-platform-evaluation.md)
  — 为什么 MVP 采用 SMPL-X + G1 双轨

## 约束

- 不要提交 raw videos、generated motion files、rendered videos、checkpoints、
  logs 或大输出。
- 官方教学视频需要按 licensing-sensitive 处理；除非权利已确认，否则优先使用本地或
  用户提供的 source media。
- 不要把 fixture demo 当成真实 GVHMR/GMR/simulator 证明。
- 不要把 G1 当成评分来源。
