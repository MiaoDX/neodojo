# neodojo

[English](README.md) · **中文**

> *"This is the Construct. It's our loading program.*
> *We can load anything, from clothing, to equipment,*
> *weapons, training simulations..."*
>
> — Morpheus, *The Matrix* (1999)

---

## I know kung fu.

27 年后，我们终于真的有了一个 Construct。

不是用来加载武器，也不是用来加载战斗程序。这一次，Construct 加载的是
**八段锦、五禽戏、易筋经**——以及未来更多需要"看见标准动作"的人体技艺。

**neodojo** 是一个为 *kung fu*（广义的"功夫"——气功、太极、武术、导引术）打造
的仿真训练场。它把官方教学视频转成 humanoid 仿真器里的关节轨迹，提供多视角
渲染和关节轨迹叠加，让你看清楚每一个动作的"标准影子"长什么样。

把这个影子加载到你的训练循环里——就像 Morpheus 把功夫程序加载到 Neo 的头脑里。

---

## What it does

- **The Loading Program** — 官方教学视频 → 单目 3D 姿态估计 → SMPL-X 全身参数 → humanoid 关节轨迹
- **The Sparring Partner** — SMPL-X 人体模型 + Unitree G1 humanoid 双轨同屏，一个负责精度，一个负责"看起来像 Neo 的对手"
- **Show Me** — 正 / 侧 / 俯三视角同步渲染 + 手腕 / 肘 / 膝关节轨迹叠加
- **Free Your Mind** — 学员摄像头实时对比模式（后续）

---

## Why "kung fu" (not just qigong)

"kung fu" 在英语里早就超越了"武术"的字面意义——它泛指**通过长期练习获得的身体技艺**。

> *"There is no try."*
> *"There is no shortcut."*

气功、太极、八段锦、五禽戏、易筋经、瑜伽体式、康复训练里的标准动作……都属于这个
广义的 *kung fu*。项目命名留出空间，让未来不被第一个用例锁死。

**第一批要加载的程序，是健身气功**——因为它们是国家体育总局公开推广、有标准
教学视频、动作慢且适合 SMPL-X 姿态估计的最佳起点。

---

## First instances

来自国家体育总局健身气功管理中心 & 中国健身气功协会的官方教学视频：

- [ ] 健身气功·八段锦
- [ ] 健身气功·五禽戏
- [ ] 健身气功·易筋经
- [ ] 健身气功·六字诀
- [ ] 健身气功·大舞
- [ ] 健身气功·马王堆导引术
- [ ] 健身气功·十二段锦
- [ ] 健身气功·太极养生杖
- [ ] 健身气功·导引养生功十二法
- [ ] 校园五禽戏（小学 / 初中 / 高中版）
- [ ] 明目功（青少 / 成人版）

---

## Tech stack at a glance

项目当前事实见：

- 📄 [`STATUS.md`](STATUS.md) — 当前状态、约束与下一步安全任务
- 📄 [`ARCHITECTURE.md`](ARCHITECTURE.md) — MVP 数据流、子系统边界与验证边界

完整技术路线、SOTA 模型对比、机器人平台评估、失败模式分析见以下背景文档：

- 📄 [`docs/technical-roadmap.md`](docs/technical-roadmap.md) — 端到端 pipeline 调研（GVHMR / GMR / Genesis / Viser / KungfuBot 等）
- 📄 [`docs/humanoid-platform-evaluation.md`](docs/humanoid-platform-evaluation.md) — 为什么 G1 + SMPL-X 双轨，而不是等"完美 humanoid"

核心 pipeline:

```
官方教学视频
  │
  ▼
GVHMR (单目视频 → SMPL-X，含手部 22+15 关节)
  │
  ▼
GMR (SMPL-X → humanoid joint，CPU 实时，支持 15 种机器人)
  │
  ├─→ SMPL-X kinematic playback (主：教学精度无损)
  └─→ Unitree G1 kinematic playback (辅：视觉吸引力)
  │
  ▼
MuJoCo / Genesis 多相机离屏渲染
  │
  ▼
Viser (web 端三视角同步 + 关节轨迹 polyline + 时间轴)
```

---

## Why this exists (the unfair advantage)

> *"I'm trying to free your mind, Neo. But I can only show you the door.*
> *You're the one that has to walk through it."*

跟着一个完整套路视频练气功最大的问题是：**你只有一个视角**。

- 老师在屏幕里转身做"鹿抵"，你看不见他的脚怎么走的；
- 你做"双手托天"做了半年，没人告诉你你的肩其实没沉、肘其实没坠；
- 你想知道自己的「白鹤亮翅」最高点离标准差几度，但没有镜子能告诉你。

**neodojo 把单视角视频里的标准动作还原成 3D，让你从任何角度看清它。**
更进一步——把你自己练习的视频也丢进同一个 pipeline，叠加在标准动作旁边对照。

这不是 prompt engineering，不是 context engineering，是 **kinematic engineering**：
为人类学习身体技艺设计一个 Construct。

---

## Status

🚧 **Bootstrap 阶段，已有 fixture-only HTML demo。**

当前 repo 状态、已知约束与下一步安全任务见 [`STATUS.md`](STATUS.md)。现在已经有
一个很小的 Python package、本地 SMPL-X 与 G1 fixture artifact 命令、教学 playback
HTML 命令、规范化 imported-GMR G1 track 边界、静态 HTML demo 生成器，以及基于
model descriptor 与 visual track 的本地 G1 SVG/HTML render evidence、GMR 原生
pickle 规范化、dependency-light 的 SMPL-X surface proxy、可选 MuJoCo offscreen
mesh render evidence、本地外部 SMPL-X mesh-frame import 边界、可选 true Rerun
SDK `.rrd` export、可选 first Viser local
runtime 与 production teaching review-loop contract、generated roboharness-style
capture bundle manifest、可选 browser-rendered public-demo screenshot capture、
可选 MuJoCo simulator recorder-capture integration，以及最小 lint/build/quality-check
命令。它也可以为后续 GPU GVHMR run 写出 dry-run 或
ffmpeg-backed 的本地 source-video handoff，并写出 GPU handoff metadata package、
copyable input bundle、executable GPU-side runner、ignored transfer archive、
可选 self-hosted GPU workflow，以及 guarded manual real-demo Pages promotion
workflow。但还没有提交到仓库的本地 GVHMR/GMR execution environment、完整
simulator runtime pipeline、内置 official SMPL-X body-model renderer、production
live-client Viser capture，或 end-to-end 的真实 generated motion artifact。

Fixture-only public demo：[`https://miaodx.com/neodojo/`](https://miaodx.com/neodojo/)

![Fixture-only neodojo public demo screenshot](https://miaodx.com/neodojo/screenshot.svg)

现在可以运行：

```bash
make verify
make lint
make check
make test
make build
make demo-public
make demo-public-browser
make real-gpu-archive LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin
make real-gpu-run-request LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin
make real-gpu-colab-notebook LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin
make real-gpu-operator-package LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin
make real-handoff LOCAL_VIDEO=path/to/local-source.mp4
make real-handoff LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin REAL_LOCAL_TITLE="Local Baduanjin proof clip"
make real-handoff-smoke
make gpu-handoff SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json
make gpu-input-bundle GPU_HANDOFF=outputs/gvhmr-gpu-handoff GPU_INPUT_INCLUDE_MEDIA=1
make gpu-input-bundle-smoke
make gpu-input-archive GPU_INPUT=outputs/gvhmr-gpu-input
make gpu-input-archive-smoke
make gpu-execution-probe
make gvhmr-run-request GPU_INPUT_ARCHIVE=outputs/gvhmr-gpu-input-archive
make gvhmr-run-request-smoke
make gvhmr-colab-notebook GVHMR_RUN_REQUEST=outputs/gvhmr-gpu-run-request
make gvhmr-colab-notebook-smoke
make gvhmr-inspect GVHMR_RESULT=outputs/real-conversion-gate/hmr4d_results.pt
make real-artifact-intake REAL_ARTIFACT_GVHMR_JSON=path/to/gvhmr-smplx-joints.json
make real-artifact-intake-smoke
make real-conversion-audit
make real-demo-pages-promotion-validate PROMOTION_DOWNLOAD_ROOT=outputs/promoted-real-demo-download PROMOTION_SOURCE_RUN_ID=123456789
make demo-real SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json GVHMR_JSON=outputs/real-conversion-gate/gvhmr-smplx-joints.json
make smoke-public
PYTHONPATH=src python -m neodojo motion-record create --out outputs/motion-contract
PYTHONPATH=src python -m neodojo motion-record create --from-gvhmr-json path/to/gvhmr-smplx-joints.json --out outputs/motion-contract
PYTHONPATH=src python -m neodojo smplx-surface proxy --motion-record outputs/motion-contract --out outputs/smplx-surface
PYTHONPATH=src python -m neodojo smplx-surface register-assets --model path/to/SMPLX_NEUTRAL.npz --license "local licensed SMPL-X asset; do not commit" --out outputs/smplx-assets
PYTHONPATH=src python -m neodojo smplx-surface mesh --motion-record outputs/motion-contract --asset-descriptor outputs/smplx-assets/assets/smplx/manifest.json --mesh-frames path/to/smplx-mesh-frames.json --out outputs/smplx-mesh
PYTHONPATH=src python -m neodojo annotations detect --motion-record outputs/motion-contract --out outputs/annotations
PYTHONPATH=src python -m neodojo robot-model register --robot unitree_g1 --fixture --out outputs/g1-visual
PYTHONPATH=src python -m neodojo tracks build --motion-record outputs/motion-contract --robot unitree_g1 --model-descriptor outputs/g1-visual/robot-models/unitree_g1/manifest.json --out outputs/g1-visual
PYTHONPATH=src python -m neodojo tracks normalize-gmr-pkl --source path/to/gmr-motion.pkl --motion-record outputs/motion-contract --out outputs/gmr-native
PYTHONPATH=src python -m neodojo tracks import-gmr-json --source path/to/gmr-unitree-g1.json --motion-record outputs/motion-contract --out outputs/g1-visual
PYTHONPATH=src python -m neodojo render g1 --model-descriptor outputs/g1-visual/robot-models/unitree_g1/manifest.json --g1-track outputs/g1-visual/tracks/g1/manifest.json --allow-fixture-model --out outputs/g1-render
PYTHONPATH=src python -m neodojo render mujoco-g1 --model-descriptor path/to/registered-g1-model/manifest.json --g1-track outputs/g1-visual/tracks/g1/manifest.json --out outputs/g1-mujoco-render
PYTHONPATH=src python -m neodojo demo play --motion-record outputs/motion-contract --g1-track outputs/g1-visual/tracks/g1/manifest.json --smplx-surface outputs/smplx-surface/surfaces/smplx/manifest.json --out outputs/teaching-demo
PYTHONPATH=src python -m neodojo demo export-rerun --playback outputs/teaching-demo/manifest.json --g1-render outputs/g1-render/manifest.json --out outputs/public-demo/neodojo-demo.rrd
PYTHONPATH=src python -m neodojo demo export-rerun --playback outputs/teaching-demo/manifest.json --g1-render outputs/g1-render/manifest.json --use-rerun-sdk --out outputs/public-demo/neodojo-demo.rrd
PYTHONPATH=src python -m neodojo demo serve-viser --playback outputs/teaching-demo/manifest.json --g1-render outputs/g1-render/manifest.json --out outputs/viser-runtime
PYTHONPATH=src python -m neodojo demo browser-smoke --public-demo outputs/public-demo --out outputs/browser-capture
PYTHONPATH=src python -m neodojo capture recorder --simulator-render outputs/g1-mujoco-render --out outputs/recorder-capture
PYTHONPATH=src python -m neodojo capture bundle --public-demo outputs/public-demo --viser-runtime outputs/viser-runtime --g1-render outputs/g1-render --out outputs/capture
PYTHONPATH=src python -m neodojo capture bundle --public-demo outputs/public-demo --viser-runtime outputs/viser-runtime --g1-render outputs/g1-render --browser-capture outputs/browser-capture --out outputs/capture
PYTHONPATH=src python -m neodojo capture bundle --public-demo outputs/public-demo --viser-runtime outputs/viser-runtime --g1-render outputs/g1-render --recorder-capture outputs/recorder-capture --out outputs/capture
PYTHONPATH=src python -m neodojo real-conversion prepare --id 03-006 --start 0 --end 12 --out outputs/real-conversion-gate
PYTHONPATH=src python -m neodojo real-conversion prepare --local-source-id local-baduanjin --local-video path/to/local-source.mp4 --local-title "Local Baduanjin proof clip" --start 0 --end 12 --out outputs/real-conversion-gate
PYTHONPATH=src python -m neodojo real-conversion materialize-source --prep outputs/real-conversion-gate/real-conversion-prep.json --local-video path/to/local-source.mp4 --dry-run --out outputs/real-conversion-source
PYTHONPATH=src python -m neodojo real-conversion package-gpu-handoff --source-materialization outputs/real-conversion-source/source-materialization.json --out outputs/gvhmr-gpu-handoff
PYTHONPATH=src python -m neodojo real-conversion package-gpu-input --gpu-handoff outputs/gvhmr-gpu-handoff --include-media --out outputs/gvhmr-gpu-input
PYTHONPATH=src python -m neodojo real-conversion archive-gpu-input --gpu-input outputs/gvhmr-gpu-input --out outputs/gvhmr-gpu-input-archive
PYTHONPATH=src python -m neodojo real-conversion probe-gpu-execution --out outputs/gvhmr-gpu-execution-probe
PYTHONPATH=src python -m neodojo real-conversion inspect-gvhmr-result --source outputs/real-conversion-gate/hmr4d_results.pt --out outputs/gvhmr-result-inspection
PYTHONPATH=src python -m neodojo real-conversion validate-source --source-materialization outputs/real-conversion-source/source-materialization.json --gvhmr-json outputs/real-conversion-gate/gvhmr-smplx-joints.json --out outputs/real-conversion-validation
PYTHONPATH=src python -m neodojo real-conversion import-demo --source-materialization outputs/real-conversion-source/source-materialization.json --gvhmr-json outputs/real-conversion-gate/gvhmr-smplx-joints.json --out outputs/real-demo
make demo-html
```

`neodojo motion-record create` 会写出 fixture-backed SMPL-X motion-record 和
teaching-track manifests，也可以通过 `--from-gvhmr-json` 导入外部 GVHMR
SMPL-X teaching-joints JSON export。如果这个 JSON 同时包含 `smplx_parameters`，
importer 会保留 mesh-ready pose/shape parameter metadata，并写出
`motion-record/smplx-parameters.json`，供未来 licensed mesh path 使用。当前 repo
仍不会在本地运行 GVHMR，也不会直接解析 raw GVHMR `.pt` 文件；JSON 路径只是给后续
GPU run 准备的 CPU-side import 边界。

`neodojo annotations detect` 会为 opening stance、settled support、raised-hands
apex anchors 写出显式的 SMPL-X-only annotation manifest 和 routine feedback
report。`make demo-public` 会把这些 anchors 喂给 teaching playback，而不是依赖隐式
final frame。

`neodojo smplx-surface proxy` 会从 SMPL-X teaching joints 生成一个 dependency-light
capsule surface proxy，用于 teaching/public demo 的视觉检查。它不会生成 licensed
SMPL-X body-model mesh，所有反馈仍然只读取 SMPL-X joints。
`neodojo smplx-surface register-assets` 可以为已有的本地 licensed SMPL-X model
file 写出 local-only descriptor，不会复制 asset。`neodojo smplx-surface mesh`
会把外部 licensed SMPL-X renderer 写出的本地
`neodojo.smplx_mesh_frames.v1` JSON 导入成
`neodojo.smplx_mesh_surface.v1` visual layer。它会验证 local asset
descriptor、imported `smplx_parameters`、frame count、vertices、faces 和
scoring boundary，然后让 teaching/public playback 引用这份 mesh evidence。
当前 repo 仍不会自己执行或再分发 official SMPL-X model assets。

`neodojo robot-model register` 和 `neodojo tracks build` 可以写出 fixture G1
model 和 visual-track manifests。它们保留 SMPL-X/G1 职责边界，但仍不会在本地运行
GMR retargeting。`neodojo tracks normalize-gmr-pkl`
可以解析 upstream `scripts/*_to_robot.py --save_path` 写出的 YanjieZe/GMR 原生
robot-motion pickle，并转成 repo 内部使用的规范化 JSON contract。`neodojo tracks
import-gmr-json` 可以把规范化的外部 `neodojo.gmr_unitree_g1_track.v1` export（含
Unitree G1 joint-angle frames）导入同一个不可评分的 G1 track contract；它不会在
本地运行 GMR，也不宣称支持所有 upstream GMR 原生输出格式。

`neodojo render g1` 会读取 G1 model descriptor 与 G1 visual-track manifest，
写出正/侧/俯三视角 SVG frame evidence、本地 HTML 页面与 render manifest。
fixture descriptor 必须显式传入 `--allow-fixture-model`；注册过的 URDF/MJCF
descriptor 不需要这个开关。这是本地 render evidence，不是 MuJoCo/Genesis
仿真器 mesh 渲染。
`neodojo render mujoco-g1` 是可选的 MuJoCo offscreen renderer，用于注册过的
URDF/MJCF descriptor。它需要安装 `sim` extra 或 `mujoco` package，并使用本地、
未追踪的机器人 assets 来做真实 Unitree G1 proof；内置 optional smoke 只用一个
tiny synthetic MJCF model 验证这条路径，real asset-load path 也已用未追踪的本地
`unitreerobotics/unitree_mujoco` `g1_29dof.xml` clone 验证。如果 G1 track 含有
imported `unitree_g1_joint_angles` pose stream，renderer 会把匹配到的 MuJoCo
hinge/slide joints 应用到所选 render frame 的 `qpos`，并在 manifest 中记录
applied、missing、skipped、clipped joints。

`neodojo demo play` 会把 SMPL-X motion-record、可选 SMPL-X surface proxy 或
mesh surface 和 G1
visual-track manifests 一起读入，并写出 `outputs/teaching-demo/index.html` 与
playback manifest。这是一个 simulator-light HTML inspection path：SMPL-X joints
仍是 scoring source，surface layer 只用于视觉检查，G1 仍然不可用于评分。它也可以通过
`--reference-video` 保留可选的本地-only 原视频同步元数据。

`neodojo demo export-rerun` 会写出内部 scene/timeline contract、fixture-only
静态 public-demo HTML 页面、SVG screenshot，以及 `outputs/public-demo/` 下的
`.rrd` 命名 recording artifact。默认情况下，这个 `.rrd` 文件是如实标注的 JSON
fallback artifact，不是真正的 Rerun SDK recording。安装 optional `rerun` extra
后，传入 `--use-rerun-sdk` 会写出真正的 Rerun SDK recording，并在 public-demo
manifest 中标记 `rerun.actual_rrd: true`。

`neodojo demo serve-viser` 会写出 `outputs/viser-runtime/scene.json`、Viser
runtime manifest，以及 generated front/side/top preview screenshots，然后从同一个
scene/timeline contract 启动可选的本地 Viser server。除非使用
`--write-contract-only`，否则它需要安装 `viser` extra 或 `viser` package。runtime
会以同步 3D tracks 展示 SMPL-X 和 G1，包含 frame slider、frame-step controls、
playback-speed metadata、trajectory overlays、camera-preset metadata/buttons、
annotation-anchor navigation、layer visibility toggles、feedback drilldown，以及显式的
SMPL-X scoring/G1 visual labels。manifest 里包含
`neodojo.viser_teaching_ui.v1` review-loop metadata；live-client Viser browser
capture 仍是 follow-on work。

`neodojo capture bundle` 会写出 `outputs/capture/manifest.json`，这是一个
generated roboharness-style multi-camera evidence manifest。它会验证 public-demo
artifacts、Viser front/side/top preview screenshots、G1 front/side/top render
frames，并保留 `scoring_source: smplx` 与 `g1_scoring_allowed: false`。传入
`--browser-capture` 时，它会收录 `neodojo demo browser-smoke` 生成的真实
headless Chromium public-demo screenshot manifest。传入 `--recorder-capture`
时，它会收录 `neodojo capture recorder` 生成的可选 MuJoCo simulator-recorder
evidence；直接 roboharness 与 live-runtime recording 仍是 follow-on work。

`make verify` 会一次运行 lint、MVP plan quality checks、tests、wheel build、
public-demo + capture-bundle smoke lane、dry-run real-handoff smoke lane，以及
metadata-only GPU input bundle/archive smoke lanes、GPU execution probe 和
fixture-only real-artifact intake smoke lane、real-conversion completion audit。
`make demo-public` 会用一个本地命令重新生成 fixture motion contract、detected
annotations、SMPL-X surface proxy、G1 visual track、G1 render evidence、teaching
playback、Viser runtime preview、public-demo artifact、generated capture bundle，
并运行 smoke check。
`make demo-public-browser` 会跑同一条 lane，然后使用 optional Playwright browser
extra 在 Chromium 中渲染 public-demo HTML，写出
`outputs/browser-capture/public-demo-browser.png`，并把 browser evidence 刷进
capture bundle。
`make smoke-public` 会验证现有的
`outputs/public-demo` artifact set。
`.github/workflows/public-demo.yml` 里的 GitHub Actions workflow 会运行同一条 fixture
lane、browser capture 和 metadata-only real/GPU smoke lanes，上传 real-handoff、
GPU input bundle、GPU input archive、GPU run-request、GPU execution probe、
real-artifact intake smoke artifacts，以及 public-demo、browser-capture 与
capture-bundle artifacts，并在 repository variable `NEODOJO_DEPLOY_PAGES=true`
时把 fixture-only public demo 发布到 GitHub Pages。
`make lint` 目前是 syntax/import bytecode compile check；`make check` 会验证
MVP plan links 和最低限度的 plan scaffolding；`make build` 会把 wheel 写到被忽略的
`outputs/dist/`。

`neodojo real-conversion prepare` 会为后续 GPU gate 写出 source metadata、trim
metadata 和下一步命令提示。它不会下载源视频，也不会运行 GVHMR。如果传入
`--local-video`，它会记录 checksum 数据和可选的 ffprobe duration、resolution、codec、
frame-rate metadata。对于本地/用户提供且不应套用 official source index row 的视频，
可以同时传 `--local-source-id` 和 `--local-video`，保留自定义 provenance。
`neodojo real-conversion materialize-source` 会读取这个 prep
manifest 与本地视频，写出 source-materialization manifest。传入 `--dry-run` 时，
它只记录准确的 ffmpeg trim 与 reference-frame extraction 命令，不处理媒体；不传
`--dry-run` 时，它需要 ffmpeg，并把 ignored trimmed-video 与 reference-frame
artifacts 写给后续 GPU GVHMR input。`make real-handoff LOCAL_VIDEO=...` 会用一个
命令运行 source prep、默认 dry-run source materialization 和 GPU handoff packaging；
设置 `REAL_LOCAL_SOURCE_ID=...` 和可选 `REAL_LOCAL_TITLE=...` 可保留 custom
local-source provenance；安装了 ffmpeg 并希望实际 trim/extract media 时，可设置
`REAL_DRY_RUN=0`。
`make real-handoff-smoke` 会用 ignored placeholder `.mp4` 跑同一条 handoff path，并已
接入 `make verify`；它不会运行 GVHMR，也不会处理媒体。
`make real-gpu-archive LOCAL_VIDEO=...` 是给外部 GPU operator 的一命令本地打包路径：
它会运行非 dry-run source materialization、打包含媒体的 GPU input bundle，并写出被
忽略的 transfer archive。它需要 ffmpeg，并且只应用于允许转移到所选 GPU machine 的
本地/用户提供媒体。
`make real-gpu-run-request LOCAL_VIDEO=...` 会在这条本地打包路径后继续从生成的
archive 写出 GPU operator request manifest 和 README。`make
real-gpu-colab-notebook LOCAL_VIDEO=...` 会再多走一步，从该 request 写出 Colab-ready
operator notebook。`make real-gpu-operator-package LOCAL_VIDEO=...` 会把 archive、
request 和 notebook 放进一个 ignored operator package 目录，方便转交。
`neodojo real-conversion package-gpu-handoff`
和 `make gpu-handoff SOURCE_MATERIALIZATION=...` 会读取 source-materialization
manifest，写出 `outputs/gvhmr-gpu-handoff/manifest.json`、README、
`source-materialization.json` 副本、`gvhmr-smplx-joints.template.json`，以及
`export_neodojo_gvhmr.py`，用于保留 source hash、trim、input video checksum、预期
export schema、GPU-side export command 和返回本地 import command。这个 package
还包含 `run_gvhmr_neodojo.sh`，用于在 GPU machine 上包装 upstream GVHMR demo
command 和 neodojo exporter。这个 exporter helper 使用 bundle-local filenames，
设计为在 GPU 环境跑完 GVHMR 后使用，并需要 `torch`、`smplx` 和本地 licensed SMPL-X
assets；这个 package 不复制媒体，也不会在本地运行 GVHMR。
`neodojo real-conversion package-gpu-input` 和 `make gpu-input-bundle
GPU_HANDOFF=... GPU_INPUT_INCLUDE_MEDIA=1` 会生成 ignored copyable GPU input
bundle，包含 `RUN_ON_GPU.md`、handoff metadata、runner script、exporter helper、
template，以及 materialized `source/trimmed-clip.mp4`。这个 bundle 只用于复制到选定的
GPU machine，不能提交或发布。`make gpu-input-bundle-smoke` 会验证 metadata-only
bundle 和 runner script，不复制媒体，也不运行 GVHMR。`neodojo real-conversion
archive-gpu-input` 和 `make gpu-input-archive GPU_INPUT=...` 会把这个目录打成
`neodojo-gvhmr-gpu-input.tar.gz`，并写出
`neodojo.gvhmr_gpu_input_archive.v1` manifest。metadata-only archive 可用于 CI；
包含媒体的 archive 仍必须留在 ignored outputs，不能提交或发布。archive 创建时会验证
transfer package 包含 GPU operator 需要的 runner script、exporter、template、
runbook、manifests 和 source metadata。持久化的外部 GPU operator checklist 在
[`docs/runbooks/gvhmr-external-gpu.md`](docs/runbooks/gvhmr-external-gpu.md)。
`make gvhmr-run-request GPU_INPUT_ARCHIVE=...` 会把已有 archive manifest 转成简洁的
operator request manifest 和 README，包含 archive hash、必需 GPU assets、手动运行命令
和本地 return commands。`make gvhmr-colab-notebook GVHMR_RUN_REQUEST=...` 会从这个
request 生成 Colab operator notebook，包含 checksum verification、guarded GVHMR
execution、returned JSON download 和本地 validation commands。`make
gvhmr-operator-package GPU_INPUT_ARCHIVE=... GVHMR_RUN_REQUEST=...
GVHMR_COLAB_NOTEBOOK=...` 会把这些生成的 handoff files 整理成一个包含 package
manifest 和 README 的 package。`make gvhmr-run-request-smoke` 会在 `make verify` 中覆盖
metadata-only request path；`make gvhmr-colab-notebook-smoke` 会覆盖 generated
notebook path；`make gvhmr-operator-package-smoke` 会覆盖 collocated package path。
如果使用用户自己管理的 GitHub Actions GPU 硬件，手动触发的
`.github/workflows/gvhmr-self-hosted-gpu.yml` workflow 可以在带 `gpu` label 的
self-hosted runner 上解压 runner-local media archive，运行同一个 packaged wrapper，
接着运行 `make real-artifact-intake` 和 strict real-conversion audit，并可选地只上传
`gvhmr-smplx-joints.json` 或 generated real-demo/public-demo evidence。它不会由 push
或 pull request 触发，也不会让默认 CI lane 运行 GVHMR。
`neodojo real-conversion probe-gpu-execution` 和 `make gpu-execution-probe`
会写出安全的本地/provider readiness manifest，只记录命令是否存在和环境变量名，不记录
secret value，也不会运行 GVHMR；它已接入 `make verify`，用于让 blocker
classification 可复现。
`neodojo real-conversion inspect-gvhmr-result` 和
`make gvhmr-inspect GVHMR_RESULT=...` 会在 GVHMR/GPU 环境安装了 optional `torch`
时检查返回的 `hmr4d_results.pt`，或者在默认本地环境检查 JSON summary。inspection
manifest 会记录 top-level keys、候选的 `smpl_params_global` / `smpl_params_incam`
parameter blocks，以及输入是否已经是 `neodojo.gvhmr_smplx_joints.v1` export。它仍不会
在本地转换 raw GVHMR `.pt` 文件。`neodojo real-conversion validate-source` 会把
GVHMR teaching-joints JSON export 与 source-materialization manifest 做 provenance 对照，
写出 validation report，并在 provenance 匹配时生成 validated import JSON copy。
`neodojo real-conversion import-demo` 和
`make demo-real SOURCE_MATERIALIZATION=... GVHMR_JSON=...` 会验证外部 GVHMR
export，把它导入 motion-record contract，并在 `outputs/real-demo/` 下重新生成同一条
annotations、SMPL-X surface、G1 visual/render、teaching playback、public-demo、
Viser preview 与 capture bundle lane。默认情况下，如果没有传入 `--g1-track` 和
`--model-descriptor`，或者没有给 `make demo-real` 传入 `G1_TRACK=...`
`MODEL_DESCRIPTOR=...`，它会派生 fixture G1 visual companion。它们仍不会在本地运行
GVHMR。
`make real-artifact-intake REAL_ARTIFACT_GVHMR_JSON=...` 是同一条 validated import
path 的更简单 post-return wrapper。使用标准路径时，它默认读取
`outputs/real-conversion-source/source-materialization.json` 并写入
`outputs/real-demo`，因此 GPU operator 返回 export 后只需要指定这个
`neodojo.gvhmr_smplx_joints.v1` JSON。
`make real-artifact-intake-smoke` 会写 fixture-only source materialization 与
GVHMR JSON 输入，再运行同一个 wrapper，让 returned-artifact intake path 在本地
和 CI 中都有覆盖，但不声称已经运行过真实 GVHMR。生成的 real-demo manifest 会用
`gvhmr_artifact_imported: true` 表示 contract import 已完成，并用
`real_gvhmr_artifact_imported: false` 表示这是 fixture smoke。
`make real-conversion-audit` 会写出
`outputs/real-conversion-audit/manifest.json`，判断 real gate 是否已完成，或是否仍
blocked on external GPU artifact。它在 blocker classification 状态下也会成功退出；
需要脚本在没有真实 non-fixture demo 时失败时，可使用
`make real-conversion-audit-strict` 或 `make verify-real`。底层 CLI 形式是
`PYTHONPATH=src python -m neodojo real-conversion audit-completion --require-complete`。
`make real-demo-pages-promotion-validate PROMOTION_DOWNLOAD_ROOT=...
PROMOTION_SOURCE_RUN_ID=...` 会在 guarded Pages promotion workflow 上传之前，
验证并 stage 已下载的 `neodojo-self-hosted-real-demo` artifact。它会拒绝
fixture-only import、未完成的 strict audit、不安全文件路径、非 SMPL-X scoring，
以及空白 public-demo 文件。

`make demo-html` 会写出 `outputs/html-demo/index.html`，这是一个由本地
motion/track manifest contract 支撑的自包含合成 fixture demo，用来验证目标教学
UI 的形态。它不证明源视频转换、气功动作精度、仿真器渲染、live-client Viser
capture 或真实 Unitree G1 retargeting 已经完成。

正在做的事情：

- [ ] 第一个端到端 demo：八段锦第一式「双手托天理三焦」
- [x] fixture-only web/HTML 教学 demo：同步 SMPL-X/G1 风格播放、轨迹叠加、
      时间轴控制，以及一个基于 SMPL-X 的几何检查
- [x] 本地 fixture SMPL-X motion-record 和 teaching-track manifests
- [x] 外部 GVHMR teaching-joints JSON 可导入同一 motion contract
- [x] 可选 imported SMPL-X pose/shape parameter contract，用于 licensed mesh evidence
- [x] dependency-light SMPL-X surface proxy layer，接入 teaching/public demos
- [x] local-only licensed SMPL-X asset descriptor 和 mesh-input validation
- [x] 本地 external licensed SMPL-X mesh-frame import，接入 teaching/public demos
- [x] 本地 fixture G1 model 和 visual-track manifests，并保持 scoring separation
- [x] 规范化外部 GMR Unitree G1 JSON import 到不可评分的 G1 visual-track contract
- [x] GMR 原生 robot-motion pickle 规范化到同一个 G1 JSON import contract
- [x] 本地 G1 SVG/HTML render evidence 命令，输出正/侧/俯三视角 frame，并保持
      `g1_scoring_allowed: false`
- [x] 可选 MuJoCo offscreen mesh render command，已用 tiny MJCF model smoke-test；
      real G1 asset-load path 也已用未追踪的本地 Unitree G1 asset clone 验证
- [x] imported GMR joint angles 可应用到匹配的真实 Unitree G1 MuJoCo qpos joints，
      用于 render evidence
- [x] 本地 teaching playback 命令，可同时消费 SMPL-X 与 G1 manifests
- [x] 确定性的 SMPL-X opening-form routine feedback review，包含多个 key-frame
      anchors 和 posture terms
- [x] fixture-only 静态 public-demo export，包含 scene/timeline contract、
      `.rrd` fallback artifact、HTML 与 SVG screenshot
- [x] 可选 true Rerun SDK `.rrd` export；live fixture-only GitHub Pages URL 已在
      [`https://miaodx.com/neodojo/`](https://miaodx.com/neodojo/) 验证
- [x] 可选第一版 Viser local runtime，包含同步 SMPL-X/G1 tracks、frame slider、
      camera/annotation controls、trajectory overlays 和 scoring-source labels
- [x] production Viser teaching review-loop contract，包含 frame stepping、
      playback-speed metadata、layer visibility toggles 和 feedback drilldown
- [x] 在一条命令 public-demo lane 中生成 Viser front/side/top preview screenshots
- [x] generated roboharness-style multi-camera capture evidence bundle，可验证
      public-demo、Viser preview 与 G1 render artifacts
- [x] 可选 browser-rendered Chromium screenshot capture，接入 CI capture bundle
- [x] 可选 MuJoCo simulator recorder-capture manifest；当本地 simulator assets
      可用时可以接入 capture bundle
- [x] 本地一条命令 `make demo-public`，以及用于 fixture public demo 的 GitHub
      Actions artifact/Page workflow
- [x] dry-run real-handoff smoke bundle 的 metadata-only CI artifact
- [x] GPU input bundle/archive/run-request smokes 和 GPU execution probe 的
      metadata-only CI artifacts
- [x] 最小 `make lint` 与 `make build` 命令面
- [x] project-owned `make check` quality gate，用于 MVP plan links/scaffolding
- [x] 本地一条命令 `make verify` 跑完 lint、quality checks、tests、build、
      public demo generation、real/GPU smoke lanes 和 real-artifact intake smoke
- [x] 本地 real-conversion prep manifest，默认 source 为 `03-006`
- [x] 带显式 provenance 的 custom local-source real-conversion prep path
- [x] 面向用户本地视频的 real-conversion source materialization handoff
- [x] 从用户本地视频一命令生成 GPU handoff 的 `make real-handoff`
- [x] 给外部 GPU operator 一命令生成含媒体 transfer archive 的 `make real-gpu-archive`
- [x] 一命令生成本地 archive 加 operator request 的 `make real-gpu-run-request`
- [x] 一命令生成本地 archive、operator request 和 Colab notebook 的
      `make real-gpu-colab-notebook`
- [x] 一命令生成 collocated archive、request、notebook 和 package manifest 的
      `make real-gpu-operator-package`
- [x] 本地 GVHMR GPU handoff package，包含 export template 与返回命令
- [x] ignored copyable GPU input bundle，可显式包含 trimmed media
- [x] ignored GPU input transfer archive，用于上传到选定的 GPU machine
- [x] 从 transfer archive 生成 external GPU run-request manifest 与 README
- [x] 从 GPU run-request manifest 生成 Colab operator notebook
- [x] 从 archive、run request 和 notebook manifests 生成 collocated operator package
- [x] 随 handoff 打包的 GPU-side GVHMR-to-neodojo export helper
- [x] 本地 GVHMR result inspection manifest，用于返回的 `.pt` 或 JSON export
- [x] 本地 GVHMR source-validation report 与 validated JSON import handoff
- [x] 外部 GPU GVHMR export 可用后的一命令本地 real-artifact import demo
- [x] 面向标准返回 GVHMR export 路径的简化 `make real-artifact-intake` wrapper
- [x] 用 fixture-backed `make real-artifact-intake-smoke` 覆盖 returned artifact
      wrapper
- [x] 用 `make real-conversion-audit` 为 real GVHMR gate 写出 executable blocker
      classifier
详细 implementation queue 放在 [`docs/plans/`](docs/plans/)，之后可以再同步成
GitHub issues。

---

## Related work in the MiaoDX ecosystem

- 🤖 [roboharness](https://github.com/MiaoDX/roboharness) — 给机器人仿真 agent 装上"眼睛"。neodojo 目前通过 generated capture bundle、browser-rendered public-demo screenshot 和 optional MuJoCo simulator recorder manifest 对齐它的多相机 evidence pattern；直接 roboharness integration 仍是 follow-on work
- 🦾 [robowbc](https://github.com/MiaoDX/robowbc) — roboharness 的全身控制 showcase

> *roboharness 给机器人请了个能看见自己的眼睛，*
> *neodojo 给人请了个永远在旁边演示的影子。*

---

## License & Acknowledgments

> *"There is no spoon."*

这里没有真正的机器人，只有仿真。但仿真已经够了——精度上限由 GVHMR、由 SMPL-X、
由 KungfuBot/PBHC 这条 motion-tracking 的研究脉络决定，**不由钢铁决定**。

致敬以下开源工作（详见 [`docs/technical-roadmap.md`](docs/technical-roadmap.md)
完整列表）：

- [GVHMR](https://github.com/zju3dv/GVHMR) (SIGGRAPH Asia 2024) — 单目视频→SMPL-X
- [GMR](https://github.com/YanjieZe/GMR) (ICRA 2026) — General Motion Retargeting
- [PBHC / KungfuBot](https://github.com/TeleHuman/PBHC) — 武术动作 humanoid 仿真前置工作
- [GR00T-WholeBodyControl](https://github.com/NVlabs/GR00T-WholeBodyControl) (NVIDIA) — humanoid 全身控制参考栈
- [Genesis](https://github.com/Genesis-Embodied-AI/Genesis) / [MuJoCo](https://github.com/google-deepmind/mujoco) — 仿真器
- [Viser](https://github.com/nerfstudio-project/viser) — web 3D 可视化
- 国家体育总局健身气功管理中心 & [中国健身气功协会](https://www.chqa.org.cn/) — 官方教学视频与功法标准

License: MIT (TBD)

---

## Contributing

> *"What if I told you... the dojo isn't the place. The dojo is the practice."*

Issues、PRs、想法、踩坑记录都欢迎。现阶段任何 feedback 都珍贵。

如果你是：

- **气功 / 太极 / 武术练习者**：你的"老师常说但视频看不出"的细节就是项目最缺的需求
- **HMR / humanoid 研究者**：欢迎 review 技术路线、指出更好的模型 / retargeting 方案
- **roboharness / AI coding agent 爱好者**：这是一个用 Claude Code routines 驱动开发的实验场

---

> *"I know kung fu."*
>
> *"Show me."*
