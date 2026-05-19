# Status

neodojo is in bootstrap state with a fixture-only public demo and a local ignored
real Baduanjin G1 replay proof.

## Current Truth

- Project positioning: convert official or user-supplied instructional movement
  videos into simulated multi-view teaching playback.
- MVP path: source video -> GVHMR SMPL-X output -> GMR retargeting -> SMPL-X
  teaching track plus Unitree G1 visual track -> MuJoCo/Genesis rendering ->
  Viser UI.
- Teaching feedback is based on the SMPL-X track. The Unitree G1 track is for
  visualization and ecosystem fit only.
- The live Pages demo remains fixture-only at
  `https://miaodx.com/neodojo/`.
- The generated public-demo `index.html` is an interactive synchronized teaching
  replay: SMPL-X skeleton teaching track plus Unitree G1 visual track by
  default, and an optional Original video panel when a local reference clip is
  available. The G1 panel is labeled as actual Unitree G1 MuJoCo model replay
  only when a non-fixture imported/native GMR track, non-fixture G1 descriptor,
  and MuJoCo PNG frame sequence are supplied.
- A local ignored proof exists in this workspace for a visible-motion Baduanjin
  clip (`80s-92s` from the local 12m08s source video): non-fixture GVHMR SMPL-X
  JSON, headless native GMR Unitree G1 joint angles, a non-fixture
  roboharness/robot_descriptions MJCF descriptor, a nonblank/changing MuJoCo PNG
  frame sequence, and public HTML consumption of those replay frames. The strict
  audit reports `real_demo_verified` for this local artifact set.
- The Baduanjin proof source should be documented as public source-index item
  `03-006` (`5八段锦两手托天理三焦`) from `video/original_videos.md`, trim
  `80s-92s`. Real-demo publication can point to this source provenance while
  still keeping raw source video and generated heavy artifacts out of git.
- The default MuJoCo G1 render style now follows the actual roboharness
  `g1-reach` scene implementation: wrapped G1 MJCF scene, blue skybox gradient,
  gray/white checker floor, roboharness lights, original G1 materials, and
  named cameras tuned for the raised-hands qigong replay.
- `make roboharness-g1-report MODEL_DESCRIPTOR=... G1_TRACK=...` writes
  `outputs/g1-roboharness-report/neodojo_g1_replay_report.html`, a sampled
  roboharness checkpoint report with `start`, `early`, `middle`, `late`, and
  `finish` stages from the imported G1 track.
- MuJoCo CI/local parity uses an explicit GL backend. The chosen default is
  `MUJOCO_GL=glfw` under `xvfb-run -a`, because it runs on GitHub-hosted Ubuntu
  and local machines with the same display-backed path. `MUJOCO_GL=osmesa` is
  CPU headless when OSMesa system libraries are installed; `MUJOCO_GL=egl` is
  for GPU/self-hosted runners with working EGL.
- `.github/workflows/public-demo.yml` has a focused MuJoCo smoke lane that
  installs the `real-g1-replay` extra and validates the G1 renderer through
  `xvfb-run -a env MUJOCO_GL=glfw`.
- The same workflow runs `make ci-real-demo` and uploads
  `outputs/real-demo/public-demo/index.html` as the
  `neodojo-real-demo-public-demo` artifact. By default this lane uses
  `samples/baduanjin-03-006-two-hands-80-92`, a committed derived JSON sample
  with source provenance, returned GVHMR SMPL-X joints, and normalized GMR
  Unitree G1 joint angles. CI regenerates the G1 descriptor, MuJoCo PNG frames,
  public HTML, and strict real-demo audit from those JSON artifacts.
- `make mujoco-backend-compare MODEL_DESCRIPTOR=... G1_TRACK=...` writes
  `outputs/g1-mujoco-backend-comparison/index.html`, a single manual review
  page comparing `egl`, `glfw`, and `osmesa` render outputs, timings, and setup
  errors.
- `make mujoco-backend-benchmark MODEL_DESCRIPTOR=... G1_TRACK=...` writes
  `outputs/g1-mujoco-backend-benchmark/benchmark.md` and `manifest.json`, with
  repeated render timing stats per backend.

## Supported Command Surface

Core verification and fixture demo:

```bash
make verify
make lint
make check
make test
make build
make demo-html
make demo-public
make demo-public-browser
make ci-real-demo
make ci-real-demo \
  CI_REAL_SOURCE_MATERIALIZATION=path/to/source-materialization.json \
  CI_REAL_GVHMR_JSON=path/to/gvhmr-smplx-joints.json \
  CI_REAL_GMR_G1_JSON=path/to/gmr-unitree-g1.json \
  CI_REAL_VERIFY_STRICT=1
make smoke-public
```

Local real-conversion preparation and returned-artifact handling:

```bash
make real-gpu-prep LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin REAL_DRY_RUN=0
make gvhmr-inspect GVHMR_RESULT=path/to/hmr4d_results.pt
make real-artifact-intake REAL_ARTIFACT_SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json REAL_ARTIFACT_GVHMR_JSON=path/to/gvhmr-smplx-joints.json
make demo-real SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json GVHMR_JSON=path/to/gvhmr-smplx-joints.json
uv pip install -e '.[real-g1-replay]'
uv pip install -e path/to/GMR
PYTHONPATH=src python -m neodojo robot-model register-roboharness-g1 --out outputs/g1-visual
PYTHONPATH=src python -m neodojo tracks run-gmr-g1 --motion-record outputs/real-demo/motion-contract --gvhmr-result path/to/hmr4d_results.pt --gmr-repo path/to/GMR --body-models path/to/GMR/assets/body_models --out outputs/gmr-native-run --execute
PYTHONPATH=src python -m neodojo tracks import-gmr-json --source outputs/gmr-native-run/normalized/gmr-unitree-g1.normalized.json --motion-record outputs/real-demo/motion-contract --model-descriptor outputs/g1-visual/robot-models/unitree_g1/manifest.json --out outputs/g1-visual
make mujoco-g1-render MODEL_DESCRIPTOR=outputs/g1-visual/robot-models/unitree_g1/manifest.json G1_TRACK=outputs/g1-visual/tracks/g1/manifest.json
make roboharness-g1-report MODEL_DESCRIPTOR=outputs/g1-visual/robot-models/unitree_g1/manifest.json G1_TRACK=outputs/g1-visual/tracks/g1/manifest.json
make mujoco-backend-compare MODEL_DESCRIPTOR=outputs/g1-visual/robot-models/unitree_g1/manifest.json G1_TRACK=outputs/g1-visual/tracks/g1/manifest.json
make mujoco-backend-benchmark MODEL_DESCRIPTOR=outputs/g1-visual/robot-models/unitree_g1/manifest.json G1_TRACK=outputs/g1-visual/tracks/g1/manifest.json
make demo-real SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json GVHMR_JSON=path/to/gvhmr-smplx-joints.json G1_TRACK=outputs/g1-visual/tracks/g1/manifest.json MODEL_DESCRIPTOR=outputs/g1-visual/robot-models/unitree_g1/manifest.json G1_RENDER=outputs/g1-mujoco-render/manifest.json
make real-conversion-audit
make verify-real
```

Useful direct CLI equivalents:

```bash
PYTHONPATH=src python -m neodojo real-conversion prepare --local-source-id local-baduanjin --local-video path/to/local-source.mp4 --start 80 --end 92 --out outputs/real-conversion-gate
PYTHONPATH=src python -m neodojo real-conversion materialize-source --prep outputs/real-conversion-gate/real-conversion-prep.json --local-video path/to/local-source.mp4 --out outputs/real-conversion-source
PYTHONPATH=src python -m neodojo real-conversion prepare-gpu-run --source-materialization outputs/real-conversion-source/source-materialization.json --out outputs/gvhmr-local-gpu-run
PYTHONPATH=src python -m neodojo real-conversion inspect-gvhmr-result --source path/to/hmr4d_results.pt --out outputs/gvhmr-result-inspection
PYTHONPATH=src python -m neodojo real-conversion import-demo --source-materialization outputs/real-conversion-source/source-materialization.json --gvhmr-json path/to/gvhmr-smplx-joints.json --out outputs/real-demo
PYTHONPATH=src python -m neodojo real-conversion audit-completion --source-materialization outputs/real-conversion-source/source-materialization.json --gvhmr-json path/to/gvhmr-smplx-joints.json --real-demo outputs/real-demo --out outputs/real-conversion-audit
```

## Removed Surface

The current repo supports local-machine GPU work only. The following surfaces
were removed from the public Makefile/CLI/CI path and should not be documented
as supported until a new plan explicitly restores them:

- Colab operator notebooks.
- Hosted GPU provider probes or run requests.
- External operator packages and transfer archives.
- Self-hosted GitHub Actions GPU workflow dispatch.
- Real-demo Pages promotion workflow.

## What Exists

- Fixture-backed SMPL-X motion-record and teaching-track manifests.
- External GVHMR SMPL-X teaching-joints JSON import into the same motion-record
  contract.
- Fixture-backed Unitree G1 model descriptor and visual-track manifest.
- External GMR JSON and native GMR pickle normalization into the G1 visual-track
  contract.
- Local GMR run manifest/execution wrapper that can run GMR headlessly from a
  local checkout or installed GMR environment, then normalize the returned native
  pickle when local SMPL-X body-model assets are supplied.
- Dependency-light SMPL-X surface proxy and local-only licensed SMPL-X asset
  descriptor/import boundary.
- Deterministic opening-form key-frame annotation and feedback reports.
- Local SVG/HTML G1 render evidence and optional MuJoCo render evidence when
  local assets/dependencies are available.
- Teaching playback HTML, interactive public-demo export with optional original
  video sync, fail-closed G1 schematic-vs-actual labels, optional Viser local
  runtime contract, browser smoke, and capture-bundle evidence.
- Optional roboharness G1 MJCF descriptor registration and MuJoCo frame-sequence
  replay contract for actual G1 public-demo frames when local dependencies and
  assets are supplied; locally verified for the ignored `80s-92s` Baduanjin
  proof artifact set.
- A committed derived JSON sample at
  `samples/baduanjin-03-006-two-hands-80-92` that lets CI regenerate the
  Baduanjin real-demo public HTML and actual G1 MuJoCo replay frames without
  committing raw media, native checkpoints, pickles, or rendered PNG outputs.
- Local GPU-run preparation that writes a source materialization manifest, GVHMR
  export template, `export_neodojo_gvhmr.py`, and `run_gvhmr_neodojo.sh` under
  ignored `outputs/`.
- Returned GVHMR result inspection, returned JSON validation/import, and a
  real-conversion audit.

## What Does Not Exist Yet

- Checked-in local GVHMR execution environment.
- Checked-in local GMR execution environment.
- Checked-in native GVHMR/GMR checkpoints, pickles, source frames, raw video, or
  rendered PNG outputs.
- Published actual G1 MuJoCo frame-sequence replay on Pages.
- Completed simulator runtime pipeline.
- Built-in official SMPL-X body-model renderer.
- Production/live-client Viser capture.
- Published real demo.
- Broad static-analysis, type-checking, coverage, or release gates.

## Next Safe Work

1. Keep the local-only command surface small while adding a true local GVHMR
   execution contract.
2. Add a compact runbook for reproducing the verified ignored `80s-92s`
   Baduanjin proof from a local GMR checkout and local SMPL-X assets.
3. Decide separately whether a real-demo Pages promotion path should exist; do
   not publish generated media until licensing and artifact-size policy are set.
