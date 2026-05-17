# MVP GVHMR GPU Runner Surface Plan

Status: IMPLEMENTED CI-SAFE GPU RUNNER PACKAGING; REAL ARTIFACT STILL EXTERNAL

## Goal

Make the remaining external GVHMR step executable from the neodojo handoff
bundle instead of leaving it as loose prose.

The local macOS/CI lane must still not run GVHMR. This slice packages a
GPU-side runner that a CUDA operator can execute inside the ignored bundle to
run upstream GVHMR and then call the neodojo exporter helper.

## Dependencies

- [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) defines the real
  artifact gate and the external GPU boundary.
- [mvp-source-media-materialization.md](mvp-source-media-materialization.md)
  provides the trimmed source clip handoff.
- [mvp-gvhmr-export-adapter.md](mvp-gvhmr-export-adapter.md) provides the
  GPU-side `export_neodojo_gvhmr.py` helper.
- Upstream GVHMR still owns its CUDA environment, checkpoints, and licensed
  SMPL/SMPL-X asset setup. Current upstream references:
  - https://github.com/zju3dv/GVHMR
  - https://github.com/zju3dv/GVHMR/blob/main/docs/INSTALL.md

## Inputs

- A `neodojo.gvhmr_gpu_handoff.v1` handoff directory.
- Optional materialized `source/trimmed-clip.mp4` inside an ignored GPU input
  bundle.
- A GPU machine with GVHMR dependencies, checkpoints, and licensed local
  SMPL-X assets.

## Outputs

- `run_gvhmr_neodojo.sh` in the GPU handoff directory.
- `run_gvhmr_neodojo.sh` in the copyable GPU input bundle.
- Manifest fields naming the runner and the one-command GPU invocation.
- CI-safe smoke evidence that the runner is packaged, executable, and
  syntactically valid without running GVHMR or copying media.

## Execution Tasks

- [x] Add a package-data shell template for the GPU runner.
- [x] Package the runner into `package-gpu-handoff`.
- [x] Package or synthesize the runner in `package-gpu-input` so older handoff
  metadata can still produce a runnable transfer bundle.
- [x] Document the runner in `README.md`, `README.zh.md`, `STATUS.md`, and the
  real-conversion gate.
- [x] Add `make gpu-input-bundle-smoke` and include it in `make verify`.
- [x] Upload the metadata-only GPU input bundle smoke artifact from CI.
- [x] Add focused tests for runner packaging, executable bit, `bash -n`, and
  `--help` behavior.

## Acceptance Evidence

- `make gpu-input-bundle-smoke` writes
  `outputs/gvhmr-gpu-input-smoke/run_gvhmr_neodojo.sh` and checks it with
  `bash -n`.
- Unit tests assert that both handoff and input-bundle manifests name
  `run_gvhmr_neodojo.sh`.
- CI uploads `neodojo-gpu-input-bundle-smoke` without media.
- The runner requires `SMPLX_MODEL_DIR` for export and does not download or
  commit licensed assets.

## Non-Goals

- Running GVHMR on the local macOS CPU workspace.
- Provisioning a paid GPU provider account.
- Downloading GVHMR checkpoints or licensed SMPL/SMPL-X assets into this repo.
- Committing source videos, `.pt`, `.pkl`, `.npz`, rendered videos, or generated
  motion outputs.
- Marking the real-conversion gate complete before a real
  `neodojo.gvhmr_smplx_joints.v1` export is returned and imported.

## Stop Condition

Stopped when every generated GPU handoff/input bundle includes an executable
runner script, CI verifies the runner packaging without media or GPU execution,
and the only remaining real-conversion blocker is still the external
GPU-produced GVHMR export.
