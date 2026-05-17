# 健身气功 Humanoid 仿真演示工具：技术路线深度调研报告

> 这份文档是 neodojo 项目启动前的端到端技术调研。
> 它回答的问题是：**用今天 (2026 年 5 月) 公开的最 SOTA 模型与开源代码，
> 能否实现"官方教学视频 → humanoid 在仿真器中演示 + 多视角教学反馈"？**
> 简短答案：**绝大部分组件已经成熟到可以直接用。我们要做的不是基础研究，
> 是领域适配 + 教学交互层 + 数据/术语标注。**

---

## 目录

- [0. 总览与结论先行](#0-总览与结论先行)
- [1. GR00T-WholeBodyControl 的完整技术栈](#1-gr00t-wholebodycontrol-的完整技术栈)
- [2. 单目视频 → 3D 人体姿态 (SMPL/SMPL-X) 的 SOTA 方法](#2-单目视频--3d-人体姿态-smplsmpl-x-的-sota-方法)
- [3. SMPL → Humanoid Robot Retargeting 方案](#3-smpl--humanoid-robot-retargeting-方案)
- [4. 多视角生成模型（单视角视频 → 多视角）](#4-多视角生成模型单视角视频--多视角)
- [5. Text-to-Motion 与"要点文字"锚定关键帧](#5-text-to-motion-与要点文字锚定关键帧)
- [6. Humanoid 仿真器的多视角渲染与轨迹可视化](#6-humanoid-仿真器的多视角渲染与轨迹可视化)
- [7. 推荐整体技术栈（最终方案）](#7-推荐整体技术栈最终方案)
- [8. 真实限制与失败模式](#8-真实限制与失败模式必须看)
- [9. 进一步阅读与代码索引（汇总链接）](#9-进一步阅读与代码索引汇总链接)
- [10. 一句话总结](#10-一句话总结)

---

## 0. 总览与结论先行

我们想做的事情——「把官方健身气功视频（八段锦/五禽戏等）→ SMPL 人体姿态 →
Unitree G1/H1 等 humanoid 在仿真器中的关节轨迹 → 多视角渲染 + 轨迹可视化作为
教学反馈」——在 2024 下半年到 2026 年期间，已经被学术界把整条流水线**几乎全部
铺通**。

**最重要的一个发现**：已经有一篇 2025 年的论文 **KungfuBot (PBHC)**
([arXiv 2506.12851](https://arxiv.org/abs/2506.12851) /
[TeleHuman/PBHC](https://github.com/TeleHuman/PBHC)) 做的就是「视频 → SMPL →
Unitree G1 → 武术/舞蹈动作模仿」——**正是 neodojo 想做的事情，只是它面向高动态
武术（长拳、跳跃）和动态平衡 RL 控制，而我们面向慢速、几乎静态平衡的气功**。
这反而让 neodojo 更容易：因为气功几乎不需要训练动态平衡策略，可以纯 kinematic
playback。

**最简推荐栈（kinematic-only 演示）**：

```
官方气功视频
  → GVHMR (SMPL-X，世界坐标，最适合慢速连续动作)
  → GMR (General Motion Retargeting，已集成 GVHMR→G1)
  → MuJoCo or Genesis (kinematic replay，不跑 RL)
  → 多相机离屏渲染 + 关节轨迹 polyline overlay
  → LLM 解析「沉肩坠肘」等术语 → 关键帧锚点（人工标注 + 几何约束）
```

整套基本是 **「已成熟可直接用」**，唯一需要我们做的是：
1. 气功视频的版权与切片处理；
2. 教学层的关键帧 / 术语对齐；
3. roboharness 风格的可视化包装。

下面分六大方向详细展开。

---

## 1. GR00T-WholeBodyControl 的完整技术栈

### 1.1 仓库现状（截至 2026-05）

[NVlabs/GR00T-WholeBodyControl](https://github.com/NVlabs/GR00T-WholeBodyControl)
（约 1.1k stars，17 commits，6 contributors）是一个**「伞形」代码库**，里面装了
两条独立但互补的技术路线：

- **Decoupled WBC**：用于 NVIDIA Isaac-GR00T 的
  [N1.5](https://research.nvidia.com/labs/gear/gr00t-n1_5/) 和
  [N1.6](https://research.nvidia.com/labs/gear/gr00t-n1_6/) 模型的下层全身控制器，
  架构是 **「下半身 RL + 上半身 IK」** 的解耦设计，主平台是 Unitree G1。
- **GEAR-SONIC**：他们最新的 humanoid 行为基础模型
  ([whitepaper](https://nvlabs.github.io/GEAR-SONIC/)，
  [arXiv 2511.07820](https://arxiv.org/abs/2511.07820)，作者 Zhengyi Luo 等，2025-11)。
  SONIC 把「motion tracking」当成一个可扩展的训练任务，用单一统一策略学到走路 / 跑 /
  爬 / 跪 / 跳 / 双臂操作等核心运动技能，目标是作为更上层规划的「运动基础模型」。
  在 [HuggingFace nvidia/GEAR-SONIC](https://huggingface.co/nvidia/GEAR-SONIC) 发模型权重。

### 1.2 关键事实清单

| 提问 | 答案 |
|---|---|
| Humanoid 平台 | **Unitree G1 是主目标平台**（README、Decoupled WBC 文档、G1 SDK 都明确）。SONIC 论文里同时支持多平台。 |
| 仿真器 | **Isaac Lab 2.3.0**（README 上有 badge）+ 自家 C++ 推理栈 `gear_sonic_deploy`。Decoupled WBC 文档里还出现了 `--simulator robocasa` 选项。 |
| 训练数据 | "Large-scale human motion data" + "preprocessed large-scale human motion datasets"（TODO 里写要后续 release）；SONIC 论文里大量使用 **AMASS** 派生数据。 |
| Retargeting pipeline | **GR00T-WBC 仓库本身不直接提供完整 retargeting 工具链**。它在 Acknowledgments 里明确说代码 derived from [HybridRobotics/whole_body_tracking (BeyondMimic)](https://github.com/HybridRobotics/whole_body_tracking) 和 [Isaac Lab](https://github.com/isaac-sim/IsaacLab)。真正的 SMPL→G1 retargeting 由姐妹仓库 [NVlabs/ProtoMotions](https://github.com/NVlabs/ProtoMotions) 提供（见 §3）。 |
| 单目视频→humanoid 端到端流程 | **没有**直接的端到端 demo。仓库提供的是：(a) VR 头显（PICO）实时遥操作，(b) keyboard/gamepad 控制 kinematic planner，(c) ZMQ 通信用于第三方上层。如要从单目视频起跑，需要外挂 GVHMR 或 WHAM 等 HMR 模型，再喂进 ProtoMotions/GMR 做 retargeting，再 load 进 SONIC/Decoupled WBC 策略。 |
| 与 GR00T N1 / N1.5 / N1.6 的关系 | **互补关系**：N1/N1.5/N1.6 是 NVIDIA Isaac-GR00T 的 **上层 VLA（Vision-Language-Action）** 基础模型，输出"动作意图"；Decoupled WBC 是 **N1.5/N1.6 内部使用的下层全身控制器**，把上层意图落到 G1 关节命令上。GEAR-SONIC 则是更进一步的 motion-tracking 基础策略，独立于 N1.x 系列，是「行为基础模型」。 |
| 与 neodojo 项目的对齐度 | **高，但不必照搬**：他们的核心场景是 loco-manipulation 和 teleop；气功是几乎不需要动态平衡控制的 kinematic-dominant 任务，跑全套 sim2real RL 是过度工程。仿真器一致性（Isaac Lab）和 G1 URDF/MJCF 这些底层资源是直接复用的关键。 |

### 1.3 上游与下游开源组件

- **上游（依赖）**：
  - [HybridRobotics/whole_body_tracking](https://github.com/HybridRobotics/whole_body_tracking)
    = BeyondMimic ([arXiv 2508.08241](https://arxiv.org/abs/2508.08241))，RSS 2025
    workshop；提供「scalable motion tracking」框架，单套 hyperparam 跑通各种动作。
  - [isaac-sim/IsaacLab](https://github.com/isaac-sim/IsaacLab)。
- **姐妹仓库（同 NVlabs 组）**：
  - [NVlabs/ProtoMotions](https://github.com/NVlabs/ProtoMotions)：retargeting 与
    RL 训练框架，支持 IsaacGym/IsaacLab/Genesis/Newton 四套仿真后端，支持
    SMPL/SMPL-X/Unitree G1/H1/自定义形态，retargeting 已切换到基于 PyRoki 的方案。
  - [NVlabs/HOVER](https://github.com/NVlabs/HOVER)：把 OmniH2O 的 Isaac Gym 实现
    移到了 Isaac Lab。

---

## 2. 单目视频 → 3D 人体姿态 (SMPL/SMPL-X) 的 SOTA 方法

### 2.1 横向对比

| 方法 | 会议/年份 | 输出 | 全局轨迹 | 遮挡鲁棒性 | 速度 (RTX 4090) | 开源 | PA-MPJPE (3DPW) | 适合气功? |
|---|---|---|---|---|---|---|---|---|
| **WHAM** | CVPR 2024 | SMPL | ✅ (用 SLAM/陀螺仪) | 中（时序融合 2D KP） | ~200 fps batch / 9 fps online | ✅ [yohanshin/WHAM](https://github.com/yohanshin/WHAM)，[wham.is.tue.mpg.de](https://wham.is.tue.mpg.de/) | ≈SOTA（PA-MPJPE 约 35-37 mm 区间） | 良好 |
| **TRAM** | ECCV 2024 | SMPL + 全局 + scene SLAM | ✅ | 中 | 中等（多阶段） | ✅ [yufu-wang/tram](https://github.com/yufu-wang/tram) | 良好（处理移动相机） |
| **GVHMR** | SIGGRAPH Asia 2024 | **SMPL-X** | ✅（Gravity-View 坐标，长序列不漂） | 良（多任务学习 + 时序 RoPE） | 网络本身 0.28 s / 1430 帧 ≈ 极快；预处理 46 s | ✅ [zju3dv/GVHMR](https://github.com/zju3dv/GVHMR)，[主页](https://zju3dv.github.io/gvhmr/) | PA-MPJPE 比 WHAM 慢 0.3 mm，但全局/长序列更稳，且输出 SMPL-X 含手部 | **★最推荐** |
| **4D-Humans / HMR2.0** | ICCV 2023 | SMPL，逐帧 + PHALP tracker | ❌（相机系） | 中 | 实时 | ✅ [shubham-goel/4D-Humans](https://github.com/shubham-goel/4D-Humans) | 良 | 中等（无全局） |
| **NLF (Neural Localizer Fields)** | NeurIPS 2024 | SMPL/SMPL-X/SMPL-H 通用 | 通过 SMPLFitter 后处理 | 良（25M 标注帧训练） | 单图快 | ✅ [isarandi/nlf](https://github.com/isarandi/nlf) | 领先 EMDB/3DPW/AGORA | 良好（适合关键帧锚定） |
| **CameraHMR** | 3DV 2025 | SMPL，单图，相机内参联估 | ❌ | 中 | 快 | ✅ [CameraHMR](https://github.com/pixelite1201/CameraHMR) · [paper](https://arxiv.org/abs/2411.08128) | 良 | 良好（适合做 anchoring） |
| **PhysHMR** | 2025-10 | SMPL + 物理可行 | ✅ | 良 | 离线 | ✅ [fengq1a0/physhmr](https://github.com/fengq1a0/physhmr) · [paper](https://arxiv.org/abs/2510.02566) | 高质量但是离线 |

### 2.2 针对气功的选型建议

气功动作的特点是：
1. 慢；
2. 长（一套 5-8 分钟）；
3. 自遮挡多（含胸、抱球、侧身、转身背对镜头）；
4. 需要精确的肢体角度（不是位置）；
5. 几乎不离开站立支撑——所以「全局轨迹」反而不那么重要，
**局部姿态精度 + 时序一致性 + 鲁棒于遮挡** 才关键。

**首选 GVHMR**，原因：

1. 直接输出 **SMPL-X**（含手指 22+15 关节），气功有大量手势（推掌、勾手），
   SMPL 不够。
2. 重力对齐天然处理"立得正不正"；长序列不漂，对几分钟的整套套路友好。
3. 推理极快（一段几分钟视频 ≤ 1 分钟），适合做教学闭环。
4. 下游生态已经成熟：[YanjieZe/GMR](https://github.com/YanjieZe/GMR) 已经原生
   集成 `gvhmr_to_robot.py`；KungfuBot/PBHC、Diffuman4D、HOI 重建等 2025 年工作
   都用 GVHMR 当默认 HMR 模块。

**备选/集成**：

- 手部细节如果 GVHMR 不够，再叠 **HAMER**（[geopavlakos/hamer](https://github.com/geopavlakos/hamer)）
  做手指 fine-grained 优化（这是 2025 年很多 HOI 论文的标准做法）。
- 如果某些镜头有走位/摄影机移动，TRAM 比 GVHMR 多一步明确的 scene SLAM；但官方
  气功视频几乎都是固定机位 + 演员定位练习，**TRAM 优势用不上**。
- **WHAM** 是更早一代基线，论文复现广，但官方实现输出 SMPL 而非 SMPL-X，缺手指。
- **NLF** 是当前精度最高的单图模型之一，可以拿来做**关键帧 anchoring**（见 §5）：
  在某些公认的「定式」帧上做高精度 fitting，去校正 GVHMR 在该帧的输出。

### 2.3 真实精度上限提醒

- 3DPW/EMDB 上 PA-MPJPE 约 35-40 mm 是当前 SOTA，但 3DPW 是日常动作；**气功属于
  OOD（out of distribution）数据**：BEDLAM、AMASS 里没有显式的太极/气功子集，
  模型见过的最相近动作是 Yoga（少量）和 MoYo（瑜伽，AMASS 中有）。在气功视频上
  **实际误差大概率会比基准高 1.5-2 倍**（经验估计 70-100 mm），尤其是
  「丹凤朝阳」「抱球」这种自遮挡严重的姿势。
- 手部精度是单独问题：SMPL-X 手部参数从全身 HMR 模型估出来通常很糙，必须叠
  HAMER 或类似手部专用模型。
- **足部接触检测**对于"站桩稳不稳"很关键，GVHMR 内置 stationary probability
  预测，可以直接用来做姿态修正。

---

## 3. SMPL → Humanoid Robot Retargeting 方案

### 3.1 重要洞察：我们的场景不需要 RL！

KungfuBot/PBHC、OmniH2O、ExBody2、HumanPlus 这些方法的**最大开销在 RL policy
训练**（teacher 20 小时 + student 10 小时 GPU/policy），目的都是 **sim2real 部署
到真机**。但 neodojo 只要 **kinematic playback in simulator**（演示给用户看动作
长什么样），不需要物理可行性，更不需要 sim2real——所以只需要 retargeting 的
"前半段"：**SMPL 关节空间 → 机器人关节空间 + IK 解算**，**不需要后半段 RL
imitation**。

这一下子把工程量降到 1/10。

### 3.2 retargeting 方案横向对比

| 方法 | 论文 | 仓库 | retargeting 算法 | 支持 G1/H1 | 训练需求 | 开源 | 推荐度（kinematic-only） |
|---|---|---|---|---|---|---|---|
| **GMR** (General Motion Retargeting) | ICRA 2026 ([arXiv 2510.02252](https://arxiv.org/abs/2510.02252)) | [YanjieZe/GMR](https://github.com/YanjieZe/GMR) | 基于 Pinocchio + IK，**已集成 GVHMR→robot 一行命令** | ✅ G1/H1/H1-2/Booster T1/PND Adam Lite/Tienkung 等 15+ 种 | **无（CPU 实时）** | ✅ | **★★★★★ 首选** |
| **ProtoMotions retarget** | — | [NVlabs/ProtoMotions](https://github.com/NVlabs/ProtoMotions) | 基于 Mink（[kevinzakka/mink](https://github.com/kevinzakka/mink)）/PyRoki 的 IK | ✅ G1/H1/SMPL/SMPL-X | 无 | ✅ | ★★★★ |
| **PHC retarget** | [PHC: Perpetual Humanoid Control](https://arxiv.org/abs/2305.06456) ICCV 2023 | [ZhengyiLuo/PHC](https://github.com/ZhengyiLuo/PHC) | shape-aware 形状拟合 + 关节角优化 | 通过外挂支持 G1 | 无（retarget 本身），但配套 RL 复杂 | ✅ | ★★★（GMR 论文指出 PHC 易产生地面穿透） |
| **SMPLSim** | — | [ZhengyiLuo/SMPLSim](https://github.com/ZhengyiLuo/SMPLSim) | SMPL 仿真 humanoid 中间层 | 间接 | 无 | ✅ | ★★ |
| **H2O** | IROS 2024 | [LeCAR-Lab/human2humanoid](https://github.com/LeCAR-Lab/human2humanoid) | shape-fit + 单相机姿态 → zero-shot teleop | ✅ H1 主 | 重 | ✅ | ★（与 OmniH2O 同仓库） |
| **OmniH2O** | CoRL 2024 ([paper](https://omni.human2humanoid.com/resources/OmniH2O_paper.pdf)) | 同上 | + teacher-student RL + 多模态接口 | ✅ H1 主, G1 也支持 | **重（20+10 小时 GPU）** | ✅（CC BY-NC 4.0） | ★ |
| **HOVER** (NVIDIA) | — | [NVlabs/HOVER](https://github.com/NVlabs/HOVER) | OmniH2O 移到 Isaac Lab，含 mask 多模式 | ✅ H1 | 重 | ✅ | ★ |
| **ExBody / ExBody2** | RSS 2024 / [arXiv 2412.13196](https://arxiv.org/abs/2412.13196) | [exbody2.github.io](https://exbody2.github.io/) | 关键点+速度跟踪，teacher-student CVAE | ✅ G1/H1 | 重 | ✅ | ★ |
| **HumanPlus** | CoRL 2024 | [MarkFzp/humanplus](https://github.com/MarkFzp/humanplus) | AMASS retarget + transformer policy (HIT) | ✅ H1 | 重 | ✅ | ★ |
| **PBHC / KungfuBot** | [arXiv 2506.12851](https://arxiv.org/abs/2506.12851), 2025-06 | [TeleHuman/PBHC](https://github.com/TeleHuman/PBHC) | 视频→SMPL（HMR）→物理过滤→Mink **或** PHC 双流水线→G1 | ✅ G1 主 | 重（每条动作单独 RL） | ✅ | ★★（**它的 motion processing 子模块单独使用很有价值**） |
| **UHC (Universal Humanoid Controller)** | NeurIPS 2021/2022 | [ZhengyiLuo/UHC](https://github.com/ZhengyiLuo/UHC) | SMPL/SMPL-H/SMPL-X humanoid MuJoCo 控制器 | ✅ 直接 SMPL 形态 | 训练（kinpoly/embodied pose） | ✅ | ★★★（**SMPL kinematic playback 的事实标准基础设施**） |
| **PoseTron** | [PoseTron (HRI 2024)](https://dl.acm.org/doi/10.1145/3610977.3634948) | 学术 | 主要做多人意图预测/姿态识别，retargeting 路径较弱 | 部分 | 学术 | 半开源 | ★（与 G1 兼容性差） |

### 3.3 推荐组合

**首选 [YanjieZe/GMR](https://github.com/YanjieZe/GMR)**。原因：

1. **作者明确把"GVHMR 单目视频 → robot motion"做成了一条命令**
   （`scripts/gvhmr_to_robot.py --robot unitree_g1 --record_video`，2025-09-16 commit）。
   这就是 neodojo 项目的最小可行流水线。
2. CPU 实时，无需训练，无需 GPU。
3. 同一作者还写了
   [awesome-humanoid-robot-learning](https://github.com/YanjieZe/awesome-humanoid-robot-learning)，
   整个 humanoid learning 生态都跟着他的命名约定走。
4. 论文里的用户研究显示 **GMR 的"对源动作忠实度"接近 Unitree 闭源数据集，超过
   PHC 和 ProtoMotions**，是当前 G1 retargeting 综合最优的开源方案。
5. **GMR 是 ICRA 2026 接收论文**，活跃维护，2025-08 至 2025-12 持续加新机器人
   （Booster K1/T1、Berkeley Humanoid Lite、Unitree H1/H1-2、Tienkung、PND Adam
   Lite、Talos、TWIST2 等）。

**备选/补充**：

- **PBHC 的 `smpl_retarget/` 子模块**：单独抠出来用，因为它已经针对武术类动作
  做了 contact mask 过滤和 motion correction，对气功的稳定站桩处理可能更友好。
  它本身支持 Mink 和 PHC 两条 retargeting 后端可选。
- **UHC**：如果想纯 SMPL kinematic playback（不经过任何机器人形态），UHC 提供
  现成的 SMPL/SMPL-H/SMPL-X MuJoCo humanoid。这是 neodojo 双轨方案里"SMPL 主轨"
  的基础设施（见 [`humanoid-platform-evaluation.md`](humanoid-platform-evaluation.md)）。
- **ProtoMotions**：如果最终决定走 Isaac Lab / Genesis 多后端方案，ProtoMotions
  是与 GR00T-WBC 同一 NVIDIA 团队、技术栈最一致的选择。

### 3.4 真实失败模式

- **足部穿透/打滑**：所有 IK retargeting 在身高/腿长不匹配时都会发生，需要
  contact mask 修正（PBHC 已实现）或把脚踝硬 clamp 到地面（GMR 提供 rate_limit
  选项）。
- **躯干自由度差异**：G1 腰部 3 DOF，人体腰部 ~6 DOF，"探海""含胸"这类涉及大幅
  躯干屈伸的动作会显著降质。这对气功是真实痛点，因为「拔背」「含胸」「沉肩」
  恰恰都依赖躯干微调。详见
  [`humanoid-platform-evaluation.md`](humanoid-platform-evaluation.md)。
- **手势 vs G1 末端**：G1 标配是 1-DOF 夹爪/3-DOF 简手，气功的「勾手」「立掌」
  无法精确表达。若想表达手势，必须切到 G1+灵巧手版本或者在可视化层单独画手指
  mesh。

---

## 4. 多视角生成模型（单视角视频 → 多视角）

### 4.1 候选模型

| 模型 | 出处 | 输入 | 输出 | 长视频支持 | 时序一致性 | 开源 |
|---|---|---|---|---|---|---|
| **CAT4D** | Google DeepMind, [arXiv 2411.18613](https://arxiv.org/abs/2411.18613) | 单目视频 | 多视角视频 + 可变形 3D Gaussian | **原生仅 16 帧/批**，需 sliding 采样外推 | 中等，长序列衰减 | 论文公开，代码未完整 release |
| **4DiM** | Google DeepMind, 2024, [project](https://4d-diffusion.github.io/) | 稀疏视图 + 时间戳 | 单帧/单序列 | 弱 | 弱 | 部分 |
| **4Real-Video** | 2024 | 单目 | 多视角视频 | 短 | 中 | 部分 |
| **SV3D / Stable Video 3D** | Stability AI, 2024 | **单图** | 多视角视频（轨道相机） | ❌ 静态对象 | 不适用动态人体 | ✅ |
| **ReconX** | 2024 | 稀疏图 | NeRF/视频 | 弱 | 弱 | ✅ |
| **Diffuman4D** | [arXiv 2507.13344](https://arxiv.org/abs/2507.13344) | 稀疏视图视频（4 路） | 密集多视角视频 | 中（sliding iterative denoising） | **专为人类设计，针对软组织运动** | 部分 |
| **ChronosObserver** | 2025 | 单目视频 | 多视角视频 | 中 | 训练-free | 部分 |

### 4.2 结论：对 neodojo，"多视角生成"路线不优于"先 3D 重建再渲染"

**核心问题**：

1. **长度限制**：气功一套常 5-8 分钟（约 9000-14400 帧）。CAT4D 原生 16 帧，
   外推到 1 分钟以上已经吃力，对 8 分钟连续套路**根本撑不住**。Diffuman4D 类似。
2. **时序一致性失效模式**：现有 video diffusion 模型在"动作语义边界"会跳变，
   对教学（学员要看每个动作细节）是致命的。
3. **不可控**：用户希望"从演练者背后看脚法"，需要精确指定相机外参；CAT4D 这种
   通用模型对极端视角（顶视/低位）质量差。
4. **代价不对等**：一套 CAT4D + 4DGS reconstruction 跑下来比"GVHMR + G1 在
   MuJoCo 渲染 4 个相机"贵几个数量级，而**质量更差**——因为 humanoid 是
   rigid + articulated，渲染本来就是工程问题已经解决。

**推荐路线**：仍然走 **3D 重建（GVHMR）→ humanoid → 多相机仿真渲染**。
video diffusion 在 neodojo 项目里**唯一合理的角色**是：

- (a) 用 CAT4D/Diffuman4D 对**关键定式静态帧**做新视角合成，作为"对照参考图"
  贴在 UI 边栏；
- (b) 用它做数据增强训练某个分类器/术语对齐器。

这两个都不是核心路径。

---

## 5. Text-to-Motion 与"要点文字"锚定关键帧

### 5.1 现状横向对比

| 方法 | 输出 | 训练数据 | 词汇覆盖 | 中文/术语友好度 |
|---|---|---|---|---|
| **MDM** ([GuyTevet/motion-diffusion-model](https://github.com/GuyTevet/motion-diffusion-model), ICLR 2023) | 22-关节人体动作 | HumanML3D | 通用日常英语 | 差 |
| **MotionGPT** ([OpenMotionLab/MotionGPT](https://github.com/OpenMotionLab/MotionGPT), NeurIPS 2023) | 同 + 文本双向 | HumanML3D + KIT | 英语 | 差 |
| **T2M-GPT** ([Mael-zys/T2M-GPT](https://github.com/Mael-zys/T2M-GPT), CVPR 2023) | 同 | HumanML3D | 英语 | 差 |
| **MLD / MotionDiffuse** | 同 | HumanML3D | 英语 | 差 |
| **MotionLLM / OMG / MoMask** (2024) | 更长更细粒度 | HumanML3D + 扩展 | 英语 + 细粒度 | 差 |
| **MotionGPT-2 / LMM** (2024-2025) | 多模态 | HumanML3D 拓展 | 英语 | 差 |

### 5.2 核心问题：气功术语 ≠ HumanML3D 词汇

HumanML3D 的描述形如 "a person walks forward then turns left and waves the right
hand"。**没有任何现成模型理解「沉肩坠肘」「含胸拔背」「虚领顶劲」「气沉丹田」**：

1. 训练数据完全缺失武术/气功类标注；
2. 即使给它中文术语，也不会 ground 到正确动作（这些术语描述的是**肌肉张力和
   姿态约束**，不是关节角度）；
3. 论文
   [Knowledge-Graph-Enhanced GAN for Martial Arts](https://www.nature.com/articles/s41598-026-36095-z)
   （2026, Sci Rep）显示，即使专门做武术 motion 合成，也得 **fine-tune 知识图谱
   + 自建小规模武术数据集**，且只覆盖长拳/南拳，包含极少量太极拳样本（14 个）。
4. 论文 [KungFuAthlete dataset](https://arxiv.org/abs/2602.13656) 自建了 859 段
   武术动作数据集，**没有公开**且只有 14 段太极。
5. **HumanML3D 的局限**：12 万条描述，但 90% 是日常生活，几乎没有"传统武术/
   导引术"。即使做 fine-tune，需要的领域数据规模远超 neodojo 能采集的。

### 5.3 务实路线

**不要试图用 text-to-motion 生成气功动作**。可行路线：

1. **数据驱动**：把权威官方视频（中国健身气功协会
   [chqa.org.cn](https://www.chqa.org.cn/) 推出的 11 套官方功法演练视频）做成
   neodojo 的**金标数据集**。GVHMR 抽出 SMPL-X，retarget 到 G1，得到 11 × N 段
   参考轨迹。这是 neodojo 的"基础知识库"。
2. **LLM 文本侧（不生成动作）**：用 LLM（GPT-5/Claude Opus 4.7/Qwen）做
   **双向标注**：
   - 对每段动作，让 LLM 看官方教学口诀文本，输出
     `(start_frame, end_frame, requirement_text)` 三元组。
   - 对每个关键定式（如「白鹤亮翅」的最终姿态），用人工 + LLM 协同标注约束
     （如「右手腕高于头顶」「左膝弯曲 30-60°」「躯干前倾 < 10°」）。
3. **可计算的约束式锚定**：把「沉肩」翻译成「肩峰相对于胸骨柄的 Z 坐标差 < X cm」，
   把「坠肘」翻译成「肘点低于肩点 Y cm」。这些是**几何约束**，可以用 GVHMR 输出
   的 SMPL-X 直接计算，**不需要模型理解中文**。这才是教学反馈的真正实现路径。
4. **关键帧静态姿态生成**：如果将来想生成「示范图片」，比生成完整动作容易得多
   ——用 SDXL/Flux + ControlNet（OpenPose 或 DWPose 骨架）已经成熟，能用静态
   关键帧的骨架去 ground 图像生成。
5. **结论**：text-to-motion 模型**目前不适合作为气功动作生成或锚定的主干**。
   它能做的只有：对部分通用动作（如"a person waves arms in slow circular
   motion"）生成粗略参考，作为校验工具。

---

## 6. Humanoid 仿真器的多视角渲染与轨迹可视化

### 6.1 横向对比

| 仿真器 | 多相机同步渲染 | 轨迹 overlay | Web 可视化 | 与 GR00T-WBC 一致性 |
|---|---|---|---|---|
| **MuJoCo 3.x** ([google-deepmind/mujoco](https://github.com/google-deepmind/mujoco)) | 易（`mujoco.Renderer` 多实例或 `update_scene(camera=...)` 切换） | 中（用 `mjv_addGeom` 加 `mjGEOM_LINE` / `mjGEOM_CAPSULE` 画 polyline，或用 `user_scn` 接口） | 中（[MuJoCo MJX](https://mujoco.readthedocs.io/) + 自写 WebGL；或导出 USD 给 Omniverse） | 部分（PBHC 用 MuJoCo 做 sim2sim 验证） |
| **MuJoCo + mujoco-python-viewer** ([rohanpsingh/mujoco-python-viewer](https://github.com/rohanpsingh/mujoco-python-viewer)) | 易 | 易 | 否 | 同上 |
| **MeshCat** ([rdeits/meshcat-python](https://github.com/rdeits/meshcat-python)，Pinocchio 生态) | 中（多 `Visualizer` 实例） | **极易**（`vis['traj'].set_object(LineSegments(...))`） | **✅ 原生 web** | 弱 |
| **Genesis** ([Genesis-Embodied-AI/genesis](https://github.com/Genesis-Embodied-AI/Genesis)) | **极易**（`scene.add_camera()` 任意多个，rasterizer 或 ray-tracer 切换） | 易（在 vis_options 里画 frame，或自加 entity） | 部分（PyRender 后端） | 兼容（ProtoMotions/Genesis-Humanoid 都用） |
| **Isaac Lab / Isaac Sim** | ✅（USD 多相机原生） | 中（需要写 USD primitives 或 debug draw） | 中（Omniverse Web 通道） | **★完全一致**（GR00T-WBC 主战场） |
| **Viser** ([nerfstudio-project/viser](https://github.com/nerfstudio-project/viser)) | 中（同步多 ViewPort，前端原生） | **极易**（`viser.scene.add_spline_catmull_rom(...)`） | **✅ Web 原生 + 现代 React UI** | 弱（用作前端） |
| **PyBullet** | 易 | 中 | 弱 | 弱 |

### 6.2 推荐：双轨方案

**主推 Genesis** 作为仿真后端，原因：

1. **多相机一句话搞定**：
   `scene.add_camera(res=(640,480), pos=..., lookat=..., fov=30)` 加几个就行
   （[官方教程](https://genesis-world.readthedocs.io/en/latest/user_guide/getting_started/visualization.html)）。
2. **API 极简、Python 友好**，与 roboharness 的「轻量可视化工具」气质吻合。
3. **Genesis-Humanoid** ([UMass-Embodied-AGI/Genesis-Humanoid](https://github.com/UMass-Embodied-AGI/Genesis-Humanoid))
   已经把 G1 + AMASS/LAFAN1/MoCap pipeline 跑通，是即拿即用的起点。
4. **支持 ProtoMotions**，与 NVIDIA 栈兼容。
5. 同时支持 rasterizer（实时教学反馈）和 ray-tracer（最终演示视频高质量）。

**备选 MuJoCo (mjpython)**：

- 如果想要**最小依赖、最长生命周期**：MuJoCo 是事实标准，KungfuBot/PBHC 的
  sim2sim 部署模块就跑在 MuJoCo 上。
- 多相机：在 MJCF 里定义 `<camera name="front"/>`、`<camera name="side"/>` 等，
  然后用 `mujoco.Renderer.update_scene(data, camera=cam_id)` 切换+渲染。
- **轨迹可视化**：MuJoCo 3.x 的 `mjv_initGeom` + `mjGEOM_LINE` 可在 scene 里加
  user geom（每帧 N 段折线表示手腕轨迹）；或更优雅地用 viewer 的 `user_scn`
  接口（参考 MuJoCo 官方 docs
  [Visualization](https://mujoco.readthedocs.io/en/stable/programming/visualization.html)）。
- 注意：mjpython（macOS 上 `mujoco.viewer.launch_passive` 必需）与离屏渲染共存
  有[已知坑](https://github.com/google-deepmind/mujoco/issues/798)；Linux 上更顺。

**Web 教学层（必备）**：

- **Viser** 是当前最现代的 Python 3D web 可视化方案，API 比 MeshCat 更新，
  原生支持 line、frustum、轨迹、可交互滑块、表单 UI，强烈建议作为前端。可以
  做出"左侧 MuJoCo 仿真，右侧浏览器多视角 + 轨迹 + 时间轴"的教学界面。
- **MeshCat** 作为 fallback：与 Pinocchio + Drake 生态深度集成，如果想做更严肃
  的运动学计算。

### 6.3 关节轨迹可视化的具体实现路径

- **手腕路径**：每帧记录左右手末端 site 的世界坐标 → 累积 polyline → 每 N 帧
  渲染一次（避免线段过密）→ 颜色按时间渐变（HSV 时间编码）。
- **关节角曲线**：单独面板展示 G1 23/29 DOF 中关键关节（如肩 pitch/roll/yaw、
  肘、髋）随时间变化，参考曲线（标准）和学员（实时摄像头→GVHMR→retarget）的
  叠加，是教学反馈最有价值的可视化。
- **关键定式打分**：在确定的定式帧停顿，弹出当前姿态与参考姿态的"骨架差异图"
  （不同色显示 deviation 大的肢段）。这是 roboharness 思路的自然延伸。

---

## 7. 推荐整体技术栈（最终方案）

### 7.1 最小可行系统（MVP）—— "已成熟可直接用"

```
[输入] 官方气功视频（mp4，固定机位）
    │
    ▼
[姿态估计] GVHMR (zju3dv/GVHMR) → SMPL-X 序列 (.pt)
    │  可选叠加：HAMER 做手部精修
    ▼
[Retargeting] GMR (YanjieZe/GMR)
    │  one-liner: `python scripts/gvhmr_to_robot.py
    │     --gvhmr_pred_file <.pt> --robot unitree_g1 --record_video`
    │  输出：G1 关节角时序 (.pkl)
    │
    │  并行：SMPL-X kinematic（不经 retargeting）
    │  作为「教学精度无损」主轨
    ▼
[Kinematic Playback]
    ├─ MuJoCo (mujoco>=3.2, MJCF: unitreerobotics G1 描述)
    └─ 或 Genesis (genesis-world>=0.4, MJCF 直读)
    │
    ▼
[多视角 + 轨迹可视化]
    ├─ 仿真器内：≥3 个 camera（正、侧、俯）离屏渲染→ MP4
    ├─ Web 前端：Viser (nerfstudio-project/viser)
    │   - URDF 加载 G1 + SMPL-X mesh 双轨
    │   - 多 ViewPort 同步
    │   - 手腕/手肘 polyline，颜色编码时间
    │   - 关节角曲线 panel
    └─ 学员输入摄像头（可选）→ 实时 GVHMR → 同框对比
    │
    ▼
[要点锚定]
    ├─ 手工：标注每段关键定式 (start_frame, end_frame, requirement_dict)
    ├─ LLM 辅助：把"沉肩坠肘"翻译为肩-胸骨/肘-肩的几何约束
    └─ 实时反馈：学员姿态偏离阈值时高亮
```

### 7.2 各组件成熟度评级

| 组件 | 成熟度 | 备注 |
|---|---|---|
| GVHMR 推理 | ✅ 已成熟可直接用 | 公开权重，几分钟视频推理 < 1 分钟 |
| GMR retargeting | ✅ 已成熟可直接用 | CPU 实时，15+ 个 humanoid 支持 |
| G1 URDF/MJCF | ✅ 已成熟可直接用 | [unitreerobotics/unitree_ros](https://github.com/unitreerobotics/unitree_ros)，PBHC 仓库已含 |
| SMPL-X humanoid MuJoCo 模型 | ✅ 已成熟可直接用 | [UHC](https://github.com/ZhengyiLuo/UHC) 提供，PHC 等都基于此 |
| MuJoCo 多相机渲染 | ✅ 已成熟可直接用 | 多 `Renderer` 实例，注意 mjpython 限制 |
| Genesis 多相机渲染 | ✅ 已成熟可直接用 | API 最简，[官方教程](https://genesis-world.readthedocs.io/en/latest/user_guide/getting_started/visualization.html) |
| Viser Web 前端 | ✅ 已成熟可直接用 | nerfstudio 出品，活跃维护 |
| 关节轨迹 polyline | ✅ 已成熟可直接用 | MuJoCo user geom / Viser line |
| 11 套官方气功视频获取 | ⚠️ 需要适配 | 中国健身气功协会有公开视频，但需确认是否允许教学派生（版权侧） |
| 气功术语→几何约束词典 | ⚠️ 需要适配 | 工作量中等，可以与气功教练合作 |
| 学员摄像头实时同框对比 | ⚠️ 需要适配 | 要求 GVHMR 流式/在线推理，目前主要是 batch 模式；可用 4D-Humans 实时版做近似 |
| 手部细节（勾手/立掌） | ⚠️ 需要适配 | G1 标准末端无法表达；HAMER 抽出来用 mesh 单独叠加可行 |
| Text-to-motion 自动生成气功动作 | ❌ 研究风险大 | 数据不存在，**不要做** |
| 单视图→多视角生成（CAT4D 路线） | ❌ 研究风险大 | 长度不够，不可控，**不要做** |
| 物理可行/sim2real | ❌ 超出项目目标 | 教学工具不需要 |

### 7.3 与 roboharness 的衔接

[MiaoDX/roboharness](https://github.com/MiaoDX/roboharness) 本身是机器人仿真的
视觉反馈工具。neodojo 可以作为它的一个**端到端 showcase**：

- roboharness 提供「在仿真器中以多模态方式回看一段策略 rollout」的能力 →
  neodojo 的播放任务可以直接复用其相机管理、视频录制、overlay 子模块；
- 反向贡献：neodojo 这个 use case 会强迫 roboharness 增强**轨迹叠加、关节角
  时序图、用户姿态实时对比**这些通用模块——这些 feature 对其他机器人项目
  （如示范学习、teleop 数据采集）也都有价值。

建议把 neodojo 仓库的目录结构设计成：

```
neodojo/
├── pipeline/         # GVHMR + GMR 一键脚本
├── motions/          # 11 套官方功法的 retargeted .pkl
├── annotations/      # 关键定式 + 几何约束 JSON
├── roboharness/      # submodule，作为可视化后端
├── webui/            # Viser 前端
└── docs/             # 给气功老师/学员的使用指南
```

---

## 8. 真实限制与失败模式（必须看）

1. **气功动作精度的真实上限**：受限于 GVHMR 在 OOD 数据上 ~70-100 mm MPJPE
   + IK retargeting 引入的 ~50 mm 额外误差 + G1 与人体形态差异（腿长比、躯干
   DOF 缺失），最终关节角再现误差预计在 **5-15°/关节**。这足以"看出是什么动作"，
   但**不足以教精微体感**（例如「沉肩」精确到几毫米的肩胛下沉）。**项目定位
   必须是"动作示范"，而非"姿态评判"**——若用于评判学员，需要明确不确定性边界。

2. **G1 的躯干 DOF 不足**：腰部 3 DOF 不足以表达气功中的「拧腰转胯」「含胸
   拔背」与脊柱波浪。这是硬件约束，无法通过算法补救。**neodojo 的对策是采用
   SMPL-X 与 G1 双轨可视化**，详见
   [`humanoid-platform-evaluation.md`](humanoid-platform-evaluation.md)。

3. **足部约束**：气功大量"足不离地"的微步法（如「金鸡独立」的虚步换重心）。
   retargeting 后必须做地面约束修正，否则会出现 "G1 整体悬浮 1 cm" 或 "脚穿透
   地面"。PBHC 的 contact mask 处理是参考样本。

4. **手势退化**：G1 默认末端是 1-DOF 夹爪。气功的「立掌」「勾手」「指诀」会全部
   退化成"开/合"。如果项目目标包含八段锦「双手托天理三焦」等动作，**手势退化
   是教学损失**。需要在 UI 端用 SMPL-X 手部 mesh 单独叠加显示。

5. **版权与数据**：中国健身气功协会官方视频的二次发布/派生作品需要确认授权范围。
   建议项目内只**分发 retargeted .pkl 数据**（无图像内容），不嵌入原视频；
   视频获取由用户自行下载。

6. **未来研究风险点**：
   - 实时姿态评分（学员摄像头侧）需要 GVHMR online 模式，目前社区只有 batch；
     可以走 [shubham-goel/4D-Humans](https://github.com/shubham-goel/4D-Humans)
     的实时 ViT 路线但精度下降。
   - 多人镜头处理：官方教学视频常有"老师 + 学员"双人场景，需要 BBox+ID
     tracking（PHALP）做人物锁定。

---

## 9. 进一步阅读与代码索引（汇总链接）

**HMR 核心**：

- GVHMR — [github](https://github.com/zju3dv/GVHMR) ·
  [paper](https://arxiv.org/abs/2409.06662) ·
  [project](https://zju3dv.github.io/gvhmr/)
- WHAM — [github](https://github.com/yohanshin/WHAM) ·
  [paper](https://arxiv.org/abs/2312.07531) ·
  [project](https://wham.is.tue.mpg.de/)
- TRAM — [github](https://github.com/yufu-wang/tram) ·
  [paper](https://arxiv.org/abs/2403.17346)
- 4D-Humans / HMR2.0 — [github](https://github.com/shubham-goel/4D-Humans) ·
  [paper](https://arxiv.org/abs/2305.20091)
- NLF — [github](https://github.com/isarandi/nlf) ·
  [paper](https://arxiv.org/abs/2407.07532)
- HAMER（手部）— [github](https://github.com/geopavlakos/hamer)
- CameraHMR — [paper](https://arxiv.org/abs/2411.08128)
- PhysHMR — [github](https://github.com/fengq1a0/physhmr) ·
  [paper](https://arxiv.org/abs/2510.02566)

**Retargeting / Humanoid Imitation**：

- GMR — [github](https://github.com/YanjieZe/GMR) ·
  [paper](https://arxiv.org/abs/2510.02252)
- ProtoMotions — [github](https://github.com/NVlabs/ProtoMotions) ·
  [docs](https://nvlabs.github.io/ProtoMotions/)
- PHC — [github](https://github.com/ZhengyiLuo/PHC) ·
  [paper](https://arxiv.org/abs/2305.06456)
- SMPLSim — [github](https://github.com/ZhengyiLuo/SMPLSim)
- UHC (Universal Humanoid Controller) — [github](https://github.com/ZhengyiLuo/UHC)
- Mink (IK) — [github](https://github.com/kevinzakka/mink)
- H2O / OmniH2O — [github](https://github.com/LeCAR-Lab/human2humanoid) ·
  [OmniH2O project](https://omni.human2humanoid.com/)
- HOVER (NVIDIA) — [github](https://github.com/NVlabs/HOVER)
- ExBody2 — [paper](https://arxiv.org/abs/2412.13196) ·
  [project](https://exbody2.github.io/)
- HumanPlus — [github](https://github.com/MarkFzp/humanplus)
- BeyondMimic — [github](https://github.com/HybridRobotics/whole_body_tracking) ·
  [paper](https://arxiv.org/abs/2508.08241) ·
  [project](https://beyondmimic.github.io/)
- **KungfuBot / PBHC** — [github](https://github.com/TeleHuman/PBHC) ·
  [paper](https://arxiv.org/abs/2506.12851) ·
  [project](https://kungfu-bot.github.io)
- ResMimic — [paper](https://arxiv.org/abs/2510.05070) ·
  [project](https://resmimic.github.io/)
- SPARK (Skeleton-Parameter Aligned Retargeting) —
  [paper](https://arxiv.org/abs/2603.11480)
- Awesome 列表 —
  [YanjieZe/awesome-humanoid-robot-learning](https://github.com/YanjieZe/awesome-humanoid-robot-learning)

**GR00T 生态**：

- GR00T-WholeBodyControl — [github](https://github.com/NVlabs/GR00T-WholeBodyControl) ·
  [docs](https://nvlabs.github.io/GR00T-WholeBodyControl/)
- GEAR-SONIC — [paper](https://arxiv.org/abs/2511.07820) ·
  [project](https://nvlabs.github.io/GEAR-SONIC/) ·
  [HF](https://huggingface.co/nvidia/GEAR-SONIC)
- GR00T N1.5 — [research page](https://research.nvidia.com/labs/gear/gr00t-n1_5/)
- GR00T N1.6 — [research page](https://research.nvidia.com/labs/gear/gr00t-n1_6/)

**Multi-view / 4D 生成（非主推）**：

- CAT4D — [paper](https://arxiv.org/abs/2411.18613)
- Diffuman4D — [paper](https://arxiv.org/abs/2507.13344)
- SV3D — [project](https://sv3d.github.io/)
- 4DiM — [project](https://4d-diffusion.github.io/)

**Text-to-Motion（不推荐作为 neodojo 主路径）**：

- MDM — [github](https://github.com/GuyTevet/motion-diffusion-model) ·
  [project](https://guytevet.github.io/mdm-page/)
- MotionGPT — [github](https://github.com/OpenMotionLab/MotionGPT)
- T2M-GPT — [github](https://github.com/Mael-zys/T2M-GPT)
- Knowledge-Graph + Martial Arts —
  [Sci Rep paper](https://www.nature.com/articles/s41598-026-36095-z)

**仿真器与可视化**：

- MuJoCo — [github](https://github.com/google-deepmind/mujoco) ·
  [docs](https://mujoco.readthedocs.io/)
- mujoco-python-viewer — [github](https://github.com/rohanpsingh/mujoco-python-viewer)
- Genesis — [github](https://github.com/Genesis-Embodied-AI/Genesis) ·
  [docs](https://genesis-world.readthedocs.io/)
- Genesis-Humanoid — [github](https://github.com/UMass-Embodied-AGI/Genesis-Humanoid)
- Isaac Lab — [github](https://github.com/isaac-sim/IsaacLab)
- Viser (Web 3D) — [github](https://github.com/nerfstudio-project/viser)
- Meshcat-Python — [github](https://github.com/rdeits/meshcat-python)

**机器人平台**：

- Unitree G1 SDK — [docs](https://support.unitree.com/home/en/G1_developer)
- Unitree H1-2 docs —
  [QUADRUPED Robotics](https://www.docs.quadruped.de/projects/h1/html/h1-2_overview.html)
- unitree_ros — [github](https://github.com/unitreerobotics/unitree_ros)
- Booster Robotics T1 / K1 — [booster.tech/booster-t1](https://www.booster.tech/booster-t1/)

**官方功法资源**：

- 中国健身气功协会（教学视频、功法标准）—
  [chqa.org.cn](https://www.chqa.org.cn/)
- 国家体育总局健身气功管理中心 —
  [sport.gov.cn/qgzx](https://www.sport.gov.cn/qgzx/)
- 深圳市文广旅体局健身气功专栏（9 套教学视频 + 5 套演练视频）—
  [wtl.sz.gov.cn](http://wtl.sz.gov.cn/ztzl_78228/tszl/wlzgj/index.html)

---

## 10. 一句话总结

**走 "GVHMR → GMR → Genesis/MuJoCo + Viser" 这条主路，借鉴 KungfuBot/PBHC 的
motion-processing 子模块做气功专属的足部接触修正，明确放弃 RL / 物理可行 /
text-to-motion-生成 / 多视角扩散生成 四个深坑，专注于"高保真 kinematic 演示
+ 几何约束式术语反馈"这一最有教学价值且技术最成熟的子集。**

这套技术组合对应的几乎所有论文都在 2024-2025 年内开源，且彼此互操作性良好；
roboharness 可以作为可视化与录制层自然嵌入。**气功动作的精度上限在 5-15°/关节
级别**，足以做"动作示范+大致评判"，不足以做"细微体感教学"——这个边界必须在
产品定位上写清楚。

---

> *关于为什么选 G1 + SMPL-X 双轨，而不是等待"完美 humanoid"出现，见配套文档：*
> *[`humanoid-platform-evaluation.md`](humanoid-platform-evaluation.md)*
