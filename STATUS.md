# Status

neodojo is in bootstrap state with one fixture-only local demo.

There is now a minimal checked-in Python package, a `make test` command,
fixture-backed and external-JSON `motion-record` paths, `robot-model`,
`tracks`, imported GMR JSON track, `annotations detect`, `render g1`,
`demo play`, `demo export-rerun`, and `real-conversion prepare` commands, a
`make demo-html` command that writes a self-contained synthetic web demo,
minimal `make lint`, `make check`, and `make build` commands, and a
`make demo-public` command plus `make verify` and GitHub Actions workflow for
the fixture public-demo artifact. `real-conversion materialize-source` can also
prepare a dry-run or ffmpeg-backed local source clip handoff for a later GPU
GVHMR run. There is still no checked-in GVHMR/GMR/simulator runtime pipeline,
MuJoCo/Genesis real mesh rendering, real generated motion artifact, or UI
server.

## Current Truth

- Project positioning: convert official instructional movement videos into
  simulated multi-view teaching playback.
- MVP path: official video -> GVHMR SMPL-X output -> GMR retargeting -> SMPL-X
  teaching track plus Unitree G1 visual track -> MuJoCo/Genesis rendering ->
  Viser UI.
- Teaching feedback should be based on the SMPL-X track. The G1 track is for
  visualization, ecosystem fit, and community-facing demos.
- Core non-goals for the MVP: RL policy training, sim2real control,
  text-to-motion generation, and video-diffusion multi-view generation.

## Active Work

- First end-to-end demo for Baduanjin opening form, "Holding Up the Heavens to
  Regulate the Triple Burner".
- Pre-GSD implementation phase split in
  `docs/plans/mvp-implementation-phases.md`.
- Immediate local-first smoke path: fixture motion -> motion record -> SMPL-X
  teaching-track manifest -> fixture G1 visual-track manifest -> local teaching
  playback HTML/manifest -> routine feedback anchors.
- Multi-camera offscreen rendering approach, likely reusing roboharness patterns.
- Synchronized SMPL-X and Unitree G1 playback in Viser.
- Key-frame detection and geometry-constrained verbal feedback for terms such as
  "sink the shoulders" and "drop the elbows".
- Fixture-only HTML teaching demo generated under `outputs/html-demo/`, proving
  the intended web playback shape without claiming real reconstruction or
  retargeting.
- Fixture-backed SMPL-X motion-record and teaching-track manifests, proving the
  local contract shape that later GVHMR/GMR imports should consume.
- External GVHMR SMPL-X teaching-joints JSON import into the same motion-record
  contract. This is an import boundary only, not local GVHMR execution or raw
  `.pt` parsing.
- Fixture-backed Unitree G1 model descriptor, derived visual-track manifest, and
  comparison report with `g1_scoring_allowed: false`.
- Normalized external GMR Unitree G1 JSON import into the same G1 visual-track
  contract, preserving imported joint angles while keeping G1 non-scoring.
- Deterministic SMPL-X opening-form routine review, producing
  `neodojo.annotation.v1` manifests plus `neodojo.routine_feedback_report.v1`
  reports with opening stance, settled support, and raised-hands apex anchors.
- Local G1 SVG/HTML render evidence generated under `outputs/g1-render/`,
  proving the render manifest, front/side/top frame evidence, and G1
  non-scoring boundary. Fixture descriptors require explicit
  `--allow-fixture-model`.
- Hardened artifact manifests now carry schema ids, shared timing,
  coordinate/floor/contact metadata, source-media provenance, optional
  reference-video sync metadata, and normalized annotation manifests.
- Fixture-only public-demo export generated under `outputs/public-demo/`,
  containing a scene/timeline contract, static HTML viewer, SVG screenshot, and
  `.rrd`-named JSON fallback artifact for the future Rerun lane.
- `make demo-public` regenerates the fixture motion, routine feedback
  annotations, G1 visual/render, teaching-playback, public-demo, and
  smoke-check artifacts in one command.
- `make check` validates MVP plan links and minimum plan scaffolding, and is
  included in `make verify` and the GitHub Actions workflow.
- `.github/workflows/public-demo.yml` runs tests, builds the fixture public demo,
  builds a wheel, uploads the artifact, and can publish the static output to
  GitHub Pages from `main` when Pages is enabled.
- Fixture-only teaching playback HTML generated under `outputs/teaching-demo/`,
  proving that the SMPL-X and G1 manifests can be consumed together while
  preserving the SMPL-X scoring boundary.
- The local non-GPU G1 render evidence slice in
  `docs/plans/mvp-g1-real-model-rendering.md` has landed as an SVG/HTML
  descriptor/track render path. MuJoCo/Genesis mesh rendering remains a later
  gap.
- Real-conversion source prep manifest generated under
  `outputs/real-conversion-gate/`, selecting source `03-006` metadata and a
  short trim window for a later GPU run. When `--local-video` is supplied, the
  source-media contract records checksum and optional ffprobe metadata.
- Source materialization handoff generated under
  `outputs/real-conversion-source/` when a local video is supplied, writing
  dry-run ffmpeg commands or ignored trimmed clip/reference-frame artifacts for
  the later GPU run.

## Blockers And Constraints

- Official instructional videos are licensing-sensitive. Prefer local,
  user-supplied source video unless rights are confirmed.
- Do not commit raw videos, generated motion files, model checkpoints, rendered
  videos, logs, or other large outputs.
- The accuracy ceiling is the HMR/SMPL-X reconstruction quality, especially for
  out-of-distribution qigong poses, self-occlusion, feet, and hands.
- Unitree G1 is not the scoring source because its torso and hand DOF cannot
  fully preserve the original human motion.
- Local execution should stay friendly to this macOS Apple Silicon CPU machine:
  use imported GVHMR/HAMER outputs or fixtures instead of running heavy GPU/CUDA
  inference locally.
- Downstream development may use synthetic or PBHC-sourced bootstrap fixtures to
  prove interfaces and playback, but the full MVP still requires a real
  GVHMR-produced Baduanjin artifact before it can be called end-to-end.

## What Can Be Run Now

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
PYTHONPATH=src python -m neodojo annotations detect --motion-record outputs/motion-contract --out outputs/annotations
PYTHONPATH=src python -m neodojo robot-model register --robot unitree_g1 --fixture --out outputs/g1-visual
PYTHONPATH=src python -m neodojo tracks build --motion-record outputs/motion-contract --robot unitree_g1 --model-descriptor outputs/g1-visual/robot-models/unitree_g1/manifest.json --out outputs/g1-visual
PYTHONPATH=src python -m neodojo tracks import-gmr-json --source path/to/gmr-unitree-g1.json --motion-record outputs/motion-contract --out outputs/g1-visual
PYTHONPATH=src python -m neodojo render g1 --model-descriptor outputs/g1-visual/robot-models/unitree_g1/manifest.json --g1-track outputs/g1-visual/tracks/g1/manifest.json --allow-fixture-model --out outputs/g1-render
PYTHONPATH=src python -m neodojo demo play --motion-record outputs/motion-contract --g1-track outputs/g1-visual/tracks/g1/manifest.json --out outputs/teaching-demo
PYTHONPATH=src python -m neodojo demo export-rerun --playback outputs/teaching-demo/manifest.json --g1-render outputs/g1-render/manifest.json --out outputs/public-demo/neodojo-demo.rrd
PYTHONPATH=src python -m neodojo real-conversion prepare --id 03-006 --start 0 --end 12 --out outputs/real-conversion-gate
PYTHONPATH=src python -m neodojo real-conversion materialize-source --prep outputs/real-conversion-gate/real-conversion-prep.json --local-video path/to/local-source.mp4 --dry-run --out outputs/real-conversion-source
make demo-html
```

`make verify` runs lint, MVP plan quality checks, tests, wheel build, and the
public-demo smoke lane.
`make lint` runs a minimal syntax/import bytecode compile check over `src/` and
`tests/`. `make check` validates MVP plan links and minimum plan scaffolding.
`make test` runs the focused Python unit tests for the fixture demo generator
and local motion contract. `make build` builds a wheel under ignored
`outputs/dist/`. `neodojo motion-record create` writes fixture-backed SMPL-X
motion-record and teaching-track manifests under the selected ignored output
directory, or imports an external GVHMR teaching-joints JSON export with
`--from-gvhmr-json`. `neodojo annotations detect` writes an explicit
SMPL-X-only annotation manifest plus routine feedback report for opening
stance, settled support, and raised-hands apex anchors, then feeds those anchors
into the public-demo lane. `neodojo robot-model register` and
`neodojo tracks build` write fixture G1 model/visual-track manifests and a
comparison report that keeps G1 non-scoring. `neodojo tracks import-gmr-json`
imports an external
normalized `neodojo.gmr_unitree_g1_track.v1` export with Unitree G1 joint-angle
frames into the same non-scoring G1 track contract; it does not run GMR
locally or parse every native upstream GMR output format. `neodojo render g1`
writes local SVG/HTML front/side/top render evidence and a render manifest from
a G1 model descriptor plus G1 track; fixture model descriptors require explicit
`--allow-fixture-model`, and this is not MuJoCo/Genesis simulator mesh
rendering. `neodojo demo play` writes
`outputs/teaching-demo/index.html` and a playback manifest from the SMPL-X and
G1 manifests. `neodojo demo export-rerun` writes
`outputs/public-demo/index.html`, `outputs/public-demo/scene.json`,
`outputs/public-demo/screenshot.svg`, and `outputs/public-demo/neodojo-demo.rrd`;
the `.rrd` is currently a JSON fallback artifact, not a real Rerun SDK
recording. `make demo-public` regenerates the full fixture public-demo lane,
including detected annotations, and runs the smoke check. `make smoke-public`
validates an existing `outputs/public-demo` artifact set. `make demo-html`
writes `outputs/html-demo/index.html`, `outputs/html-demo/manifest.json`, and
the local motion/track manifests it consumes. These artifacts use synthetic
fixture motion only; they validate UI plumbing, trajectory drawing, timeline
sync, the local SMPL-X/G1 scoring boundary, and one SMPL-X-based geometry check,
not qigong correctness.

`neodojo real-conversion prepare` writes ignored source/trim metadata for the
later GPU run and does not download video or execute GVHMR. When a local video
is supplied, it records checksum data and optional ffprobe duration,
resolution, codec, and frame-rate metadata. `neodojo real-conversion
materialize-source` consumes that prep manifest and a local video to write a
source-materialization manifest. With `--dry-run`, it records the ffmpeg trim
and reference-frame extraction commands without processing media. Without
`--dry-run`, it requires ffmpeg and writes ignored trimmed-video and frame
artifacts for the later GPU GVHMR input handoff.

## Remaining Non-GPU Gaps

- MuJoCo/Genesis real Unitree G1 mesh rendering from local URDF/MJCF plus
  meshes: `docs/plans/mvp-simulator-mesh-rendering.md`.
- Native GMR execution/parsing from upstream pickle/NumPy outputs:
  `docs/plans/mvp-native-gmr-runner.md`. The repo now has a normalized
  imported-GMR JSON boundary, but not local GMR execution.
- SMPL-X mesh/body-surface playback; current demos draw joints and bones:
  `docs/plans/mvp-smplx-body-surface-playback.md`.
- Simulator/Viser runtime integration and multi-camera offscreen capture:
  `docs/plans/mvp-viser-multicamera-runtime.md`.
- True Rerun SDK `.rrd` export and verification of the live GitHub Pages URL:
  `docs/plans/mvp-rerun-pages-release.md`.
- Validation that an imported real GVHMR artifact was produced from the exact
  materialized source clip and trim window:
  `docs/plans/mvp-gvhmr-source-validation.md`.

## Next Safe Task

The next MVP capability is `docs/plans/mvp-real-conversion-gate.md` for the
later GPU artifact import path. Do not run GVHMR full-video inference on this
macOS CPU workspace; use a GPU-capable machine to export a GVHMR SMPL-X
teaching-joints JSON artifact, then import it through
`neodojo motion-record create --from-gvhmr-json`.

## Background Evidence

- `docs/technical-roadmap.md` is the long technical research report.
- `docs/humanoid-platform-evaluation.md` records the G1 + SMPL-X dual-track
  platform decision.
- `docs/plans/mvp-implementation-phases.md` indexes the current executable MVP
  plan slices.
