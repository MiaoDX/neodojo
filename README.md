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
and next safe task. There is now a small checked-in Python package, local
SMPL-X and G1 fixture artifact commands, a normalized imported-GMR G1 track
boundary, native GMR pickle normalization, a dependency-light SMPL-X surface
proxy, a teaching-playback HTML command, a static HTML demo generator, local
SVG/HTML G1 render evidence from a model descriptor plus visual track, optional
MuJoCo offscreen mesh render evidence, optional true Rerun SDK `.rrd` export,
an optional first Viser local runtime, and minimal lint/build/quality-check
commands. It can also write a dry-run or ffmpeg-backed local source-video
handoff for a later GPU GVHMR run. There is still no checked-in GVHMR/GMR
execution pipeline, simulator runtime pipeline, licensed SMPL-X mesh
generation, production teaching UI, or verified render from real Unitree G1
mesh assets.

What can be run now:

```bash
make verify
make lint
make check
make test
make build
make demo-public
make smoke-public
PYTHONPATH=src python -m neodojo motion-record create --out outputs/motion-contract
PYTHONPATH=src python -m neodojo motion-record create --from-gvhmr-json path/to/gvhmr-smplx-joints.json --out outputs/motion-contract
PYTHONPATH=src python -m neodojo smplx-surface proxy --motion-record outputs/motion-contract --out outputs/smplx-surface
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
PYTHONPATH=src python -m neodojo real-conversion prepare --id 03-006 --start 0 --end 12 --out outputs/real-conversion-gate
PYTHONPATH=src python -m neodojo real-conversion materialize-source --prep outputs/real-conversion-gate/real-conversion-prep.json --local-video path/to/local-source.mp4 --dry-run --out outputs/real-conversion-source
PYTHONPATH=src python -m neodojo real-conversion validate-source --source-materialization outputs/real-conversion-source/source-materialization.json --gvhmr-json outputs/real-conversion-gate/gvhmr-smplx-joints.json --out outputs/real-conversion-validation
make demo-html
```

`neodojo motion-record create` writes fixture-backed SMPL-X motion-record and
teaching-track manifests, or imports an external GVHMR SMPL-X teaching-joints
JSON export with `--from-gvhmr-json`. The repo still does not run GVHMR locally
or parse raw GVHMR `.pt` files; the JSON path is the CPU-side import boundary
for a later GPU run.

`neodojo annotations detect` writes an explicit SMPL-X-only annotation manifest
and routine feedback report for opening stance, settled support, and
raised-hands apex anchors. `make demo-public` feeds those anchors into the
teaching playback instead of relying on an implicit final frame.

`neodojo smplx-surface proxy` writes a dependency-light capsule surface proxy
derived from SMPL-X teaching joints. It improves visual inspection in the
teaching/public demo while staying honest that no licensed SMPL-X body-model
mesh is generated and all feedback still reads SMPL-X joints.

`neodojo robot-model register` and `neodojo tracks build` can write fixture G1
model and visual-track manifests. These preserve the SMPL-X/G1 responsibility
split but do not yet load a real Unitree G1 mesh or run GMR retargeting.
`neodojo tracks normalize-gmr-pkl` parses the native YanjieZe/GMR robot-motion
pickle shape written by upstream `scripts/*_to_robot.py --save_path` and emits
the normalized JSON contract used by the repo. `neodojo tracks import-gmr-json`
imports a normalized external
`neodojo.gmr_unitree_g1_track.v1` export with Unitree G1 joint-angle frames
into the same non-scoring G1 track contract; it does not run GMR locally or
claim support for every native upstream GMR output format.

`neodojo render g1` consumes a G1 model descriptor and G1 visual-track manifest,
then writes SVG front/side/top frame evidence plus a local HTML page and render
manifest. Fixture descriptors require `--allow-fixture-model`; registered
URDF/MJCF descriptors are accepted without that flag. This is local render
evidence, not MuJoCo/Genesis simulator mesh rendering.
`neodojo render mujoco-g1` is the optional MuJoCo offscreen renderer for
registered URDF/MJCF descriptors. It requires installing the `sim` extra or the
`mujoco` package and still needs local, untracked robot assets for a real
Unitree G1 proof; the built-in optional smoke verifies the path with a tiny
synthetic MJCF model.

`neodojo demo play` consumes the SMPL-X motion-record, optional SMPL-X surface
proxy, and G1 visual-track manifests together, then writes
`outputs/teaching-demo/index.html` plus a playback manifest. This is a
simulator-light HTML inspection path: SMPL-X joints stay the scoring source,
the surface proxy is visual-only, and G1 stays non-scoring. It can also
preserve optional local-only original-video sync metadata with
`--reference-video`.

`neodojo demo export-rerun` writes the internal scene/timeline contract, a
fixture-only static public-demo HTML page, an SVG screenshot, and a `.rrd`-named
recording artifact under `outputs/public-demo/`. By default, the `.rrd` file is
an honest JSON fallback artifact, not a real Rerun SDK recording. With
`--use-rerun-sdk` and the optional `rerun` extra installed, the same command
writes a true Rerun SDK recording and marks
`rerun.actual_rrd: true` in the public-demo manifest.

`neodojo demo serve-viser` writes `outputs/viser-runtime/scene.json` plus a
Viser runtime manifest, then starts an optional local Viser server from the
same scene/timeline contract. It requires installing the `viser` extra or the
`viser` package. The first runtime shows SMPL-X and G1 as synchronized 3D
tracks with a frame slider, trajectory overlays, camera-preset metadata, and
explicit SMPL-X scoring/G1 visual labels; it is not the final teaching UI.

`make verify` runs lint, MVP plan quality checks, tests, wheel build, and the
public-demo smoke lane.
`make demo-public` regenerates the fixture motion contract, detected
annotations, SMPL-X surface proxy, G1 visual track, G1 render evidence,
teaching playback, public-demo artifact, and smoke check in one local command.
`make smoke-public`
validates an existing
`outputs/public-demo` artifact set. The GitHub Actions workflow at
`.github/workflows/public-demo.yml` runs the same fixture lane, uploads the
artifact, and can publish it to GitHub Pages when Pages is enabled for the repo
and `NEODOJO_DEPLOY_PAGES=true` is set as a repository variable.
`make lint` is currently a syntax/import bytecode compile check; `make check`
validates MVP plan links and minimum plan scaffolding; `make build` writes a
wheel under ignored `outputs/dist/`.

`neodojo real-conversion prepare` writes source metadata, trim metadata, and
next-command hints for the later GPU gate. It does not download the source
video or run GVHMR. When `--local-video` is supplied, it records checksum data
and optional ffprobe duration, resolution, codec, and frame-rate metadata.
`neodojo real-conversion materialize-source` consumes that prep manifest plus a
local video and writes a source-materialization manifest. With `--dry-run`, it
records exact ffmpeg trim and reference-frame extraction commands without
processing media. Without `--dry-run`, it requires ffmpeg and writes ignored
trimmed-video and reference-frame artifacts for the later GPU GVHMR input.
`neodojo real-conversion validate-source` compares a GVHMR teaching-joints JSON
export against the source-materialization manifest, writes a validation report,
and emits a validated import JSON copy when provenance matches.

`make demo-html` writes `outputs/html-demo/index.html`, a self-contained
synthetic fixture demo for the intended teaching UI shape, backed by the local
motion/track manifest contract. It does not prove source-video conversion,
qigong motion accuracy, simulator rendering, production Viser UX, or real
Unitree G1 retargeting.

In progress:

- [ ] First end-to-end demo: Baduanjin opening form *"Holding Up the
      Heavens to Regulate the Triple Burner"*
- [x] Fixture-only web/HTML teaching demo for synchronized SMPL-X/G1-style
      playback, trajectory overlays, timeline controls, and one SMPL-X-based
      geometry check
- [x] Local fixture SMPL-X motion-record and teaching-track manifests
- [x] External GVHMR teaching-joints JSON import into the same motion contract
- [x] Dependency-light SMPL-X surface proxy layer in teaching/public demos
- [x] Local fixture G1 model and visual-track manifests with scoring separation
- [x] Normalized external GMR Unitree G1 JSON import into the non-scoring G1
      visual-track contract
- [x] Native GMR robot-motion pickle normalization into that same G1 JSON import
      contract
- [x] Local G1 SVG/HTML render evidence command with front/side/top frames and
      `g1_scoring_allowed: false`
- [x] Optional MuJoCo offscreen mesh render command, smoke-tested with a tiny
      MJCF model; final real G1 asset proof still needs local assets
- [x] Local teaching playback command that consumes SMPL-X and G1 manifests
- [x] Deterministic SMPL-X opening-form routine feedback review with multiple
      key-frame anchors and posture terms
- [x] Fixture-only static public-demo export with scene/timeline contract,
      `.rrd` fallback artifact, HTML, and SVG screenshot
- [x] Optional true Rerun SDK `.rrd` export; live GitHub Pages URL verification
      remains repository-setting dependent
- [x] Optional first Viser local runtime with synchronized SMPL-X/G1 tracks,
      frame slider, trajectory overlays, and scoring-source labels
- [x] One-command local `make demo-public` flow and GitHub Actions artifact/Page
      workflow for the fixture public demo
- [x] Minimal `make lint` and `make build` command surface
- [x] Project-owned `make check` quality gate for MVP plan links/scaffolding
- [x] One-command local `make verify` flow for lint, quality checks, tests,
      build, and public demo generation
- [x] Local real-conversion prep manifest for source `03-006`
- [x] Local real-conversion source materialization handoff for a user-supplied
      video
- [x] Local GVHMR source-validation report and validated JSON import handoff
- [ ] MuJoCo/Genesis real Unitree G1 mesh rendering from user-supplied URDF/MJCF
      and meshes
- [ ] roboharness-style multi-camera offscreen capture integration
- [ ] production Viser teaching UX beyond the first optional local runtime

The detailed implementation queue lives in [`docs/plans/`](docs/plans/) and
can later be mirrored into GitHub issues.

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
