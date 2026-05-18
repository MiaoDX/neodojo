# MVP DevEx And CI Surface Plan

Status: IMPLEMENTED WITH BROWSER CAPTURE, REAL-HANDOFF, GPU-INPUT, GPU-ARCHIVE, GPU-EXECUTION-PROBE, AND REAL-ARTIFACT-INTAKE SMOKE ARTIFACT CI VERIFIED

## Goal

Add the minimal developer and CI surface needed to regenerate and publish the
non-GPU demo lane:

```text
one local command
  -> fixture motion/contracts
  -> G1 visual/render inputs
  -> teaching playback
  -> Rerun public-demo export
  -> screenshot smoke check
  -> generated capture bundle
  -> optional browser-rendered screenshot capture
  -> uploaded artifact
  -> GitHub Pages publish
```

The goal is a reproducible command and CI lane for fixture/non-GPU artifacts.
Do not claim install, lint, build, or CI support before the actual command
surface and workflow exist. The later
[mvp-lint-build-surface.md](mvp-lint-build-surface.md) slice owns the minimal
lint/build commands.

## Dependencies

- [mvp-pipeline-contract-hardening.md](mvp-pipeline-contract-hardening.md)
  stabilizes the manifests that CI should validate.
- [mvp-visualization-and-public-demo.md](mvp-visualization-and-public-demo.md)
  defines the Rerun export, static viewer page, screenshot, and public-demo
  manifest.
- Existing `make test`, `make demo-html`, and Python module entrypoints remain
  the current runnable surface until this slice adds more.
- GitHub Pages publishing requires repository settings and workflow permissions
  that may need manual owner configuration.

## Implemented Local Path

`make demo-public` now regenerates the fixture motion contract, detected
annotations, fixture G1 model descriptor, G1 visual track, G1 SVG/HTML render
evidence, teaching playback HTML/manifest, public-demo scene, `.rrd` fallback
artifact, SVG screenshot, public-demo manifest, Viser runtime contract, and
front/side/top Viser preview screenshots. It then runs `neodojo demo smoke`
against `outputs/public-demo` and `neodojo capture bundle` to write
`outputs/capture/manifest.json`.

`make verify` now wraps the default dependency-light local lane: lint, plan
quality checks, tests, wheel build, `make demo-public`,
`make real-handoff-smoke`, `make gpu-input-bundle-smoke`,
`make gpu-input-archive-smoke`, `make gpu-execution-probe`, and
`make real-artifact-intake-smoke`, and `make real-conversion-audit`.
`make demo-public-browser` adds the optional Playwright-backed Chromium
screenshot capture and refreshes the capture bundle with browser evidence.
`make real-artifact-intake-smoke` writes fixture-only source materialization
and GVHMR JSON inputs, then runs the standard `make real-artifact-intake`
wrapper so the returned-artifact import path is covered without a GPU artifact.
The generated real-demo manifest distinguishes `gvhmr_artifact_imported` from
`real_gvhmr_artifact_imported` so fixture smoke does not masquerade as a real
GVHMR result.

`.github/workflows/public-demo.yml` installs the package, runs lint, plan
quality checks, tests, wheel build, runs `make real-handoff-smoke`, uploads a
metadata-only `neodojo-real-handoff-smoke` artifact from that smoke, runs
`make gpu-input-bundle-smoke`, uploads a metadata-only
`neodojo-gpu-input-bundle-smoke` artifact, runs
`make gpu-input-archive-smoke`, uploads a metadata-only
`neodojo-gpu-input-archive-smoke` artifact, runs `make gpu-execution-probe`,
uploads a metadata-only `neodojo-gpu-execution-probe` artifact, runs
`make real-artifact-intake-smoke`, uploads a fixture-only
`neodojo-real-artifact-intake-smoke` artifact, runs
`make real-conversion-audit`, uploads a metadata-only
`neodojo-real-conversion-audit` artifact, installs Chromium through the
optional Playwright browser extra, and runs `make demo-public-browser`. It
uploads `outputs/public-demo` as the standalone
public-demo artifact, uploads `outputs/browser-capture` as browser evidence,
uploads a capture-bundle artifact containing `outputs/capture` plus the
referenced public-demo, browser-capture, Viser runtime, and G1 render evidence,
and uploads the public-demo directory as the GitHub Pages artifact. The deploy
job runs only on `main` outside pull requests when Pages is configured and
`NEODOJO_DEPLOY_PAGES=true` is set as a repository variable. Pages is now
configured and the live fixture-only URL is verified at
`https://miaodx.com/neodojo/`.

GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/25999641059` verified the
default CI lane on `main`: lint, plan quality checks, tests, wheel build,
public-demo generation, public-demo artifact upload, capture-bundle artifact
upload, Pages artifact upload, and Pages deployment completed. The downloaded
`neodojo-public-demo` artifact passed
`PYTHONPATH=src python3 -m neodojo demo smoke --public-demo outputs/ci-public-demo-latest`,
and the downloaded `neodojo-capture-bundle` artifact contained all manifest
references needed for the generated multi-camera evidence bundle. The live
`https://miaodx.com/neodojo/` HTML, screenshot SVG, and manifest returned the
expected fixture-only labels.

GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/26000413142` verified the
browser-capture CI lane on `main`: Chromium installed through Playwright,
`make demo-public-browser` passed, `neodojo-browser-capture` contained a
1280x720 PNG plus `neodojo.browser_capture.v1` manifest, the capture bundle
recorded `real_browser_capture: true`, and Pages deployed.

GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/26003369563` verified the
metadata-only real-handoff smoke artifact on `main`: lint, plan quality checks,
tests, wheel build, `make real-handoff-smoke`, handoff artifact upload, browser
capture, capture-bundle upload, Pages artifact upload, and Pages deployment
passed. The downloaded `neodojo-real-handoff-smoke` artifact contained the
prep manifest, source-materialization manifest, GPU handoff manifest, README,
source-materialization copy, GVHMR export template, and GPU-side exporter
helper, and contained no video files.

GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/26004331422` verified the
GPU input bundle smoke artifact on `main`: `make gpu-input-bundle-smoke`
passed, the `neodojo-gpu-input-bundle-smoke` artifact uploaded
`RUN_ON_GPU.md`, handoff metadata, the export template, exporter helper, and
`run_gvhmr_neodojo.sh`, and Pages deployed. The artifact does not include
source media.

GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/26005618093` verified the
metadata-only GPU execution probe artifact on `main`: `make
gpu-execution-probe` passed, the `neodojo-gpu-execution-probe` artifact
uploaded `neodojo.gvhmr_gpu_execution_probe.v1`, no secret values were recorded,
and the artifact classified the CI runner as `external_gpu_artifact_missing`
with no local CUDA, Docker GPU runtime, or configured GPU provider candidate.

GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/26006210299` verified the
fixture-only real-artifact intake smoke artifact on `main`: `make
real-artifact-intake-smoke` passed, the
`neodojo-real-artifact-intake-smoke` artifact uploaded source materialization,
GVHMR JSON, source-validation, real-demo, public-demo, and capture manifests,
the source-validation report passed with 36 frames at 24 fps, the real-demo
manifest records `real_gvhmr_artifact_imported: false` for fixture smoke, and
the artifact contains no source media or checkpoint/model files.

GitHub Actions run
`https://github.com/MiaoDX/neodojo/actions/runs/26006485103` verified the
real-conversion completion audit artifact on `main`: `make
real-conversion-audit` passed, the `neodojo-real-conversion-audit` artifact
uploaded only `neodojo.real_conversion_audit.v1` and nested
`neodojo.gvhmr_gpu_execution_probe.v1` manifests, and the audit classified the
gate as `external_gpu_artifact_missing` with `complete: false`. The opt-in
strict local gate is `make verify-real`, which runs the same audit with
`--require-complete` and is expected to fail until a real non-fixture artifact
has been imported.

## Inputs

- Existing fixture generation commands.
- Hardened manifest validators and fixture data.
- Rerun public-demo export command and static viewer page.
- Browser or headless screenshot tool selected by the implementation.
- GitHub Actions environment and repository Pages settings.
- `.gitignore` policy excluding generated outputs, screenshots, `.rrd`, videos,
  logs, and large artifacts.

## Outputs

- A one-command local orchestration target, for example:

  ```bash
  make demo-public
  make demo-public-browser
  ```

  or an equivalent CLI flow that regenerates all non-GPU demo artifacts from
  fixtures.

- Minimal package/dev command surface required by the command, such as
  project metadata or scripts, only if the repo needs them to run reliably.
- Focused CI jobs for:
  - unit tests
  - fixture demo generation
  - manifest validation
  - Rerun `.rrd` export
  - static page generation
  - screenshot capture
  - generated capture bundle validation
  - nonblank visual smoke checks
  - artifact upload
  - GitHub Pages publish
- A visual smoke check that verifies generated HTML/Rerun pages are nonblank and
  contain expected tracks, labels, fixture-only status, and scoring-source
  metadata.
- Documentation updates that describe only commands and CI jobs that exist.

## Execution Tasks

1. Choose the orchestration surface.
   - [x] Use `make demo-public` as the one local command.
   - [x] Use `neodojo demo smoke` for explicit artifact validation.
   - [x] Keep commands small and reproducible.

2. Add minimal dev setup only when necessary.
   - [x] Reuse existing `pyproject.toml` and editable install in CI.
   - [x] Defer lint/build claims to a dedicated command-surface slice.
   - [x] Keep optional heavyweight visualization dependencies out of the
     default path.

3. Build the local demo-public flow.
   - [x] Generate motion-record and teaching-track fixtures.
   - [x] Generate deterministic opening-form annotations.
   - [x] Generate G1 visual-track fixtures.
   - [x] Generate G1 render evidence and teaching playback HTML/manifest.
   - [x] Export `.rrd` fallback artifact and static viewer page.
   - [x] Capture SVG screenshot evidence.
   - [x] Write a public-demo manifest.
   - [x] Write a generated multi-camera capture bundle manifest.
   - [x] Add optional browser-rendered public-demo screenshot capture.

4. Add CI validation.
   - [x] Run `make test`.
   - [x] Run `make demo-public`.
   - [x] Run `make demo-public-browser` in CI after installing the optional
     browser runtime.
   - [x] Validate generated public-demo artifacts with `neodojo demo smoke`.
   - [x] Upload generated outputs as CI artifacts without committing them.
   - [x] Upload the dry-run real-handoff smoke metadata bundle without the
     placeholder source media.
   - [x] Upload the metadata-only GPU input bundle smoke artifact with
     `run_gvhmr_neodojo.sh` and no media.
   - [x] Upload the metadata-only GPU input archive smoke artifact with no
     media.
   - [x] Upload the metadata-only GPU execution probe artifact with no secret
     values.
   - [x] Upload the fixture-only real-artifact intake smoke artifact with no
     media.
   - [x] Upload the metadata-only real-conversion completion audit artifact.
   - [x] Add an opt-in strict local real-completion gate without making the
     fixture-only CI lane fail before a GPU artifact exists.

5. Add visual smoke checks.
   - [x] Check generated HTML, scene, `.rrd` fallback, and SVG screenshot are
     nonblank.
   - [x] Check expected text or scene labels for SMPL-X, G1, fixture-only
     status, and scoring-source metadata.
   - [x] Save SVG screenshots as artifacts.
   - [x] Add browser-rendered screenshot capture with optional Playwright
     dependency in CI.

6. Publish to GitHub Pages.
   - [x] Stage only static public-demo assets in the Pages artifact.
   - [x] Do not publish source videos, generated motion files, checkpoints,
     logs, or large private artifacts.
   - [x] Keep repository owner setup explicit through the
     `NEODOJO_DEPLOY_PAGES` repository variable.
   - [x] Verify the live Pages URL before adding public README links.

7. Update docs after verification.
   - [x] README.md and README.zh.md describe the local command, workflow, and
     verified Pages URL.
   - [x] STATUS.md lists new commands only after they run locally.
   - [x] Keep fixture-only limitations visible in every user-facing mention.

## Acceptance Evidence

- One local command regenerates the fixture public-demo artifacts from a clean
  ignored output directory.
- Unit tests and manifest validation pass locally; CI is configured to run the
  same commands.
- CI uploads the generated `.rrd` fallback recording, static viewer page, SVG
  screenshot, public-demo manifest, browser-rendered PNG screenshot, generated
  capture bundle artifact with referenced evidence, and metadata-only
  real-handoff smoke artifact without source media, verified by runs
  `25999641059`, `26000413142`, and `26003369563`.
- CI uploads the metadata-only GPU input bundle smoke artifact with the
  executable runner script and no source media, verified by run `26004331422`.
- CI uploads the metadata-only GPU input archive smoke artifact with no source
  media.
- CI uploads the metadata-only GPU execution probe artifact with command/env-key
  readiness evidence and no secret values, verified by run `26005618093`.
- CI uploads the fixture-only real-artifact intake smoke artifact with
  source-validation, public-demo, and capture manifests but no media, verified
  by run `26006210299`.
- CI uploads the real-conversion completion audit artifact with blocker status
  and no media, verified by run `26006485103`.
- The visual smoke check proves the generated pages are nonblank and include
  expected tracks/labels.
- GitHub Pages publishes only safe static demo assets once repository Pages is
  enabled and the deploy toggle is set.
- README.md and README.zh.md mention the public demo command, workflow,
  verified live URL, and fixture-only status.
- Generated outputs, screenshots, `.rrd`, videos, logs, browser captures, and
  large artifacts remain out of tracked source except for deliberate publish
  artifacts.

## Non-Goals

- Running GVHMR, GMR, HAMER, or any GPU inference in CI.
- Adding broad lint or build systems beyond the dedicated minimal
  lint/build-surface slice.
- Publishing official source videos or generated motion artifacts.
- Making CI the proof of qigong correctness.
- Replacing later real-artifact or Viser work.

## Stop Condition

Stopped when a clean checkout can run one non-GPU public-demo command locally,
CI can regenerate and visually smoke-test the same artifact set, and GitHub
Pages publishing can run without tracking generated outputs in the source
branch.
