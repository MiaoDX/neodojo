# Humanoid 平台评估：为什么是 G1 + SMPL-X 双轨

> 这份文档回答一个核心问题：
> **既然 G1 的躯干 DOF 不足以完美复刻气功动作，要不要换更接近人体的机器人？
> 还是干脆不用机器人，直接用 SMPL-X 人体模型？**
>
> 简短答案：**社区当前不存在能完美复刻人类动作的开源 humanoid。G1 的 3 DOF 腰
> 在所有开源商用平台里已经是天花板。正确解法是双轨——SMPL-X 担任"教学精度
> 主角"，G1 担任"视觉吸引力外壳"，二者共用一份 GVHMR 输出。**

---

## 目录

- [1. 问题背景](#1-问题背景)
- [2. 商用 humanoid 的躯干 DOF 真相](#2-商用-humanoid-的躯干-dof-真相)
- [3. 为什么"完美 humanoid"短期不会到来](#3-为什么完美-humanoid-短期不会到来)
- [4. SMPL/SMPL-X 才是教学准确性的终点](#4-smplsmpl-x-才是教学准确性的终点)
- [5. 那为什么还要保留 G1](#5-那为什么还要保留-g1)
- [6. 双轨方案的实现细节](#6-双轨方案的实现细节)
- [7. 决策表](#7-决策表)
- [8. 参考链接](#8-参考链接)

---

## 1. 问题背景

[`technical-roadmap.md`](technical-roadmap.md) 已经指出，Unitree G1 的躯干 DOF
不足以表达气功核心要求——「拧腰转胯」「含胸拔背」「沉肩坠肘」依赖的躯干微调，
G1 的 3 DOF 腰部+ 7 DOF 肩部组合**捕捉得到方向，捕捉不到精度**。

直接反应是：换更高 DOF 的 humanoid。这份文档系统评估了这条路。

---

## 2. 商用 humanoid 的躯干 DOF 真相

> ⚠️ 这一节的发现**纠正了 technical-roadmap.md §3.4 的一处不准确表述**。
> 横向比较后会发现，G1 的 3 DOF 腰**反而是所有商用开源 humanoid 里最好的**——
> 短板是绝对值（人体腰部约 6 DOF），不是相对差。

| 机器人 | 腰 / 躯干 DOF | 单臂 DOF | 开源 URDF | 价格 | GMR 支持 | 备注 |
|---|---|---|---|---|---|---|
| **Unitree G1** | **3**（yaw + roll + pitch） | 7 | ✅ | $16k 起 | ✅ | **商用开源天花板** |
| Unitree H1 | 1（只有 yaw） | 4 | ✅ | $90k | ✅ | 速度记录保持者，但躯干差 |
| Unitree H1-2 | 1（只有 yaw） | 7 | ✅ | $129k | ✅ | 升级了臂，没升级腰 |
| Unitree H2 | 1（沿用 H1-2 架构） | 7 | 部分 | $30k | 待加 | 2026 上市 |
| Booster T1 | **1**（只有 yaw） | 4-6 | ✅ | $34k | ✅ | RoboCup 2025 AdultSize 冠军 |
| Booster K1 | 1 | 4 | ✅ | $12.5k | ✅ | 教育级，便宜便携 |
| Tienkung | 类似 | — | ✅ | — | ✅ | GMR 已支持 |
| PND Adam Lite | 类似 | — | ✅ | — | ✅ | GMR 已支持 |
| PAL Talos | 1 (waist yaw) | 7 | ✅ | — | ✅ | 真正研究级 |
| Berkeley Humanoid Lite | 低（教育级） | — | ✅ | — | ✅ | 低成本平台 |
| **XPENG IRON** (2025) | **6+ 仿生脊柱** | — | ❌ **完全闭源** | 不售卖 | ❌ | **唯一接近人体**，82 DOF，但不可用 |
| 学术 Kotaro / Kojiro / Kenshiro | 15 DOF 仿肌骨脊柱 | — | ❌ **无开源 URDF** | 非售卖 | ❌ | 十几年前学术原型 |
| Flexinoid (2025, 张量整数脊柱) | 多段柔性 | — | 论文级 | — | ❌ | Sci Rep 2025 论文，无现成 URDF |

### 关键数据来源

- Unitree H1-2 27 DOF (7×2 arm + 6×2 leg + 1 waist) 配置 —
  [QUADRUPED docs](https://www.docs.quadruped.de/projects/h1/html/h1-2_overview.html)
- Booster T1 23 DOF (6×2 leg + 4×2 arm + 1 waist + 2 head) 配置 —
  [Génération Robots](https://www.generationrobots.com/blog/en/booster-t1-the-humanoid-development-platform-for-researchers-and-developers/)
- XPENG IRON 82 DOF + bionic spine —
  [Global Times 2025-11](https://www.globaltimes.cn/page/202511/1347511.shtml)
- Flexinoid 柔性脊柱 (±30°/65° flexion, ±30° lateral bending) —
  [Sci Rep 44646 (2025)](https://www.nature.com/articles/s41598-025-32165-w)

### 一句话结论

**能"完美复刻人类动作"的高 DOF 脊柱机器人确实存在，但全部不开源。**
开源 humanoid 的躯干 DOF 全部停留在 1-3 DOF 区间，G1 的 3 DOF 已经是上限。

---

## 3. 为什么"完美 humanoid"短期不会到来

**结构性原因，不只是工程进度问题**：

1. **DOF 越多控制越难、成本越贵**。每多一个 DOF，需要多一个 high-torque motor、
   多一组编码器、多一套控制算法。脊柱多段 DOF 在保持站立平衡上是噩梦。这是为什么
   工业派（Unitree、Booster、Figure、Apptronik）默认把躯干压缩到 1-3 DOF。

2. **仿生脊柱的现有实现是学术原型**。日本东大 Kotaro / Kojiro / Kenshiro 系列
   做了 15+ 年仿肌骨脊柱研究，最先进的 Kenshiro 也没有公开可用的 URDF/MJCF。
   2025 年 Flexinoid 用张量整数脊柱（tensegrity）做柔性脊柱，但仅是论文原型。

3. **XPENG IRON 是商用例外，但是封闭生态**。82 DOF 含仿生脊柱，2025 年 11 月
   发布。但 XPENG 没有开放 URDF、没有 SDK 开放接口，也不进入 GMR / ProtoMotions
   等开源 retargeting 生态。短期内不可能成为 neodojo 的可选项。

4. **即使有更多 DOF，retargeting 也会卡在数据**。SMPL/SMPL-X 是 24/55 DOF
   人体模型，已经远高于任何商用 humanoid。问题瓶颈本来就是 GVHMR 输出的 SMPL-X
   到机器人的映射——没有公开 humanoid 把脊柱开到 SMPL-X 水平的硬件。

**判断**：未来 1-2 年内不会出现"开源 + 高 DOF 脊柱 + 与现有 retargeting 生态
兼容"的 humanoid。等不来。

---

## 4. SMPL/SMPL-X 才是教学准确性的终点

既然机器人短期不会接近人体，那就**不用机器人做精度主角**。

### 4.1 SMPL-X 本身就是 55 DOF 人体

SMPL-X 模型包含：

- 22 个 body joints（含 spine1 + spine2 + spine3 三段脊柱）
- 15 + 15 个 hand joints（双手手指完整建模）
- 3 个 face joints（颌、眼）

加上身体形状参数 (shape) 和表情参数 (expression)，总共 ~55 个旋转 DOF +
10 shape parameters。**这已经是 GVHMR 直接输出的格式**——没有任何 retargeting
损失。

### 4.2 现成可用的 SMPL-X kinematic humanoid

- [ZhengyiLuo/UHC](https://github.com/ZhengyiLuo/UHC) 提供 SMPL / SMPL-H / SMPL-X
  三套 humanoid MJCF（MuJoCo 直接加载），支持任意体型参数。
- [ZhengyiLuo/SMPLSim](https://github.com/ZhengyiLuo/SMPLSim) 提供更轻量的 SMPL
  仿真 humanoid 中间层。
- [PHUMA](https://arxiv.org/abs/2510.05070) / PHC 等大量研究工作都把 SMPL
  humanoid 作为标准的 kinematic playback 对象。

### 4.3 SMPL-X 主轨的流水线极简

```
GVHMR 输出 (.pt, SMPL-X 参数)
  │
  ▼ forward kinematics (直接，无 retargeting)
  │
SMPL-X mesh 序列
  │
  ▼ MuJoCo / Genesis 加载 UHC 提供的 SMPL-X MJCF
  │
仿真器里的人体模型
```

**对教学准确性来说，这是唯一无损方案**。

---

## 5. 那为什么还要保留 G1

> *"There is no spoon. But there is a brand."*

保留 G1 并行轨的三个理由：

### 5.1 视觉吸引力 / 传播价值

「AI 教 humanoid 打八段锦」的标题党价值远大于「AI 播放 SMPL 网格」。
社区传播力差一个数量级。这不是虚荣——neodojo 项目的目标之一是**建立 MiaoDX
在 AI Agent + 机器人交叉领域的影响力**。

### 5.2 与 MiaoDX 生态品牌对齐

[roboharness](https://github.com/MiaoDX/roboharness) 的核心 demo 都是机器人。
气功 showcase 自然延伸到 G1 才能保持"MiaoDX = 机器人 + AI" 的品牌一致性。
如果 neodojo 完全没机器人，反而割裂。

### 5.3 几乎零额外工程成本

[GMR](https://github.com/YanjieZe/GMR) 同一个命令支持 15+ humanoid：

```bash
# 主轨：SMPL-X kinematic
python scripts/gvhmr_to_robot.py --gvhmr_pred_file motion.pt --robot smpl --record_video

# 辅轨：Unitree G1
python scripts/gvhmr_to_robot.py --gvhmr_pred_file motion.pt --robot unitree_g1 --record_video
```

两条命令共用一份 GVHMR 输出。**渲染时间翻倍，工程量不翻倍**。

### 5.4 这是 KungfuBot/PBHC 的事实标准

PBHC 论文里的所有 figure 都是 SMPL humanoid + Unitree G1 双轨展示——SMPL 在前
做"人类参考"，G1 在后做"机器人复刻"。**neodojo 沿用这个行业惯例**。

---

## 6. 双轨方案的实现细节

### 6.1 UI 布局

```
┌─────────────┬─────────────┬─────────────┐
│ 原视频      │ SMPL-X 老师 │ G1 机器人    │
│ (真人示范)  │ (技术精确)  │ (品牌价值)  │
│ 正侧俯三视  │ 正侧俯三视  │ 正侧俯三视  │
└─────────────┴─────────────┴─────────────┘
                  │
              手腕/肘/膝 轨迹叠加
              关键定式打分 (基于 SMPL-X 角度)
```

三列并排同步：

- 左列：原始官方教学视频（用户自己下载，本地播放）
- 中列：SMPL-X kinematic 人体，**用于精度评判与几何约束计算**
- 右列：Unitree G1 humanoid，**用于品牌展示与社区传播**

每列内部用 Viser 的 ViewPort 提供正/侧/俯三视角同步。

### 6.2 数据共享

```
GVHMR 输出 (SMPL-X .pt)
    │
    ├──→ SMPL-X 直接渲染（中列）
    │     - 计算几何约束（沉肩、坠肘等）
    │     - 关节角度时间曲线
    │     - 定式打分
    │
    └──→ GMR retarget 到 G1 (.pkl)
          - 仿真器加载 G1 MJCF
          - 渲染品牌展示
          - 容许 5-15° 的精度损失
```

**所有"教学反馈"逻辑只读 SMPL-X**。G1 链路纯展示，不参与评判。这样的好处：

- G1 retargeting 引入的精度损失不影响教学
- G1 形态变化（未来换 H2 / Booster T1 / 其他）不影响评判逻辑
- 评判逻辑的可信度跟着 GVHMR 进步而提升，不被机器人硬件锁死

### 6.3 关于手势的妥协

气功的「立掌」「勾手」「指诀」对 G1 默认末端（1-DOF 夹爪）无法表达。
**双轨方案天然处理这个问题**：

- SMPL-X 含完整手部 15+15 关节，配合 HAMER（[geopavlakos/hamer](https://github.com/geopavlakos/hamer)）
  做手部精修，完全保留手势细节
- G1 端的手势退化成"开/合"，但用户视觉上仍能看出大致姿态
- 在 UI 上明确标注："手部精度以中列 SMPL-X 为准"

---

## 7. 决策表

| 维度 | 单 SMPL-X | 单 G1 | **双轨 (推荐)** |
|---|---|---|---|
| 教学精度 | ✅ 无损 | ❌ 5-15° 损失 | ✅ 用 SMPL-X 评判 |
| 视觉吸引力 | ⚠️ 网格不够"酷" | ✅ 机器人 | ✅ 二者都有 |
| 品牌一致性 (MiaoDX = 机器人) | ❌ 没机器人 | ✅ | ✅ |
| 工程成本 | 低 | 低 | 中（基本翻倍渲染） |
| 跟随社区惯例 (PBHC 等) | ⚠️ 部分 | ⚠️ 部分 | ✅ 完全对齐 |
| 未来扩展到瑜伽/康复 | ✅ | ⚠️（康复不需要机器人） | ✅ 灵活 |
| 学员实时对比模式 | ✅ 直接对比 SMPL-X | ❌ 要再 retarget | ✅ 学员对比 SMPL-X 主轨 |

**结论**：双轨。

---

## 8. 参考链接

**机器人平台规格**：

- Unitree G1 — [unitree.com/g1](https://www.unitree.com/g1)
- Unitree H1 — [unitree.com/h1](https://www.unitree.com/h1/)
- Unitree H1-2 docs —
  [QUADRUPED Robotics](https://www.docs.quadruped.de/projects/h1/html/h1-2_overview.html)
- Booster T1 — [booster.tech/booster-t1](https://www.booster.tech/booster-t1/)
- Booster T1 详细规格 (Génération Robots) —
  [generationrobots.com](https://www.generationrobots.com/blog/en/booster-t1-the-humanoid-development-platform-for-researchers-and-developers/)
- XPENG IRON 发布 (Global Times 2025-11) —
  [globaltimes.cn](https://www.globaltimes.cn/page/202511/1347511.shtml)

**SMPL / SMPL-X 仿真基础设施**：

- [ZhengyiLuo/UHC](https://github.com/ZhengyiLuo/UHC) — Universal Humanoid
  Controller (Mujoco SMPL/SMPL-H/SMPL-X)
- [ZhengyiLuo/SMPLSim](https://github.com/ZhengyiLuo/SMPLSim)
- [SMPL-X 官方](https://smpl-x.is.tue.mpg.de/)

**仿生脊柱研究**：

- Flexinoid (tensegrity spine) —
  [Sci Rep 44646 (2025)](https://www.nature.com/articles/s41598-025-32165-w)
- Multi-segment lumbar spine —
  [Researchgate (2025)](https://www.researchgate.net/publication/295250035_Development_of_the_Multi-Segment_Lumbar_Spine_for_Humanoid_Robots)
- Bionic humanoid torso (early Kotaro/Kojiro/Kenshiro 系列) —
  [Worldscientific](https://www.worldscientific.com/doi/abs/10.1142/S0219843617500104)

**Retargeting 通用平台**：

- [YanjieZe/GMR](https://github.com/YanjieZe/GMR) — 支持 15+ humanoid，CPU 实时

**双轨惯例参考**：

- [TeleHuman/PBHC (KungfuBot)](https://github.com/TeleHuman/PBHC) —
  论文 figure 全部采用 SMPL + G1 双轨展示
- [NVlabs/ProtoMotions](https://github.com/NVlabs/ProtoMotions) — 同时支持
  SMPL/SMPL-X 与 G1/H1，体现"先 SMPL 再 humanoid" 的标准流水线

---

> *回到 neodojo 主线：见 [`technical-roadmap.md`](technical-roadmap.md)。*
