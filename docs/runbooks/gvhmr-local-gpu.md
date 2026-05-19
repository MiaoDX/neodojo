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
- A local source clip from a documented public source index, or another
  user-supplied clip. Preserve the source URL/provenance in the generated
  manifests; do not commit or publish the raw source video from this repo.

The current local Baduanjin proof uses public source-index item `03-006`
(`5八段锦两手托天理三焦`) from `video/original_videos.md`, trim `80s-92s`.

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

## MuJoCo GL Backend Notes

Use an explicit `MUJOCO_GL` value for reproducible rendering:

- `MUJOCO_GL=glfw`: display-backed OpenGL. On headless CI, run it through
  `xvfb-run -a`; on a desktop session, no Xvfb wrapper is needed.
- `MUJOCO_GL=osmesa`: CPU software headless rendering. Useful on GitHub-hosted
  Ubuntu if `libosmesa6` and matching Python OpenGL dependencies are installed;
  typically slower than GPU-backed EGL/GLFW.
- `MUJOCO_GL=egl`: headless GPU rendering. Prefer this for self-hosted GPU
  runners with working EGL/NVIDIA or Mesa EGL support.

The backend should not materially change the G1 pose, camera, or labels. Minor
pixel-level differences can happen from different OpenGL drivers, especially
around anti-aliasing, depth edges, and shading. For CI, compare manifest fields,
resolution, nonblank pixels, and frame-change evidence rather than exact PNG
hashes across different GL backends.
