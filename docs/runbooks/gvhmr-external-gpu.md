# GVHMR External GPU Artifact Runbook

This runbook is for the remaining real-conversion step that cannot run on the
local macOS CPU workspace: produce one real
`neodojo.gvhmr_smplx_joints.v1` export from a prepared neodojo GPU input
archive.

It does not replace the generated `RUN_ON_GPU.md` inside each archive. Treat
that generated file as the bundle-specific source of truth, and this document
as the durable operator checklist.

## Inputs

- A neodojo GPU input archive, for example:
  `outputs/gvhmr-gpu-input-archive-local-bilibili/neodojo-gvhmr-gpu-input.tar.gz`.
- A CUDA-capable machine with shell access.
- Local licensed SMPL-X model assets. Do not upload or commit these assets to
  the neodojo repository.
- GVHMR checkpoints and dependencies in the GPU environment.
- Rights approval for the selected source clip.

## Upstream References

- GVHMR repository: <https://github.com/zju3dv/GVHMR>
- GVHMR installation notes:
  <https://github.com/zju3dv/GVHMR/blob/main/docs/INSTALL.md>

As of May 18, 2026, upstream GVHMR documents a Python 3.10 environment,
`pip install -r requirements.txt`, editable install, a Google Colab demo, a
Hugging Face demo, and the demo entrypoint
`python tools/demo/demo.py --video=... -s` for static-camera inference.
The install notes also require separately downloaded SMPL/SMPL-X model assets
and GVHMR/HMR2/ViTPose/YOLO checkpoints under `inputs/checkpoints/`.

## Prepare The Local Archive

For the current ignored local Bilibili candidate, the archive already exists:

```bash
ls -lh outputs/gvhmr-gpu-input-archive-local-bilibili/neodojo-gvhmr-gpu-input.tar.gz
python -m json.tool outputs/gvhmr-gpu-input-archive-local-bilibili/manifest.json
```

For another local source, regenerate the handoff:

```bash
make real-gpu-archive LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin
```

To record whether this local workspace has any configured GPU execution route:

```bash
make gpu-execution-probe
python -m json.tool outputs/gvhmr-gpu-execution-probe/manifest.json
```

This probe records command presence and environment-variable names only. It
does not record secret values and does not run GVHMR.

The expanded form is:

```bash
make real-handoff LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin REAL_DRY_RUN=0
make gpu-input-bundle GPU_HANDOFF=outputs/gvhmr-gpu-handoff GPU_INPUT_INCLUDE_MEDIA=1
make gpu-input-archive GPU_INPUT=outputs/gvhmr-gpu-input
```

The resulting media-containing archive must remain under ignored outputs and
must not be committed or uploaded as a public CI artifact.

## Run On The GPU Machine

Copy the archive to the GPU machine, then unpack it:

```bash
mkdir -p neodojo-gvhmr-run
tar -xzf neodojo-gvhmr-gpu-input.tar.gz -C neodojo-gvhmr-run
cd neodojo-gvhmr-run
python -m json.tool manifest.json
```

Create or activate the GVHMR environment. Follow upstream GVHMR docs for exact
provider-specific setup; the durable shape is:

```bash
git clone https://github.com/zju3dv/GVHMR
cd GVHMR
conda create -y -n gvhmr python=3.10
conda activate gvhmr
pip install -r requirements.txt
pip install -e .
mkdir -p inputs/checkpoints
```

Place licensed body-model files and downloaded checkpoints in the structure
required by upstream GVHMR. Keep those assets outside git.

Return to the unpacked neodojo bundle and run the packaged wrapper:

```bash
cd /path/to/neodojo-gvhmr-run
chmod +x run_gvhmr_neodojo.sh
GVHMR_REPO=/path/to/GVHMR \
SMPLX_MODEL_DIR=/path/to/GVHMR/inputs/checkpoints/body_models/smplx \
OUTPUT_ROOT=/path/to/gvhmr-output \
STATIC_CAM=1 \
./run_gvhmr_neodojo.sh
```

For a provider where GVHMR is already installed, set `GVHMR_REPO` and omit
`--install`. For a fresh Python environment where the wrapper should clone and
install GVHMR with `pip`, run:

```bash
GVHMR_REPO=/path/to/GVHMR \
SMPLX_MODEL_DIR=/path/to/GVHMR/inputs/checkpoints/body_models/smplx \
./run_gvhmr_neodojo.sh --install
```

The wrapper writes `gvhmr-smplx-joints.json` in the bundle directory by
default. That JSON is the artifact to return to the local neodojo workspace.

## Validate Back Locally

Copy `gvhmr-smplx-joints.json` back to the local machine, then run:

```bash
make real-artifact-intake \
  REAL_ARTIFACT_SOURCE_MATERIALIZATION=outputs/real-handoff-local-bilibili/source-materialized/source-materialization.json \
  REAL_ARTIFACT_GVHMR_JSON=path/to/gvhmr-smplx-joints.json

make demo-real \
  SOURCE_MATERIALIZATION=outputs/real-handoff-local-bilibili/source-materialized/source-materialization.json \
  GVHMR_JSON=path/to/gvhmr-smplx-joints.json
```

Inspect:

```bash
python -m json.tool outputs/real-demo/manifest.json
PYTHONPATH=src python -m neodojo demo smoke --public-demo outputs/real-demo/public-demo
```

If import fails, classify it as one of:

- source provenance mismatch
- missing GVHMR runtime metadata
- unexpected upstream result shape
- SMPL-X model/export issue
- local neodojo contract issue

Only fix neodojo contracts when the returned artifact proves the contract is
too narrow for real GVHMR output.

## Stop Condition

Stop when `make demo-real` imports the returned
`neodojo.gvhmr_smplx_joints.v1` export and regenerates the real-demo public
artifact, or when the failure is classified with enough evidence for a focused
follow-up plan.
