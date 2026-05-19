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

当前 public demo 是 fixture-only。它的 `index.html` 是交互式双栏教学回放：
左侧是 SMPL-X skeleton teaching track，右侧是 Unitree G1 robot model replay，
两侧共用同一个同步 timeline，并且只允许 SMPL-X 作为评分来源。它由
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
browser-smoke、capture-bundle、本地 GPU run 准备、返回 GVHMR export 检查/导入，
real-demo audit 命令，以及 public two-panel teaching HTML profile。

它还没有提交到仓库的本地 GVHMR/GMR execution environment、完整 simulator runtime
pipeline、默认真实 GMR-derived G1 replay、已提交 generated motion artifact、
production Viser UI，或已发布 real demo。本机 real GVHMR proof 只存在于 ignored
`outputs/` 下。当前命令面不再支持 Colab、hosted GPU provider、self-hosted
Actions GPU、operator-package，或 real-demo Pages-promotion workflows。
本机 real-demo audit 也会检查返回的 GVHMR 帧是否有可见动作，因此静止的片头裁剪不会
被当成完成的教学回放。

## 运行

```bash
make verify
make demo-public-browser
make real-gpu-prep LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin REAL_DRY_RUN=0
make gvhmr-inspect GVHMR_RESULT=path/to/hmr4d_results.pt
make real-artifact-intake REAL_ARTIFACT_SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json REAL_ARTIFACT_GVHMR_JSON=path/to/gvhmr-smplx-joints.json
make verify-real
make smoke-public
```

完整命令列表、blockers 和下一步安全任务见 [`STATUS.md`](STATUS.md)。

## 项目文档

- [`STATUS.md`](STATUS.md) — 当前事实、可运行命令、blockers 和 CI 证据
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — MVP 数据流、子系统边界、contracts 和验证边界
- [`docs/technical-roadmap.md`](docs/technical-roadmap.md) — 背景技术调研
- [`docs/humanoid-platform-evaluation.md`](docs/humanoid-platform-evaluation.md)
  — 为什么 MVP 采用 SMPL-X + G1 双轨
- [`docs/runbooks/gvhmr-local-gpu.md`](docs/runbooks/gvhmr-local-gpu.md) —
  当前本机 GVHMR run 路径

## 约束

- 不要提交 raw videos、generated motion files、rendered videos、checkpoints、
  logs 或大输出。
- 官方教学视频需要按 licensing-sensitive 处理；除非权利已确认，否则优先使用本地或
  用户提供的 source media。
- 不要把 fixture demo 当成真实 GVHMR/GMR/simulator 证明。
- 不要把 G1 当成评分来源。
