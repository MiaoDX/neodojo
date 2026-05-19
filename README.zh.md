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
同一个 workflow 也会运行 `make ci-real-demo`，并把
`outputs/real-demo/public-demo/index.html` 上传为
`neodojo-real-demo-public-demo` artifact。默认这个 CI real-demo artifact 使用
[`samples/baduanjin-03-006-two-hands-80-92`](samples/baduanjin-03-006-two-hands-80-92)
里提交的派生 JSON sample：source provenance、返回的 GVHMR SMPL-X joints、
normalized GMR Unitree G1 joint angles。CI 会从这些 JSON 重新生成 G1 model
descriptor、MuJoCo frames 和 public HTML；raw source video 和 rendered outputs
仍然不进 git。

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
pipeline、production Viser UI，或已发布 real demo。仓库现在包含一个用于 CI 的
小型 Baduanjin derived JSON sample；raw video、native checkpoints、pickles、
rendered PNGs 和大 generated outputs 仍然 ignored。本机 ignored `outputs/` 下的
Baduanjin `80s-92s` 可见动作片段 proof 现在已经通过 `make verify-real`：它包含
imported/native GMR Unitree G1 joint angles、non-fixture
roboharness/robot_descriptions MJCF descriptor、nonblank/changing MuJoCo PNG
frame sequence，并且 public HTML 会消费这些 replay frames。当前命令面不再支持
Colab、hosted GPU provider、self-hosted Actions GPU、operator-package，或
real-demo Pages-promotion workflows。CI 现在会从 committed derived JSON 上传一个
sample-backed real-demo public HTML artifact。本机和 CI real-demo audit 也会检查
返回的 GVHMR 帧是否有可见动作，因此静止的片头裁剪不会被当成完成的教学回放。

## 运行

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

默认 MuJoCo G1 render 采用 roboharness `g1-reach` 的真实 scene 风格：wrapped
G1 MJCF scene、蓝色 skybox gradient、灰白 checker floor、roboharness lights、
原始 G1 materials，以及针对 raised-hands 气功回放调过构图的 named cameras。
这个 render target 使用 CI-compatible OpenGL 路径：`MUJOCO_GL=glfw` 配合
`xvfb-run -a`，默认 `1280x960`，输出到 `outputs/g1-mujoco-render`。GitHub
Actions 里有同一 backend 路径的 focused smoke test。

`make roboharness-g1-report` 会写出
`outputs/g1-roboharness-report/neodojo_g1_replay_report.html`，这是一个 sampled
roboharness checkpoint report，按 `start`、`early`、`middle`、`late`、`finish`
几个阶段展示 imported G1 track。

`MUJOCO_GL=osmesa` 仍然是安装 OSMesa system libraries 后的 CPU software headless
fallback。`MUJOCO_GL=egl` 更适合有可用 EGL 的 GPU/self-hosted runner。
如果要把可见差异和 backend setup failures 放在一个文件里人工比较，可以运行：

```bash
make mujoco-backend-compare MODEL_DESCRIPTOR=outputs/g1-visual/robot-models/unitree_g1/manifest.json G1_TRACK=outputs/g1-visual/tracks/g1/manifest.json
```

它会写出 `outputs/g1-mujoco-backend-comparison/index.html`。
如果要做重复计时 benchmark，可以运行：

```bash
make mujoco-backend-benchmark MODEL_DESCRIPTOR=outputs/g1-visual/robot-models/unitree_g1/manifest.json G1_TRACK=outputs/g1-visual/tracks/g1/manifest.json
```

它会写出 `outputs/g1-mujoco-backend-benchmark/benchmark.md` 和完整
`manifest.json`。

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
