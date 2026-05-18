# GVHMR Local GPU Runbook

This runbook covers the supported real-conversion path: prepare a local source
clip, run GVHMR on a local CUDA machine, export a
`neodojo.gvhmr_smplx_joints.v1` JSON, then import and audit it locally.

It does not cover Colab, hosted GPU providers, external operator packages,
self-hosted GitHub Actions runners, or real-demo Pages promotion.

## Preconditions

- A local CUDA-capable machine.
- A local GVHMR checkout and dependencies.
- Local licensed SMPL-X assets. Do not commit or publish them.
- A local/user-supplied source clip with rights approval for this use.

## Prepare The Local Run Workspace

```bash
make real-gpu-prep \
  LOCAL_VIDEO=path/to/local-source.mp4 \
  REAL_LOCAL_SOURCE_ID=local-baduanjin \
  REAL_DRY_RUN=0
```

This writes:

- `outputs/real-conversion-gate/real-conversion-prep.json`
- `outputs/real-conversion-source/source-materialization.json`
- `outputs/gvhmr-local-gpu-run/manifest.json`
- `outputs/gvhmr-local-gpu-run/gvhmr-smplx-joints.template.json`
- `outputs/gvhmr-local-gpu-run/export_neodojo_gvhmr.py`
- `outputs/gvhmr-local-gpu-run/run_gvhmr_neodojo.sh`

All of these outputs are ignored. Source media, GVHMR checkpoints, SMPL-X
assets, `.pt` results, generated JSON, rendered media, and logs must stay out of
git.

## Run GVHMR Locally

From the generated local GPU workspace:

```bash
cd outputs/gvhmr-local-gpu-run
SMPLX_MODEL_DIR=/path/to/licensed/smplx/body_models \
GVHMR_REPO=/path/to/GVHMR \
./run_gvhmr_neodojo.sh --install
```

The wrapper delegates to upstream GVHMR and then uses
`export_neodojo_gvhmr.py` to write `gvhmr-smplx-joints.json`.

## Inspect Or Import The Result

To inspect a native GVHMR result before export:

```bash
make gvhmr-inspect GVHMR_RESULT=path/to/hmr4d_results.pt
```

To import the returned neodojo JSON:

```bash
make real-artifact-intake \
  REAL_ARTIFACT_SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json \
  REAL_ARTIFACT_GVHMR_JSON=outputs/gvhmr-local-gpu-run/gvhmr-smplx-joints.json
```

Then run the strict real gate:

```bash
make verify-real
```

`make verify-real` only passes when the source materialization, returned GVHMR
JSON, imported real-demo manifest, and public-demo manifest prove a non-fixture
real GVHMR artifact.
