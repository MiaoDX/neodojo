# neodojo

**English** · [中文](README.zh.md)

> *"This is the Construct. It's our loading program.*
> *We can load anything, from clothing, to equipment,*
> *weapons, training simulations..."*
>
> — Morpheus, *The Matrix* (1999)

---

## I know kung fu.

27 years later, we finally have a real Construct.

Not for loading weapons. Not for loading combat programs. This Construct
loads **Baduanjin, Wu Qin Xi, Yi Jin Jing**—and, eventually, any human
movement practice that benefits from *seeing* the standard form.

**neodojo** is a simulation training dojo for *kung fu* in its broadest
sense—qigong, taichi, traditional martial arts, daoyin, and beyond. It
converts official instructional videos into joint trajectories of a humanoid
in simulation, then renders the result from multiple angles with overlaid
joint paths. You see exactly what the "standard shadow" of each move
should look like.

Then you load that shadow into your training loop—the way Morpheus loaded
kung fu into Neo's mind.

---

## What it does

- **The Loading Program** — official video → monocular 3D pose estimation
  → SMPL-X full-body parameters → humanoid joint trajectories
- **The Sparring Partner** — SMPL-X human model + Unitree G1 humanoid
  side-by-side on one screen: one for accuracy, one to look like the
  opponent Neo trained against
- **Show Me** — synchronized front / side / top views with overlaid
  trajectories for wrist, elbow, knee
- **Free Your Mind** — webcam-based real-time comparison mode (future
  work)

---

## Why "kung fu" (not just qigong)

In English, *kung fu* long ago outgrew its literal meaning of "martial
arts." It now refers to **any skill acquired through prolonged practice**.

> *"There is no try."*
> *"There is no shortcut."*

Qigong, taichi, Baduanjin, Wu Qin Xi, Yi Jin Jing, yoga poses, the
standard movements in physical rehab—all of it fits under that broader
umbrella. The project name leaves room so the first use case doesn't lock
in everything that follows.

**The first programs to be loaded are Chinese Health Qigong**—because
they're publicly endorsed by the General Administration of Sport of
China, have standardized instructional videos, are slow enough to suit
SMPL-X pose estimation, and have a built-in community of practitioners
who would actually benefit.

---

## First instances

From the official instructional videos of the Chinese Health Qigong
Association and the Health Qigong Management Center of the General
Administration of Sport of China:

- [ ] Health Qigong · Baduanjin (Eight Pieces of Brocade)
- [ ] Health Qigong · Wu Qin Xi (Five Animal Frolics)
- [ ] Health Qigong · Yi Jin Jing (Muscle-Tendon Changing Classic)
- [ ] Health Qigong · Liu Zi Jue (Six Healing Sounds)
- [ ] Health Qigong · Da Wu (Great Dance)
- [ ] Health Qigong · Mawangdui Daoyin Shu
- [ ] Health Qigong · Shi Er Duan Jin (Twelve Pieces of Brocade)
- [ ] Health Qigong · Taiji Yangsheng Zhang (Health-Preserving Staff)
- [ ] Health Qigong · Daoyin Yangsheng Gong Shi Er Fa
- [ ] Campus Wu Qin Xi (primary / middle / high school editions)
- [ ] Ming Mu Gong / Eye-Brightening Qigong (youth / adult editions)

---

## Tech stack at a glance

Current project truth lives in:

- 📄 [`STATUS.md`](STATUS.md) — current state, constraints, and next safe task
- 📄 [`ARCHITECTURE.md`](ARCHITECTURE.md) — MVP data flow, subsystem
  boundaries, and proof boundaries

Full technical investigation, SOTA model comparisons, robot platform
evaluation, and failure-mode analysis live in these background notes:

- 📄 [`docs/technical-roadmap.md`](docs/technical-roadmap.md) —
  end-to-end pipeline study (GVHMR / GMR / Genesis / Viser / KungfuBot
  etc.)
- 📄 [`docs/humanoid-platform-evaluation.md`](docs/humanoid-platform-evaluation.md) —
  why G1 + SMPL-X dual-track, instead of waiting for a "perfect
  humanoid"

Core pipeline:

```
Official instructional video
  │
  ▼
GVHMR (monocular video → SMPL-X, with 22+15 hand joints)
  │
  ▼
GMR (SMPL-X → humanoid joint angles; real-time on CPU, 15+ robots)
  │
  ├─→ SMPL-X kinematic playback   (primary: lossless teaching accuracy)
  └─→ Unitree G1 kinematic playback (secondary: visual appeal)
  │
  ▼
MuJoCo / Genesis multi-camera offscreen rendering
  │
  ▼
Viser (synchronized 3-view web UI + joint trajectory overlays + timeline)
```

---

## Why this exists (the unfair advantage)

> *"I'm trying to free your mind, Neo. But I can only show you the door.*
> *You're the one that has to walk through it."*

Following a single-angle qigong video has one fundamental problem:
**you only see one angle**.

- The teacher turns sideways for *Deer Charging Backwards*—you cannot see
  the footwork.
- You've practiced *Holding Up the Heavens* for six months and no one's
  told you your shoulders are still raised, your elbows still floating.
- You want to know how many degrees your *White Crane Spreads Its Wings*
  deviates from standard, but no mirror can tell you.

**neodojo reconstructs the standard motion in 3D from single-angle
footage, so you can look at it from any angle.** Push it further: feed
your own practice video into the same pipeline, overlay it next to the
standard, and see the gap.

This is not prompt engineering. Not context engineering. It's
**kinematic engineering**: designing a Construct for humans to learn
embodied skills.

---

## Status

🚧 **Bootstrap phase, with a fixture-only HTML demo.**

See [`STATUS.md`](STATUS.md) for the current repo state, known constraints,
and next safe task. There is now a small checked-in Python package, a local
SMPL-X fixture motion-contract command, and a static HTML demo generator, but
there is still no checked-in GVHMR/GMR/simulator runtime pipeline or CI gate.

What can be run now:

```bash
make test
PYTHONPATH=src python -m neodojo motion-record create --out outputs/motion-contract
make demo-html
```

`neodojo motion-record create` writes fixture-backed SMPL-X motion-record and
teaching-track manifests. These are plumbing artifacts only, not real GVHMR
outputs or qigong teaching evidence.

`make demo-html` writes `outputs/html-demo/index.html`, a self-contained
synthetic fixture demo for the intended teaching UI shape, backed by the local
motion/track manifest contract. It does not prove source-video conversion,
qigong motion accuracy, simulator rendering, Viser, or real Unitree G1
retargeting.

In progress:

- [ ] First end-to-end demo: Baduanjin opening form *"Holding Up the
      Heavens to Regulate the Triple Burner"*
- [x] Fixture-only web/HTML teaching demo for synchronized SMPL-X/G1-style
      playback, trajectory overlays, timeline controls, and one SMPL-X-based
      geometry check
- [x] Local fixture SMPL-X motion-record and teaching-track manifests
- [ ] roboharness-style multi-camera offscreen capture integration
- [ ] SMPL-X + Unitree G1 dual-track synchronized Viser UI
- [ ] Automatic key-frame detection + geometry-constrained verbal
      feedback (translating phrases like *"sink the shoulders, drop the
      elbows"* into computable geometric constraints)

The full roadmap is being unfolded as GitHub issues.

---

## Related work in the MiaoDX ecosystem

- 🤖 [roboharness](https://github.com/MiaoDX/roboharness) — eyes for
  robot simulation agents. neodojo reuses its multi-camera management
  and recording layer.
- 🦾 [robowbc](https://github.com/MiaoDX/robowbc) — whole-body control
  showcase built on roboharness.

> *roboharness gave robots eyes to see themselves;*
> *neodojo gives humans a shadow that always demonstrates the standard.*

---

## License & Acknowledgments

> *"There is no spoon."*

There are no real robots here. Only simulation. But simulation is enough—
the accuracy ceiling is set by GVHMR, by SMPL-X, by the motion-tracking
research thread of KungfuBot/PBHC. **Not by steel.**

Standing on the shoulders of (see
[`docs/technical-roadmap.md`](docs/technical-roadmap.md) for the full
list):

- [GVHMR](https://github.com/zju3dv/GVHMR) (SIGGRAPH Asia 2024) —
  monocular video → SMPL-X
- [GMR](https://github.com/YanjieZe/GMR) (ICRA 2026) — General Motion
  Retargeting
- [PBHC / KungfuBot](https://github.com/TeleHuman/PBHC) — martial-arts
  humanoid simulation
- [GR00T-WholeBodyControl](https://github.com/NVlabs/GR00T-WholeBodyControl)
  (NVIDIA) — whole-body control reference stack
- [Genesis](https://github.com/Genesis-Embodied-AI/Genesis) /
  [MuJoCo](https://github.com/google-deepmind/mujoco) — simulators
- [Viser](https://github.com/nerfstudio-project/viser) — web 3D
  visualization
- [Chinese Health Qigong Association](https://www.chqa.org.cn/) &
  Health Qigong Management Center of the General Administration of
  Sport of China — official instructional videos and routine standards

License: MIT (TBD)

---

## Contributing

> *"What if I told you... the dojo isn't the place. The dojo is the
> practice."*

Issues, PRs, ideas, war stories—all welcome. At this early stage every
piece of feedback is valuable.

If you are:

- **A qigong / taichi / martial-arts practitioner**: the details your
  teacher tells you but the video can't reveal are exactly what this
  project most needs
- **An HMR / humanoid researcher**: please review the technical roadmap
  and suggest better models or retargeting approaches
- **A roboharness / AI-coding-agent enthusiast**: this is an open
  experiment in Claude-Code-routines-driven development

---

> *"I know kung fu."*
>
> *"Show me."*
