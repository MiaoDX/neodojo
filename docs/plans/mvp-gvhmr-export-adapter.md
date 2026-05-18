# MVP GVHMR Export Adapter Plan

Status: IMPLEMENTED GPU-SIDE EXPORT HELPER; REAL ARTIFACT STILL EXTERNAL

## Goal

Close the gap between GVHMR's native `hmr4d_results.pt` output and the
project-owned `neodojo.gvhmr_smplx_joints.v1` import contract:

```text
GVHMR hmr4d_results.pt
  -> licensed local SMPL-X body model in the GPU/GVHMR environment
  -> named SMPL-X teaching joints
  -> neodojo.gvhmr_smplx_joints.v1 JSON
  -> local source validation and import-demo
```

This plan does not make the macOS CPU workspace run GVHMR. It makes the
external GPU handoff concrete enough that the GPU operator has an executable
export helper instead of only a blank JSON template.

## Dependencies

- [mvp-source-media-materialization.md](mvp-source-media-materialization.md)
  prepares the local trimmed-clip handoff without committing media.
- [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) owns the final
  GPU artifact proof.
- [mvp-gvhmr-source-validation.md](mvp-gvhmr-source-validation.md) validates
  the returned JSON against `source-materialization.json`.
- [mvp-local-motion-contract.md](mvp-local-motion-contract.md) imports the
  returned `neodojo.gvhmr_smplx_joints.v1` JSON.

## Inputs

- `source-materialization.json` from the local source handoff.
- GVHMR `hmr4d_results.pt` generated on a GPU-capable machine.
- Licensed local SMPL-X model directory in the GPU environment.
- `gvhmr-smplx-joints.template.json` from the neodojo handoff package.
- Runtime metadata: actual GVHMR command, upstream commit/version, hardware,
  and frame rate.

## Outputs

- `export_neodojo_gvhmr.py` in every `package-gpu-handoff` output directory.
- A bundled `source-materialization.json` copy so the GPU export command does
  not depend on repo-local paths after the handoff directory is copied.
- Handoff manifest fields pointing to that exporter and the command template.
- README instructions for running GVHMR first, then the exporter, then the
  local `make demo-real` return path.
- Focused tests that the exporter is packaged, dependency-lazy for `--help`,
  and recorded in the handoff manifest.

## Execution Tasks

1. Add GPU-side export helper.
   - [x] Ship a standalone `export_neodojo_gvhmr.py` template with the package.
   - [x] Keep `torch`, `smplx`, CUDA, and licensed SMPL-X assets as GPU-side
     runtime requirements only.
   - [x] Map SMPL-X output joints into the current neodojo teaching-joint set.
   - [x] Preserve source-materialization provenance, GVHMR command/runtime, and
     selected parameter block in the returned JSON.

2. Wire the helper into the handoff bundle.
   - [x] Copy the exporter into `outputs/gvhmr-gpu-handoff/`.
   - [x] Copy `source-materialization.json` into the handoff bundle.
   - [x] Record it in the manifest under the expected export and command
     sections.
   - [x] Use bundle-local filenames in the GPU-side exporter command.
   - [x] Mention the exporter and source-materialization copy in the generated
     handoff README.

3. Verify locally without pretending to run GVHMR.
   - [x] Compile the generated exporter script.
   - [x] Confirm `--help` works without importing `torch` or `smplx`.
   - [x] Keep the real conversion gate blocked until a real GPU-produced JSON
     artifact is returned and validated.

## Acceptance Evidence

- `make gpu-handoff SOURCE_MATERIALIZATION=...` writes
  `export_neodojo_gvhmr.py` beside `manifest.json`, `README.md`, and
  `gvhmr-smplx-joints.template.json`, plus a copyable
  `source-materialization.json`.
- `gvhmr-smplx-joints.template.json` and the packaged GPU-side exporter
  explicitly write `fixture_only: false` into the returned
  `neodojo.gvhmr_smplx_joints.v1` JSON, so real GPU exports are not inferred
  only from a missing fixture flag.
- The handoff manifest records `commands.gpu_export_neodojo` and
  `expected_export.gpu_exporter_script`.
- The generated README has a GPU-side exporter command after the upstream
  GVHMR command.
- The GPU-side exporter command uses bundle-local filenames for the template,
  source-materialization manifest, and returned JSON.
- Unit tests compile the generated exporter and run `--help` without optional
  GPU dependencies installed.
- Docs continue to state that actual GVHMR inference, SMPL-X model execution,
  and the first real artifact remain external to this repo until the GPU run
  returns a validated JSON export.

## Non-Goals

- Running GVHMR on this macOS CPU workspace.
- Bundling SMPL-X model files, GVHMR checkpoints, videos, `.pt` files, or
  generated motion artifacts.
- Claiming a working end-to-end real conversion without a GPU-produced
  `neodojo.gvhmr_smplx_joints.v1` export.
- Supporting every possible upstream GVHMR result shape beyond the documented
  `smpl_params_global` / `smpl_params_incam` blocks.

## Stop Condition

Stop when the GPU handoff package contains an executable exporter helper,
records the helper in machine-readable metadata, and local tests prove the
helper can be inspected without optional GPU dependencies. The broader real
conversion gate remains open until a real GVHMR run returns a validated
neodojo export.
