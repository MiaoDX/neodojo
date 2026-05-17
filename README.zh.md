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

🚧 **Bootstrap 阶段**。

当前 repo 状态、已知约束与下一步安全任务见 [`STATUS.md`](STATUS.md)。目前还没有
提交到仓库的运行时 pipeline、package layout、测试命令或 CI gate。

正在做的事情：

- [ ] 第一个端到端 demo：八段锦第一式「双手托天理三焦」
- [ ] roboharness 风格的多视角离屏录制集成
- [ ] SMPL-X 与 Unitree G1 双轨同屏 Viser UI
- [ ] 关键定式自动检测 + 几何约束式术语反馈
  （把"沉肩坠肘"翻译成可计算的几何约束）

完整 roadmap 会以 issue 形式持续展开。

---

## Related work in the MiaoDX ecosystem

- 🤖 [roboharness](https://github.com/MiaoDX/roboharness) — 给机器人仿真 agent 装上"眼睛"。neodojo 复用其多相机管理与录制层
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
