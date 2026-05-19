# Status

neodojo is in bootstrap state with a fixture-only public demo and a local ignored
real GVHMR proof.

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
- The generated public-demo `index.html` is now an interactive two-panel
  teaching replay: SMPL-X skeleton teaching track on the left, Unitree G1 robot
  model replay on the right, and one synchronized timeline. The default G1
  replay is still fixture-derived unless an imported GMR track and registered
  model descriptor are supplied.
- A local ignored GPU proof exists in this workspace for a visible-motion
  Baduanjin clip (`80s-92s` from the local 12m08s source video): non-fixture
  GVHMR SMPL-X JSON, imported under ignored `outputs/real-demo/`, with a strict
  local audit reporting `real_demo_verified`, checking the two-panel public
  teaching HTML profile, and rejecting GVHMR exports that are too static for a
  teaching replay.

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
make smoke-public
```

Local real-conversion preparation and returned-artifact handling:

```bash
make real-gpu-prep LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin REAL_DRY_RUN=0
make gvhmr-inspect GVHMR_RESULT=path/to/hmr4d_results.pt
make real-artifact-intake REAL_ARTIFACT_SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json REAL_ARTIFACT_GVHMR_JSON=path/to/gvhmr-smplx-joints.json
make demo-real SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json GVHMR_JSON=path/to/gvhmr-smplx-joints.json
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
- Dependency-light SMPL-X surface proxy and local-only licensed SMPL-X asset
  descriptor/import boundary.
- Deterministic opening-form key-frame annotation and feedback reports.
- Local SVG/HTML G1 render evidence and optional MuJoCo render evidence when
  local assets/dependencies are available.
- Teaching playback HTML, interactive two-panel public-demo export, optional
  Viser local runtime contract, browser smoke, and capture-bundle evidence.
- Local GPU-run preparation that writes a source materialization manifest, GVHMR
  export template, `export_neodojo_gvhmr.py`, and `run_gvhmr_neodojo.sh` under
  ignored `outputs/`.
- Returned GVHMR result inspection, returned JSON validation/import, and a
  real-conversion audit.

## What Does Not Exist Yet

- Checked-in local GVHMR execution environment.
- Checked-in local GMR execution environment.
- Default true GMR-derived Unitree G1 replay.
- Completed simulator runtime pipeline.
- Built-in official SMPL-X body-model renderer.
- Production/live-client Viser capture.
- Committed generated motion artifact.
- Published real demo.
- Broad static-analysis, type-checking, coverage, or release gates.

## Next Safe Work

1. Keep the local-only command surface small while adding a true local GVHMR
   execution contract.
2. Add real GMR/G1 retargeting once a local GMR runtime contract exists.
3. Continue simulator rendering polish with local assets and screenshot/frame
   evidence.
