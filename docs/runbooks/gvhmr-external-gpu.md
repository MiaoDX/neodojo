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
Upstream now defaults away from DPVO for faster inference through SimpleVO;
install DPVO only when the selected GPU run genuinely needs that optional visual
odometry path.

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

To regenerate the archive and the operator request together:

```bash
make real-gpu-run-request LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin
```

To regenerate the archive, operator request, and Colab notebook together:

```bash
make real-gpu-colab-notebook LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin
```

To regenerate those files and collocate them into one operator package folder:

```bash
make real-gpu-operator-package LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin
```

To record whether this local workspace has any configured GPU execution route:

```bash
make gpu-execution-probe
python -m json.tool outputs/gvhmr-gpu-execution-probe/manifest.json

make gpu-execution-probe GPU_PROBE_GITHUB_REPO=MiaoDX/neodojo
python -m json.tool outputs/gvhmr-gpu-execution-probe/manifest.json
```

This probe records command presence and environment-variable names only. It
does not record secret values and does not run GVHMR. When
`GPU_PROBE_GITHUB_REPO` or CLI `--github-repo` is supplied, it also checks
self-hosted GitHub GPU runner visibility and repository secret counts through
`gh` without recording secret values or secret names.

The expanded form is:

```bash
make real-handoff LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin REAL_DRY_RUN=0
make gpu-input-bundle GPU_HANDOFF=outputs/gvhmr-gpu-handoff GPU_INPUT_INCLUDE_MEDIA=1
make gpu-input-archive GPU_INPUT=outputs/gvhmr-gpu-input
```

The resulting media-containing archive must remain under ignored outputs and
must not be committed or uploaded as a public CI artifact.

Before sending the archive to a GPU operator, generate the concise request
artifact if it was not already created by `make real-gpu-run-request`:

```bash
make gvhmr-run-request GPU_INPUT_ARCHIVE=outputs/gvhmr-gpu-input-archive
python -m json.tool outputs/gvhmr-gpu-run-request/manifest.json
```

The generated `outputs/gvhmr-gpu-run-request/README.md` summarizes the archive
hash, required GPU assets, expected return artifact, GPU command, and local
`make real-artifact-intake` / `make verify-real` checks. It is a handoff aid;
the media-containing archive and returned GVHMR artifacts still stay under
ignored outputs.

To generate a Colab-ready operator notebook from that request:

```bash
make gvhmr-colab-notebook GVHMR_RUN_REQUEST=outputs/gvhmr-gpu-run-request
```

The notebook writes checksum verification, archive unpacking, runner help
validation, guarded GVHMR execution, returned JSON download, and local return
commands into `outputs/gvhmr-colab-operator/gvhmr-colab-operator.ipynb`.

To collocate an existing archive, request, and notebook into one package:

```bash
make gvhmr-operator-package \
  GPU_INPUT_ARCHIVE=outputs/gvhmr-gpu-input-archive \
  GVHMR_RUN_REQUEST=outputs/gvhmr-gpu-run-request \
  GVHMR_COLAB_NOTEBOOK=outputs/gvhmr-colab-operator
```

The package writes `outputs/gvhmr-operator-package/manifest.json`, `README.md`,
`archive/`, `request/`, and `colab/`, then validates the copied package before
returning. Media-containing packages remain ignored and must not be committed
or uploaded as public CI artifacts.

To validate an already-collocated package before transfer or self-hosted
workflow dispatch:

```bash
make gvhmr-operator-package-validate GVHMR_OPERATOR_PACKAGE=outputs/gvhmr-operator-package
```

This checks the package, request, and notebook schemas plus the copied archive,
request, and notebook checksum links.

## Optional Self-Hosted GPU Workflow

If a user-managed GitHub Actions runner with labels `self-hosted` and `gpu`
has access to the prepared archive or operator package, GVHMR dependencies,
checkpoints, and licensed local SMPL-X assets, use the manual workflow
`gvhmr-self-hosted-gpu`.

The workflow is defined at
`.github/workflows/gvhmr-self-hosted-gpu.yml`. It is `workflow_dispatch` only;
it does not run on push or pull requests. It accepts either:

- `gpu_input_archive_path`: path on the self-hosted runner to
  `neodojo-gvhmr-gpu-input.tar.gz`
- `gvhmr_operator_package_path`: path on the self-hosted runner to
  `outputs/gvhmr-operator-package/` or its `manifest.json`

Its required runtime inputs are:

- `gvhmr_repo`: existing GVHMR checkout or install destination
- `smplx_model_dir`: licensed local SMPL-X model directory

When `gvhmr_operator_package_path` is provided, the workflow validates the
package, run-request, and notebook manifest schemas plus the copied archive,
request, and notebook checksums before unpacking.

Optional inputs allow installing GVHMR, exporting from an existing
`hmr4d_results.pt` with `skip_gvhmr`, selecting `smpl_params_global` or
`smpl_params_incam`, opting into a short-lived upload of only
`gvhmr-smplx-joints.json`, and opting into generated real-demo artifact upload.
After GVHMR export, the workflow runs `make real-artifact-intake` and
`real-conversion audit-completion --require-complete` against the returned JSON
and bundled `source-materialization.json`. Do not use the workflow to upload
source videos, trimmed clips, checkpoints, SMPL-X assets, `.pt` files, rendered
videos, logs, or full result directories.

If the self-hosted workflow uploaded `neodojo-self-hosted-real-demo`, the
generated public-demo artifact can be promoted to GitHub Pages through the
separate manual workflow `promote-real-demo-pages`. That workflow requires the
self-hosted workflow run ID, explicit `confirm_replace_fixture_pages=true`, and
repository variable `NEODOJO_DEPLOY_REAL_PAGES=true`. Before deploying, it
revalidates the real-demo manifest, strict audit manifest, public-demo files,
SMPL-X scoring boundary, and `neodojo demo smoke`. Use this only after rights
and artifact provenance have been reviewed; it does not publish media,
checkpoints, SMPL-X assets, `.pt` files, logs, or full GVHMR result
directories. To run the same promotion validation locally against a downloaded
artifact directory before dispatching the workflow:

```bash
make real-demo-pages-promotion-validate \
  PROMOTION_DOWNLOAD_ROOT=outputs/promoted-real-demo-download \
  PROMOTION_SOURCE_RUN_ID=<self-hosted-run-id>
```

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
