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
左侧是 SMPL-X skeleton teaching track，右侧是 Unitree G1 schematic evidence，
两侧共用同一个同步 timeline，并且只允许 SMPL-X 作为评分来源。只有在提供
non-fixture imported GMR joint-angle track 和 MuJoCo PNG frame sequence 时，
右侧才会标成 actual Unitree G1 MuJoCo model replay。它由
[`.github/workflows/public-demo.yml`](.github/workflows/public-demo.yml) 在 CI
中通过 `make demo-public-browser` 生成，上传为 `neodojo-public-demo` artifact，
并在 `main` 分支设置 `NEODOJO_DEPLOY_PAGES=true` 时发布到 GitHub Pages。

- 在线 fixture-only demo: [`https://miaodx.com/neodojo/`](https://miaodx.com/neodojo/)
- 生成文件：`index.html`、`manifest.json`、`scene.json`、`screenshot.svg`、
  `neodojo-demo.rrd`
- 当前 CI 证据：[`STATUS.md`](STATUS.md) 记录已验证的 GitHub Actions runs 和
  fixture-only Pages 状态。
- real-demo 的 source provenance 可以直接指向公开 source-video index。本机
  Baduanjin proof 使用 [`video/original_videos.md`](video/original_videos.md)
  里的 source `03-006`（`5八段锦两手托天理三焦`），trim `80s-92s`；demo 发布的是
  派生 skeleton/robot playback，不发布 source video。

![Fixture-only neodojo public demo screenshot](https://miaodx.com/neodojo/screenshot.svg)

## 当前状态

这个 repo 仍处于 bootstrap 状态。它已经有 fixture-backed motion、annotation、
SMPL-X surface、G1 visual-track、本地 render evidence、public-demo、
browser-smoke、capture-bundle、本地 GPU run 准备、本地 GMR run handoff/
normalization、roboharness G1 descriptor registration、返回 GVHMR export
检查/导入，real-demo audit 命令，以及 public two-panel teaching HTML profile。

它还没有提交到仓库的本地 GVHMR/GMR execution environment、完整 simulator runtime
pipeline、默认真实 GMR-derived G1 replay、已提交 generated motion artifact、
production Viser UI，或已发布 real demo。本机 ignored `outputs/` 下的 Baduanjin
`80s-92s` 可见动作片段 proof 现在已经通过 `make verify-real`：它包含
imported/native GMR Unitree G1 joint angles、non-fixture
roboharness/robot_descriptions MJCF descriptor、nonblank/changing MuJoCo PNG
frame sequence，并且 public HTML 会消费这些 replay frames。当前命令面不再支持
Colab、hosted GPU provider、self-hosted Actions GPU、operator-package，或
real-demo Pages-promotion workflows。本机 real-demo audit 也会检查返回的 GVHMR 帧
是否有可见动作，因此静止的片头裁剪不会被当成完成的教学回放。

## 运行

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

MuJoCo CI rendering 应该显式设置 OpenGL backend。GitHub-hosted Ubuntu 上，
`MUJOCO_GL=glfw` 配合 `xvfb-run -a` 是最实用的 smoke-test 路径。
安装 `libosmesa6` 后，`MUJOCO_GL=osmesa` 是 CPU headless 路径。
`MUJOCO_GL=egl` 更适合有可用 EGL 的 GPU/self-hosted runner。
如果要把可见差异和 backend setup failures 放在一个文件里人工比较，可以运行：

```bash
make mujoco-backend-compare MODEL_DESCRIPTOR=outputs/g1-visual/robot-models/unitree_g1/manifest.json G1_TRACK=outputs/g1-visual/tracks/g1/manifest.json
```

它会写出 `outputs/g1-mujoco-backend-comparison/index.html`。

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
- real demo 要在 docs/manifests 里保留公开 source-video provenance；不要从本 repo
  发布 raw source videos。
- 不要把 fixture demo 当成真实 GVHMR/GMR/simulator 证明。
- 不要把 schematic 右栏证据标成 actual G1 model replay。
- 不要把 G1 当成评分来源。
