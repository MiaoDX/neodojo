# Status

neodojo is in bootstrap state with one fixture-only local demo.

There is now a minimal checked-in Python package, a `make test` command,
fixture-backed and external-JSON `motion-record` paths, `robot-model`,
`tracks`, imported GMR JSON track, native GMR pickle normalization,
`smplx-surface proxy`, `smplx-surface mesh`, `annotations detect`, `render g1`,
optional `render mujoco-g1`,
`demo play`, `demo export-rerun`, optional `demo serve-viser`, and
`demo browser-smoke`, `capture recorder`, and `capture bundle` commands, a
`make demo-html` command that writes a
self-contained synthetic web demo, minimal `make lint`, `make check`, and
`make build` commands, `make demo-public` / optional
`make demo-public-browser` commands plus `make verify` and GitHub Actions
workflow for the fixture public-demo artifact, browser capture, generated
capture bundle, and metadata-only real-handoff smoke artifact,
`make real-handoff`, `make gpu-handoff`, `make gpu-input-bundle`,
`make gpu-input-bundle-smoke`, `make gpu-input-archive`, `make
real-gpu-archive`, `make real-gpu-run-request`,
`make real-gpu-colab-notebook`, `make real-gpu-operator-package`,
`make gpu-input-archive-smoke`, and
`make gpu-execution-probe`, `make gvhmr-run-request`, and
`make gvhmr-run-request-smoke`, `make gvhmr-colab-notebook`,
`make gvhmr-colab-notebook-smoke`, `make gvhmr-operator-package`, and
`make gvhmr-operator-package-smoke`, plus
`make gvhmr-operator-package-archive` and
`make gvhmr-operator-package-archive-smoke` for external GVHMR run metadata,
transfer bundles/archives, CI-safe GPU runner packaging, reproducible
GPU/provider readiness classification, generated GPU-operator run requests,
Colab operator notebooks, collocated operator packages, and single-file
operator package archives, metadata-only CI GPU
run-request/notebook/package/package-archive/probe artifacts, and a
tracked external-GPU operator runbook, `make gvhmr-inspect` for returned GVHMR
result inspection, `make demo-real` / `make real-artifact-intake` for a
validated external GVHMR JSON once a GPU artifact exists, and
`make real-artifact-intake-smoke` for fixture-backed coverage of that returned
artifact wrapper, and `make real-conversion-audit` for an executable blocker
classification of the real GVHMR gate, plus a manual
`.github/workflows/gvhmr-self-hosted-gpu.yml` workflow for user-managed
self-hosted GPU runners that also validates/imports the returned export, plus a
manual `.github/workflows/promote-real-demo-pages.yml` workflow for promoting a
validated self-hosted real-demo artifact to GitHub Pages only after explicit
confirmation and strict audit validation, plus
`make real-demo-pages-promotion-validate` for exercising the same promotion
artifact validator locally, with a verified live fixture-only GitHub Pages demo
at
`https://miaodx.com/neodojo/`. `real-conversion materialize-source` can also
prepare a dry-run or ffmpeg-backed local source clip handoff for a later GPU
GVHMR run, `real-conversion package-gpu-handoff` can package the handoff
manifest, export template, GPU-side exporter helper, executable GPU runner, and
return command for the external GPU operator, `real-conversion
package-gpu-input` can create an ignored copyable GPU input bundle with the
materialized trimmed clip and executable GPU runner when media inclusion is
explicit, `real-conversion archive-gpu-input` can create an ignored transfer
archive plus manifest from that bundle, `real-conversion inspect-gvhmr-result`
can inspect
returned GVHMR result keys and candidate SMPL-X parameter blocks,
`real-conversion validate-source` can validate a GVHMR JSON export against that
handoff before import, and `real-conversion import-demo` can regenerate the
local demo lane from that validated export. There is
still no checked-in local GVHMR/GMR execution environment, completed simulator
runtime pipeline, built-in official SMPL-X body-model renderer, real generated
motion artifact, or hosted/live-client Viser capture.

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
- Generated roboharness-style multi-camera capture evidence bundle from the
  current public-demo, Viser preview, G1 render artifacts, and optional
  browser-rendered public-demo screenshot, and optional MuJoCo simulator
  recorder capture; direct roboharness/live-runtime capture remains follow-on.
- Production Viser teaching UI contract and review-loop controls beyond the
  first optional local runtime; live-client browser capture remains follow-on.
- Key-frame detection and geometry-constrained verbal feedback for terms such as
  "sink the shoulders" and "drop the elbows".
- Fixture-only HTML teaching demo generated under `outputs/html-demo/`, proving
  the intended web playback shape without claiming real reconstruction or
  retargeting.
- Fixture-backed SMPL-X motion-record and teaching-track manifests, proving the
  local contract shape that later GVHMR/GMR imports should consume.
- External GVHMR SMPL-X teaching-joints JSON import into the same motion-record
  contract. This is an import boundary only, not local GVHMR execution or raw
  `.pt` parsing. When the external JSON carries `smplx_parameters`, the import
  path now preserves mesh-ready pose/shape parameter metadata under
  `motion-record/smplx-parameters.json` for the local mesh-frame import path.
- Fixture-backed Unitree G1 model descriptor, derived visual-track manifest, and
  comparison report with `g1_scoring_allowed: false`.
- Normalized external GMR Unitree G1 JSON import into the same G1 visual-track
  contract, preserving imported joint angles while keeping G1 non-scoring.
- Native YanjieZe/GMR robot-motion pickle normalization into the same
  `neodojo.gmr_unitree_g1_track.v1` import contract. This parses the saved
  `--save_path` artifact shape, preserves Unitree G1 joint angles, derives the
  current viewer joints from the source SMPL-X motion record, and does not run
  GMR locally.
- Dependency-light SMPL-X capsule surface proxy generated from teaching joints
  under `outputs/smplx-surface/`. It is a visual-only inspection layer in
  teaching/public demos, not a licensed SMPL-X body mesh and not a scoring
  source. A local-only licensed SMPL-X asset descriptor, imported mesh-ready
  SMPL-X pose/shape parameter validation, and external mesh-frame import path
  now exist. `smplx-surface mesh` writes a `neodojo.smplx_mesh_surface.v1`
  visual layer from a local `neodojo.smplx_mesh_frames.v1` JSON while keeping
  official SMPL-X body-model assets local and uncommitted.
- Deterministic SMPL-X opening-form routine review, producing
  `neodojo.annotation.v1` manifests plus `neodojo.routine_feedback_report.v1`
  reports with opening stance, settled support, and raised-hands apex anchors.
- Local G1 SVG/HTML render evidence generated under `outputs/g1-render/`,
  proving the render manifest, front/side/top frame evidence, and G1
  non-scoring boundary. Fixture descriptors require explicit
  `--allow-fixture-model`.
- Optional MuJoCo offscreen render evidence generated by `render mujoco-g1`
  when the `mujoco` package and local registered URDF/MJCF assets are available.
  The built-in optional smoke verifies the path with a tiny MJCF model; real
  Unitree G1 asset-load proof has also been verified locally with an untracked
  clone of `unitreerobotics/unitree_mujoco` `g1_29dof.xml`. Imported GMR
  `unitree_g1_joint_angles` streams are now applied to matching MuJoCo
  hinge/slide `qpos` joints for the selected render frame, with manifest
  evidence for applied, missing, skipped, and clipped joints.
- Hardened artifact manifests now carry schema ids, shared timing,
  coordinate/floor/contact metadata, source-media provenance, optional
  reference-video sync metadata, and normalized annotation manifests.
- Fixture-only public-demo export generated under `outputs/public-demo/`,
  containing a scene/timeline contract, static HTML viewer, SVG screenshot, and
  a default `.rrd`-named JSON fallback artifact.
- Optional true Rerun SDK `.rrd` export is available through
  `demo export-rerun --use-rerun-sdk` when the optional `rerun` extra is
  installed. The fixture-only GitHub Pages public demo is verified at
  `https://miaodx.com/neodojo/`.
- Optional first Viser local runtime is available through `demo serve-viser`
  when the optional `viser` extra is installed. It loads the shared
  scene/timeline contract, shows synchronized SMPL-X and G1 3D tracks,
  trajectory overlays, camera preset controls, annotation-anchor navigation, a
  frame slider, frame-step controls, layer visibility toggles, feedback
  drilldown, playback-speed metadata, and explicit scoring-source labels. The
  contract path also writes generated front/side/top SVG preview screenshots
  for visual smoke evidence without requiring the optional Viser package.
- `make demo-public` regenerates the fixture motion, routine feedback
  annotations, SMPL-X surface proxy, G1 visual/render, teaching-playback,
  public-demo, Viser runtime preview, generated capture bundle, and smoke-check
  artifacts in one command.
- `make demo-public-browser` runs the fixture public-demo lane, renders the
  generated public-demo HTML through headless Chromium with the optional
  Playwright browser extra, writes `outputs/browser-capture/manifest.json` and
  `outputs/browser-capture/public-demo-browser.png`, and refreshes the capture
  bundle with that browser evidence.
- `make gpu-handoff SOURCE_MATERIALIZATION=...` writes
  `outputs/gvhmr-gpu-handoff/manifest.json`, a README, and
  `source-materialization.json`, `gvhmr-smplx-joints.template.json`, and
  `export_neodojo_gvhmr.py` plus `run_gvhmr_neodojo.sh` for an external GVHMR
  run. The manifest preserves source-materialization hash, trim, input-video
  checksum, expected `neodojo.gvhmr_smplx_joints.v1` export path, a GPU-side
  export command, the executable GPU runner command, and the local return
  command. The exporter helper uses bundle-local filenames and is intended to
  run after GVHMR in the GPU environment with `torch`, `smplx`, and licensed
  local SMPL-X assets. It does not copy source media or run GVHMR locally.
- `make gpu-input-bundle-smoke` writes a metadata-only
  `outputs/gvhmr-gpu-input-smoke/` bundle and checks `run_gvhmr_neodojo.sh`
  with `bash -n`. It is included in `make verify` and does not copy media or
  run GVHMR.
- `make gpu-input-archive-smoke` writes a metadata-only
  `outputs/gvhmr-gpu-input-archive-smoke/neodojo-gvhmr-gpu-input.tar.gz` plus
  `neodojo.gvhmr_gpu_input_archive.v1` manifest and lists the archive members.
  It is included in `make verify` and does not copy media or run GVHMR.
- `make gvhmr-run-request` writes a concise
  `neodojo.gvhmr_gpu_run_request.v1` operator request manifest plus README from
  an existing GPU input archive. `make gvhmr-run-request-smoke` covers the
  metadata-only request path in `make verify`; media-including requests remain
  ignored and must not be committed or published.
- `make gvhmr-inspect GVHMR_RESULT=...` writes
  `outputs/gvhmr-result-inspection/manifest.json`, a
  `neodojo.gvhmr_result_inspection.v1` manifest that reports result keys,
  candidate `smpl_params_global` / `smpl_params_incam` blocks, candidate joint
  tensors, and whether the input is already a
  `neodojo.gvhmr_smplx_joints.v1` export. Native `.pt` inspection requires
  `torch` in the GVHMR/GPU environment; the default local path can inspect JSON
  summaries/exports only.
- `make demo-real SOURCE_MATERIALIZATION=... GVHMR_JSON=...` validates an
  externally produced GVHMR SMPL-X teaching-joints JSON against the
  source-materialization manifest, imports it into the motion-record contract,
  and regenerates annotations, the SMPL-X surface proxy, G1 visual/render,
  teaching playback, public-demo, Viser preview, and capture-bundle artifacts
  under `outputs/real-demo/`. It derives a fixture G1 visual companion unless
  an external G1 track and model descriptor are supplied with `G1_TRACK=...`
  and `MODEL_DESCRIPTOR=...`. It does not run GVHMR locally.
- `capture recorder` writes `outputs/recorder-capture/manifest.json`, a
  `neodojo.recorder_capture.v1` manifest that validates optional MuJoCo
  offscreen front/side/top render frames from `render mujoco-g1` as direct
  simulator-recorder evidence.
- `capture bundle` writes `outputs/capture/manifest.json`, a generated
  roboharness-style multi-camera evidence manifest that validates public-demo
  artifacts, Viser front/side/top preview screenshots, and G1 front/side/top
  render frames. With `--browser-capture`, it also validates the optional
  browser-rendered public-demo screenshot. With `--recorder-capture`, it also
  validates optional direct MuJoCo simulator-recorder evidence. This is not a
  direct roboharness integration or video artifact.
- `make check` validates MVP plan links and minimum plan scaffolding, and is
  included in `make verify` and the GitHub Actions workflow.
- `.github/workflows/public-demo.yml` runs tests, builds a wheel, runs the
  dry-run real-conversion handoff smoke, installs the optional Playwright
  browser runtime, builds the fixture public demo with browser capture, uploads
  the metadata-only real-handoff smoke artifact, metadata-only GPU input bundle
  smoke artifact, metadata-only GPU input archive smoke artifact, metadata-only
  GPU run-request smoke artifact, metadata-only Colab operator notebook smoke
  artifact, metadata-only GVHMR operator package smoke artifact,
  metadata-only GVHMR operator package archive smoke artifact, metadata-only
  GPU execution probe artifact, fixture-only real-artifact intake smoke
  artifact, default real-conversion audit artifact, opt-in GitHub-route
  real-conversion audit artifact, standalone public-demo artifact,
  browser-capture artifact, and capture-bundle artifact containing the capture
  manifest and referenced generated evidence, and publishes the static
  public-demo output to GitHub Pages from `main` when the repository variable
  `NEODOJO_DEPLOY_PAGES=true` is set.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/25999641059` verified the
  default CI lane on `main`, uploaded the `neodojo-public-demo` and
  `neodojo-capture-bundle` artifacts, produced a CI-generated `index.html` that
  passes `neodojo demo smoke`, produced a capture-bundle artifact whose
  manifest references resolve inside the downloaded bundle, and deployed the
  fixture-only Pages URL `https://miaodx.com/neodojo/`.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26000413142` verified the
  browser-capture CI lane on `main`: Chromium installed, `make
  demo-public-browser` passed, the `neodojo-browser-capture` artifact contained
  a 1280x720 PNG and `neodojo.browser_capture.v1` manifest, the downloaded
  capture bundle recorded `real_browser_capture: true`, and Pages deployed.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26001914760` verified the
  fixture public-demo lane on `main` after the real-conversion import-demo
  wrapper: lint, plan checks, tests, wheel build, browser capture, artifact
  upload, and Pages deploy passed. The downloaded public-demo artifact passes
  `neodojo demo smoke`, the browser-capture artifact contains a 1280x720 PNG,
  and the capture-bundle artifact records `real_browser_capture: true`,
  `public_demo_smoke_checked: true`, and 11 nonblank generated evidence
  artifacts.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26003369563` verified the
  metadata-only real-handoff smoke artifact on `main`: lint, plan checks, tests,
  wheel build, `make real-handoff-smoke`, handoff artifact upload, browser
  capture, capture-bundle upload, Pages artifact upload, and Pages deploy
  passed. The downloaded `neodojo-real-handoff-smoke` artifact contains the
  prep manifest, source-materialization manifest, GPU handoff manifest, README,
  source-materialization copy, GVHMR export template, and GPU-side exporter
  helper, and contains no video files.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26004331422` verified the
  executable GPU-runner packaging on `main`: lint, plan checks, tests, wheel
  build, `make real-handoff-smoke`, `make gpu-input-bundle-smoke`, handoff
  artifact upload, metadata-only GPU input bundle artifact upload, browser
  capture, capture-bundle upload, Pages artifact upload, and Pages deploy
  passed. The `neodojo-gpu-input-bundle-smoke` artifact contains the GPU input
  manifest, `RUN_ON_GPU.md`, handoff metadata, source-materialization copy,
  GVHMR export template, GPU-side exporter helper, and
  `run_gvhmr_neodojo.sh`, and contains no video files.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26004620869` verified the
  GPU input archive surface on `main`: lint, plan checks, tests, wheel build,
  `make real-handoff-smoke`, `make gpu-input-bundle-smoke`, `make
  gpu-input-archive-smoke`, artifact upload, browser capture, capture-bundle
  upload, Pages artifact upload, and Pages deploy passed. The downloaded
  `neodojo-gpu-input-archive-smoke` artifact contains
  `neodojo-gvhmr-gpu-input.tar.gz` plus a
  `neodojo.gvhmr_gpu_input_archive.v1` manifest with `media_included: false`
  and `safe_for_git: true`; archive members are metadata/scripts only and no
  `.mp4`, `.pt`, `.pkl`, or `.npz` files are present.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26005182190` verified the
  current `main` public-demo lane after the one-command GPU archive target
  landed: lint, plan checks, tests, wheel build, real-handoff smoke, GPU input
  bundle smoke, GPU input archive smoke, browser capture, public-demo artifact
  upload, capture-bundle upload, Pages artifact upload, and Pages deploy
  passed. The downloaded `neodojo-public-demo` artifact contains `index.html`,
  `scene.json`, `manifest.json`, `screenshot.svg`, and
  `neodojo-demo.rrd`; the live Pages manifest remains fixture-only and carries
  the expected SMPL-X teacher, Unitree G1 visual, routine feedback, and SMPL-X
  surface proxy labels.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26005618093` verified the
  GPU execution probe artifact on `main`: lint, plan checks, tests, wheel
  build, real-handoff smoke, GPU input bundle smoke, GPU input archive smoke,
  `make gpu-execution-probe`, probe artifact upload, browser capture,
  public-demo artifact upload, capture-bundle upload, Pages artifact upload,
  and Pages deploy passed. The downloaded `neodojo-gpu-execution-probe`
  artifact contains `neodojo.gvhmr_gpu_execution_probe.v1`, reports
  `external_gpu_artifact_missing`, `safe_for_git: true`,
  `secret_values_recorded: false`, no local CUDA, no Docker GPU runtime, and no
  configured provider candidates.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26006210299` verified the
  real-artifact intake smoke lane on `main`: lint, plan checks, tests, wheel
  build, real-handoff smoke, GPU input bundle smoke, GPU input archive smoke,
  GPU execution probe, `make real-artifact-intake-smoke`, smoke artifact
  upload, browser capture, public-demo artifact upload, capture-bundle upload,
  Pages artifact upload, and Pages deploy passed. The downloaded
  `neodojo-real-artifact-intake-smoke` artifact contains fixture-only
  source-materialization and GVHMR JSON inputs plus real-demo, validation,
  public-demo, and capture manifests. The source validation report passed with
  36 frames at 24 fps, 1.5 seconds of motion, matching source provenance. The
  real-demo manifest records `gvhmr_artifact_imported: true`,
  `real_gvhmr_artifact_imported: false`, and both source/export fixture flags
  as true, and the artifact includes no `.mp4`, `.pt`, `.pkl`, or `.npz` files.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26006485103` verified the
  real-conversion completion audit artifact on `main`: `make
  real-conversion-audit` passed, the `neodojo-real-conversion-audit` artifact
  contains only the audit manifest and nested GPU execution probe manifest, and
  the audit records `status: external_gpu_artifact_missing`, `complete: false`,
  `blocked: true`, and the next action to run GVHMR on a GPU-capable machine.
  The nested probe remains `safe_for_git: true` with `secret_values_recorded:
  false`, and no `.mp4`, `.pt`, `.pkl`, or `.npz` files are present.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26006738133` verified the
  strict real-completion gate change on `main`: the default fixture CI lane
  still passed and deployed, the downloaded `neodojo-public-demo` artifact
  contains `neodojo.public_demo.v1`, `fixture_only: true`, `index.html`,
  `screenshot.svg`, and the expected SMPL-X/G1/fixture labels, while the
  downloaded `neodojo-real-conversion-audit` artifact remains
  `external_gpu_artifact_missing`, `complete: false`, `blocked: true`, with a
  safe nested GPU probe and no secret values.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26007158313` verified the
  self-hosted GVHMR return-artifact intake changes on `main`: the default
  fixture CI lane still passed and deployed, the downloaded public-demo
  artifact remains `neodojo.public_demo.v1` with `fixture_only: true` and the
  expected SMPL-X/G1/fixture labels, and the downloaded real-conversion audit
  artifact still reports `external_gpu_artifact_missing`, `complete: false`,
  `blocked: true`, with a safe nested GPU probe and no secret values.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26007531255` verified the
  guarded real-demo Pages promotion changes on `main`: the default fixture CI
  lane still passed and deployed, the downloaded public-demo artifact passes
  `neodojo demo smoke` and remains `neodojo.public_demo.v1` with
  `fixture_only: true`, while the downloaded real-conversion audit artifact
  still reports `external_gpu_artifact_missing`, `complete: false`, and
  `blocked: true`.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26008421430` verified the
  generated GPU run-request smoke surface on `main`: lint, plan checks, tests,
  wheel build, real-handoff smoke, GPU input bundle smoke, `make
  gvhmr-run-request-smoke`, GPU input archive artifact upload, GPU run-request
  artifact upload, GPU execution probe, real-artifact intake smoke,
  real-conversion audit, browser capture, public-demo artifact upload,
  capture-bundle upload, Pages artifact upload, and Pages deploy passed. The
  downloaded `neodojo-gpu-run-request-smoke` artifact contains
  `neodojo.gvhmr_gpu_run_request.v1`, `media_included: false`,
  `safe_for_git: true`, and expected return schema
  `neodojo.gvhmr_smplx_joints.v1`; the downloaded public-demo artifact passes
  `neodojo demo smoke` and the audit still reports
  `external_gpu_artifact_missing`, `complete: false`, `blocked: true`.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26009044473` verified the
  generated Colab operator notebook handoff on `main`: lint, plan checks,
  tests, wheel build, real-handoff smoke, GPU input bundle smoke, GPU input
  archive/run-request smoke, Colab notebook smoke, GPU execution probe,
  real-artifact intake smoke, real-conversion audit, browser capture,
  public-demo artifact upload, capture-bundle upload, Pages artifact upload,
  and Pages deploy passed. The downloaded
  `neodojo-gvhmr-colab-operator-smoke` artifact contains
  `neodojo.gvhmr_colab_operator_notebook.v1`,
  `status: metadata_only_not_ready_for_gpu`, `media_included: false`,
  `safe_for_git: true`, a notebook with archive checksum verification,
  guarded `RUN_GVHMR = False` execution, safe archive-member path validation,
  and local `make real-artifact-intake` / `make verify-real` return commands.
  The downloaded public-demo artifact and live Pages manifest still report
  `neodojo.public_demo.v1`, `fixture_only: true`, `scoring_source: smplx`, and
  the expected SMPL-X teacher / Unitree G1 visual labels; the audit still
  reports `external_gpu_artifact_missing`, `complete: false`, `blocked: true`.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26009913491` verified the
  collocated GVHMR operator package handoff on `main`: lint, plan checks,
  tests, wheel build, real-handoff smoke, GPU input bundle smoke, GPU input
  archive/run-request smoke, Colab notebook smoke, operator package smoke, GPU
  execution probe, real-artifact intake smoke, real-conversion audit, browser
  capture, public-demo artifact upload, capture-bundle upload, Pages artifact
  upload, and Pages deploy passed. The downloaded
  `neodojo-gvhmr-operator-package-smoke` artifact contains
  `neodojo.gvhmr_operator_package.v1`, `status:
  metadata_only_not_ready_for_gpu`, `media_included: false`, `safe_for_git:
  true`, copied archive/request/notebook files, a package README, and no source
  media in the package archive. The downloaded public-demo artifact passed
  `neodojo demo smoke`; the live Pages manifest still reports
  `neodojo.public_demo.v1`, `fixture_only: true`, and `scoring_source: smplx`;
  the audit still reports `external_gpu_artifact_missing`, `complete: false`,
  `blocked: true`.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26010670374` verified the
  self-hosted GPU workflow package-validation hardening on `main`: lint, plan
  checks, tests, wheel build, real-handoff smoke, GPU input bundle smoke, GPU
  input archive/run-request smoke, Colab notebook smoke, operator package
  smoke, GPU execution probe, real-artifact intake smoke, real-conversion
  audit, browser capture, public-demo artifact upload, capture-bundle upload,
  Pages artifact upload, and Pages deploy passed. The workflow package-input
  path now validates operator-package, run-request, and Colab-notebook schemas
  plus archive/request/notebook checksum links before unpacking; the downloaded
  public-demo artifact and live Pages manifest still report
  `neodojo.public_demo.v1`, `fixture_only: true`, and `scoring_source: smplx`,
  while the audit remains `external_gpu_artifact_missing`, `complete: false`,
  and `blocked: true`.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26011378922` verified copied
  operator-package validation during package creation on `main`: lint, plan
  checks, tests, wheel build, real-handoff smoke, GPU input bundle smoke, GPU
  input archive/run-request smoke, Colab notebook smoke, operator package
  smoke plus validation, GPU execution probe, real-artifact intake smoke,
  real-conversion audit, browser capture, public-demo artifact upload,
  capture-bundle upload, Pages artifact upload, and Pages deploy passed. The
  downloaded `neodojo-public-demo` artifact passed `neodojo demo smoke` and
  contains non-empty `index.html`, `screenshot.svg`, and
  `neodojo-demo.rrd` files with `neodojo.public_demo.v1`, `fixture_only:
  true`, `scoring_source: smplx`, SMPL-X teacher scoring enabled, and Unitree
  G1 scoring disabled. A local validation of the ignored media-containing
  `outputs/gvhmr-operator-package/` handoff reports
  `ready_for_external_gpu_operator_package`. The strict local completion gate
  still reports `external_gpu_artifact_missing`, `complete: false`, and
  `blocked: true`.
- GitHub Actions run
  `https://github.com/MiaoDX/neodojo/actions/runs/26012215777` verified the
  opt-in GitHub-route real-conversion audit artifact on `main`: lint, plan
  checks, tests, wheel build, real/GPU smoke artifacts, default audit,
  GitHub-route audit, browser capture, public-demo artifact upload,
  capture-bundle upload, Pages artifact upload, and Pages deploy passed. The
  downloaded `neodojo-real-conversion-audit-github` artifact still reports
  `external_gpu_artifact_missing`, `complete: false`, no secret names, and no
  secret values. The nested GitHub probe records safe 403 API errors when the
  CI integration token cannot read runner/secret-count endpoints instead of
  inventing counts. The downloaded `neodojo-public-demo` artifact remains
  fixture-only with SMPL-X scoring.
- Fixture-only teaching playback HTML generated under `outputs/teaching-demo/`,
  proving that the SMPL-X and G1 manifests can be consumed together while
  preserving the SMPL-X scoring boundary.
- The local non-GPU G1 render evidence slice in
  `docs/plans/mvp-g1-real-model-rendering.md` has landed as an SVG/HTML
  descriptor/track render path. Optional MuJoCo mesh rendering now has a
  tiny-MJCF smoke, a real local Unitree G1 asset-load smoke, and a real local
  GMR joint-angle-to-qpos smoke against matching Unitree G1 joint names.
- Real-conversion source prep manifest generated under
  `outputs/real-conversion-gate/`, selecting source `03-006` metadata and a
  short trim window for a later GPU run. When `--local-video` is supplied, the
  source-media contract records checksum and optional ffprobe metadata.
- Source materialization handoff generated under
  `outputs/real-conversion-source/` when a local video is supplied, writing
  dry-run ffmpeg commands or ignored trimmed clip/reference-frame artifacts for
  the later GPU run.
- `make real-handoff` smoke generated
  `outputs/real-handoff-smoke/prep/real-conversion-prep.json`,
  `outputs/real-handoff-smoke/source-materialized/source-materialization.json`,
  and `outputs/real-handoff-smoke/gpu-handoff/manifest.json` from an ignored
  local `.mp4` placeholder. The smoke used default dry-run materialization, so
  the GPU handoff correctly reports `needs_materialization` while still writing
  the copyable exporter bundle metadata. CI uploads the metadata-only handoff
  smoke files as `neodojo-real-handoff-smoke` without including the placeholder
  `.mp4`.
- `make real-gpu-archive LOCAL_VIDEO=...` has been smoke-tested against an
  ignored local Bilibili candidate. The command wrote
  `outputs/real-gpu-archive-command-smoke/gpu-input-archive/manifest.json`
  with `status: archive_with_media`, `media_included: true`, and
  `safe_for_git: false`; the archive members include `RUN_ON_GPU.md`,
  `run_gvhmr_neodojo.sh`, `export_neodojo_gvhmr.py`,
  `gvhmr-smplx-joints.template.json`, `source-materialization.json`, and
  `source/trimmed-clip.mp4`.
- `make real-gpu-run-request LOCAL_VIDEO=...` has been smoke-tested against the
  ignored local Bilibili candidate with a 2-second trim. The command wrote the
  same media-containing archive shape plus
  `outputs/real-gpu-run-request-smoke/run-request/manifest.json`, which reports
  `schema: neodojo.gvhmr_gpu_run_request.v1`,
  `status: ready_for_external_gpu`, `media_included: true`,
  `safe_for_git: false`, and expected return schema
  `neodojo.gvhmr_smplx_joints.v1`.
- `make real-gpu-colab-notebook LOCAL_VIDEO=...` chains the same media
  materialization, transfer archive, generated run request, and Colab operator
  notebook. It has been smoke-tested against the ignored local Bilibili
  candidate with a 2-second trim and wrote
  `outputs/real-gpu-colab-command-smoke/colab-operator/manifest.json` with
  `schema: neodojo.gvhmr_colab_operator_notebook.v1`,
  `status: ready_for_colab_operator`, `media_included: true`, and
  `safe_for_git: false`.
- `make real-gpu-operator-package LOCAL_VIDEO=...` chains the media
  materialization, transfer archive, generated run request, Colab operator
  notebook, and collocated operator package. The lower-level
  `make gvhmr-operator-package-smoke` is included in `make verify` and writes
  `outputs/gvhmr-operator-package-smoke/manifest.json` with
  `schema: neodojo.gvhmr_operator_package.v1`,
  `status: metadata_only_not_ready_for_gpu`, `media_included: false`, and
  `safe_for_git: true`. The default ignored local Bilibili proof package at
  `outputs/gvhmr-operator-package/manifest.json` reports
  `status: ready_for_external_gpu_operator_package`, `media_included: true`,
  and `safe_for_git: false`; media-containing operator packages remain ignored.
- `make gvhmr-colab-notebook GVHMR_RUN_REQUEST=...` has been smoke-tested for
  both metadata-only CI handoffs and the ignored media-containing local
  run-request. The media-containing path wrote
  `outputs/real-gpu-run-request-smoke/colab-operator/manifest.json`, which
  reports `schema: neodojo.gvhmr_colab_operator_notebook.v1`,
  `status: ready_for_colab_operator`, `media_included: true`, and
  `safe_for_git: false`; the notebook includes the archive checksum, guarded
  `RUN_GVHMR = False` execution, returned JSON download, and local validation
  commands.
- The ignored local Bilibili proof-clip request
  `outputs/gvhmr-gpu-run-request-local-bilibili/manifest.json` can now be handed
  to the same notebook path. A local generation wrote
  `outputs/gvhmr-colab-operator-local-bilibili/manifest.json` with
  `schema: neodojo.gvhmr_colab_operator_notebook.v1`,
  `status: ready_for_colab_operator`, `media_included: true`, and
  `safe_for_git: false`, leaving only private GPU execution and returned-export
  validation.
- `make gpu-execution-probe` writes
  `outputs/gvhmr-gpu-execution-probe/manifest.json` and is included in
  `make verify`. On the current macOS ARM workspace it reports
  `external_gpu_artifact_missing`, with no local CUDA runtime, no Docker GPU
  runtime, and no configured GPU provider candidate detected.
- GVHMR GPU handoff package generated under `outputs/gvhmr-gpu-handoff-smoke/`
  in local smoke, writing `neodojo.gvhmr_gpu_handoff.v1` manifest metadata,
  README instructions, a copyable `source-materialization.json`,
  `neodojo.gvhmr_smplx_joints.v1` export template, and the standalone
  `export_neodojo_gvhmr.py` GPU-side exporter helper plus
  `run_gvhmr_neodojo.sh`. The smoke used dry-run source materialization, so the
  handoff correctly reports
  `needs_materialization` until a real trimmed clip exists.
- A tracked external-GPU operator runbook now lives at
  `docs/runbooks/gvhmr-external-gpu.md`. It records the archive transfer,
  upstream GVHMR setup shape, packaged `run_gvhmr_neodojo.sh` invocation,
  returned-export validation command, and failure-classification loop without
  committing media, checkpoints, SMPL-X assets, or returned motion artifacts.
- GVHMR result inspection smoke generated
  `outputs/gvhmr-result-inspection-smoke/manifest.json` from the existing local
  fixture export and reported `already_neodojo_export`. Unit tests also cover a
  synthetic `smpl_params_global` summary and the no-`torch` `.pt` error path.
- Source validation report generated under `outputs/real-conversion-validation/`
  for GVHMR teaching-joints JSON exports that declare matching materialization
  provenance. Passing validation writes a `.validated.json` import copy and
  preserves source-validation status in the motion-record provenance.
- `make demo-real` has been smoke-tested with generated ignored source
  materialization and GVHMR JSON fixtures; it wrote `outputs/real-demo-smoke/`
  with a validated source report, imported motion-record manifest, public-demo
  artifact, Viser preview, and capture bundle. This is still a local handoff
  proof, not a real GVHMR execution proof.
- `make real-artifact-intake REAL_ARTIFACT_GVHMR_JSON=...` wraps the same
  validated import-demo path with standard default paths for the returned export
  workflow. It has been smoke-tested against fixture-backed real-demo inputs and
  wrote `outputs/real-artifact-intake-smoke/`.
- `make real-artifact-intake-smoke` generates fixture-only source
  materialization and GVHMR JSON inputs, then runs the same
  `make real-artifact-intake` wrapper. It is included in `make verify` and is
  intended to keep the returned-artifact intake surface covered without
  claiming a real GVHMR artifact exists. Its real-demo manifest records
  `gvhmr_artifact_imported: true` and `real_gvhmr_artifact_imported: false`
  for fixture smoke, plus explicit source/export fixture flags.
- `make real-conversion-audit` writes
  `outputs/real-conversion-audit/manifest.json`, a non-failing audit manifest
  that classifies the real-conversion gate as complete or blocked. In the
  current local state it reports `external_gpu_artifact_missing`, `complete:
  false`, and the next action to run GVHMR externally and return a
  `neodojo.gvhmr_smplx_joints.v1` export. With
  `REAL_AUDIT_GITHUB_REPO=OWNER/REPO`, it includes the opt-in GitHub
  self-hosted runner and repository secret-count probe in the nested GPU
  execution manifest without recording secret values or secret names.
- `make real-conversion-audit-strict` and `make verify-real` run the same
  audit with `--require-complete`, so they intentionally fail until a real
  non-fixture GVHMR demo has been imported and regenerated.
- `.github/workflows/gvhmr-self-hosted-gpu.yml` is a manual
  `workflow_dispatch` path for user-managed runners labeled `self-hosted` and
  `gpu`. It can run the packaged GVHMR wrapper from a runner-local archive or
  collocated operator package. For package inputs it validates schemas and
  archive/request/notebook checksums before unpacking. It then validates/imports
  the returned export with `make real-artifact-intake`, runs the strict
  real-conversion audit, and optionally uploads only
  `gvhmr-smplx-joints.json` or generated real-demo/public-demo evidence; it is
  not part of default push/PR CI and does not upload media, checkpoints, SMPL-X
  assets, or `.pt` result files.
- `.github/workflows/promote-real-demo-pages.yml` is a separate manual
  `workflow_dispatch` path for replacing the fixture-only Pages artifact only
  after a self-hosted run has uploaded `neodojo-self-hosted-real-demo`. It
  requires `confirm_replace_fixture_pages=true` and repository variable
  `NEODOJO_DEPLOY_REAL_PAGES=true`, revalidates the real-demo manifest, strict
  audit manifest, public-demo files, SMPL-X scoring boundary, and
  `neodojo demo smoke`, and deploys only the generated public-demo directory
  plus a promotion manifest. It does not run GVHMR and is not triggered by
  push or pull request events.
- `make real-demo-pages-promotion-validate` and
  `neodojo real-conversion validate-pages-promotion` expose that promotion
  validator as a local command, so fixture-only imports, incomplete strict
  audits, unsafe file paths, non-SMPL-X scoring, and blank public-demo files can
  be rejected in unit tests before a manual Pages promotion run exists.

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
make demo-public-browser
make real-gpu-archive LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin
make real-gpu-run-request LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin
make real-gpu-colab-notebook LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin
make real-gpu-operator-package LOCAL_VIDEO=path/to/local-source.mp4 REAL_LOCAL_SOURCE_ID=local-baduanjin
make real-handoff LOCAL_VIDEO=path/to/local-source.mp4
make real-handoff-smoke
make gpu-handoff SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json
make gpu-input-bundle GPU_HANDOFF=outputs/gvhmr-gpu-handoff GPU_INPUT_INCLUDE_MEDIA=1
make gpu-input-bundle-smoke
make gpu-input-archive GPU_INPUT=outputs/gvhmr-gpu-input
make gpu-input-archive-smoke
make gpu-execution-probe
make gvhmr-run-request GPU_INPUT_ARCHIVE=outputs/gvhmr-gpu-input-archive
make gvhmr-run-request-smoke
make gvhmr-colab-notebook GVHMR_RUN_REQUEST=outputs/gvhmr-gpu-run-request
make gvhmr-colab-notebook-smoke
make gvhmr-operator-package GPU_INPUT_ARCHIVE=outputs/gvhmr-gpu-input-archive GVHMR_RUN_REQUEST=outputs/gvhmr-gpu-run-request GVHMR_COLAB_NOTEBOOK=outputs/gvhmr-colab-operator
make gvhmr-operator-package-smoke
make gvhmr-operator-package-validate GVHMR_OPERATOR_PACKAGE=outputs/gvhmr-operator-package
make gvhmr-inspect GVHMR_RESULT=outputs/real-conversion-gate/hmr4d_results.pt
make real-artifact-intake REAL_ARTIFACT_GVHMR_JSON=path/to/gvhmr-smplx-joints.json
make real-artifact-intake-smoke
make real-conversion-audit
make demo-real SOURCE_MATERIALIZATION=outputs/real-conversion-source/source-materialization.json GVHMR_JSON=outputs/real-conversion-gate/gvhmr-smplx-joints.json
make smoke-public
PYTHONPATH=src python -m neodojo motion-record create --out outputs/motion-contract
PYTHONPATH=src python -m neodojo motion-record create --from-gvhmr-json path/to/gvhmr-smplx-joints.json --out outputs/motion-contract
PYTHONPATH=src python -m neodojo smplx-surface proxy --motion-record outputs/motion-contract --out outputs/smplx-surface
PYTHONPATH=src python -m neodojo smplx-surface register-assets --model path/to/SMPLX_NEUTRAL.npz --license "local licensed SMPL-X asset; do not commit" --out outputs/smplx-assets
PYTHONPATH=src python -m neodojo smplx-surface mesh --motion-record outputs/motion-contract --asset-descriptor outputs/smplx-assets/assets/smplx/manifest.json --mesh-frames path/to/smplx-mesh-frames.json --out outputs/smplx-mesh
PYTHONPATH=src python -m neodojo annotations detect --motion-record outputs/motion-contract --out outputs/annotations
PYTHONPATH=src python -m neodojo robot-model register --robot unitree_g1 --fixture --out outputs/g1-visual
PYTHONPATH=src python -m neodojo tracks build --motion-record outputs/motion-contract --robot unitree_g1 --model-descriptor outputs/g1-visual/robot-models/unitree_g1/manifest.json --out outputs/g1-visual
PYTHONPATH=src python -m neodojo tracks normalize-gmr-pkl --source path/to/gmr-motion.pkl --motion-record outputs/motion-contract --out outputs/gmr-native
PYTHONPATH=src python -m neodojo tracks import-gmr-json --source path/to/gmr-unitree-g1.json --motion-record outputs/motion-contract --out outputs/g1-visual
PYTHONPATH=src python -m neodojo render g1 --model-descriptor outputs/g1-visual/robot-models/unitree_g1/manifest.json --g1-track outputs/g1-visual/tracks/g1/manifest.json --allow-fixture-model --out outputs/g1-render
PYTHONPATH=src python -m neodojo render mujoco-g1 --model-descriptor path/to/registered-g1-model/manifest.json --g1-track outputs/g1-visual/tracks/g1/manifest.json --out outputs/g1-mujoco-render
PYTHONPATH=src python -m neodojo demo play --motion-record outputs/motion-contract --g1-track outputs/g1-visual/tracks/g1/manifest.json --smplx-surface outputs/smplx-surface/surfaces/smplx/manifest.json --out outputs/teaching-demo
PYTHONPATH=src python -m neodojo demo export-rerun --playback outputs/teaching-demo/manifest.json --g1-render outputs/g1-render/manifest.json --out outputs/public-demo/neodojo-demo.rrd
PYTHONPATH=src python -m neodojo demo export-rerun --playback outputs/teaching-demo/manifest.json --g1-render outputs/g1-render/manifest.json --use-rerun-sdk --out outputs/public-demo/neodojo-demo.rrd
PYTHONPATH=src python -m neodojo demo serve-viser --playback outputs/teaching-demo/manifest.json --g1-render outputs/g1-render/manifest.json --out outputs/viser-runtime
PYTHONPATH=src python -m neodojo demo browser-smoke --public-demo outputs/public-demo --out outputs/browser-capture
PYTHONPATH=src python -m neodojo capture recorder --simulator-render outputs/g1-mujoco-render --out outputs/recorder-capture
PYTHONPATH=src python -m neodojo capture bundle --public-demo outputs/public-demo --viser-runtime outputs/viser-runtime --g1-render outputs/g1-render --out outputs/capture
PYTHONPATH=src python -m neodojo capture bundle --public-demo outputs/public-demo --viser-runtime outputs/viser-runtime --g1-render outputs/g1-render --browser-capture outputs/browser-capture --out outputs/capture
PYTHONPATH=src python -m neodojo capture bundle --public-demo outputs/public-demo --viser-runtime outputs/viser-runtime --g1-render outputs/g1-render --recorder-capture outputs/recorder-capture --out outputs/capture
PYTHONPATH=src python -m neodojo real-conversion prepare --id 03-006 --start 0 --end 12 --out outputs/real-conversion-gate
PYTHONPATH=src python -m neodojo real-conversion prepare --local-source-id local-baduanjin --local-video path/to/local-source.mp4 --local-title "Local Baduanjin proof clip" --start 0 --end 12 --out outputs/real-conversion-gate
PYTHONPATH=src python -m neodojo real-conversion materialize-source --prep outputs/real-conversion-gate/real-conversion-prep.json --local-video path/to/local-source.mp4 --dry-run --out outputs/real-conversion-source
PYTHONPATH=src python -m neodojo real-conversion package-gpu-handoff --source-materialization outputs/real-conversion-source/source-materialization.json --out outputs/gvhmr-gpu-handoff
PYTHONPATH=src python -m neodojo real-conversion package-gpu-input --gpu-handoff outputs/gvhmr-gpu-handoff --include-media --out outputs/gvhmr-gpu-input
PYTHONPATH=src python -m neodojo real-conversion archive-gpu-input --gpu-input outputs/gvhmr-gpu-input --out outputs/gvhmr-gpu-input-archive
PYTHONPATH=src python -m neodojo real-conversion probe-gpu-execution --out outputs/gvhmr-gpu-execution-probe
PYTHONPATH=src python -m neodojo real-conversion write-gpu-run-request --gpu-input-archive outputs/gvhmr-gpu-input-archive --out outputs/gvhmr-gpu-run-request
PYTHONPATH=src python -m neodojo real-conversion inspect-gvhmr-result --source outputs/real-conversion-gate/hmr4d_results.pt --out outputs/gvhmr-result-inspection
PYTHONPATH=src python -m neodojo real-conversion validate-source --source-materialization outputs/real-conversion-source/source-materialization.json --gvhmr-json outputs/real-conversion-gate/gvhmr-smplx-joints.json --out outputs/real-conversion-validation
PYTHONPATH=src python -m neodojo real-conversion import-demo --source-materialization outputs/real-conversion-source/source-materialization.json --gvhmr-json outputs/real-conversion-gate/gvhmr-smplx-joints.json --out outputs/real-demo
make demo-html
```

`make verify` runs lint, MVP plan quality checks, tests, wheel build, the
public-demo plus capture-bundle smoke lane, the dry-run real-handoff smoke
lane, metadata-only GPU input bundle/archive smoke lanes, GPU execution probe,
metadata-only GPU run-request smoke, fixture-only real-artifact intake smoke
lane, and real-conversion completion audit.
`make lint` runs a minimal syntax/import bytecode compile check over `src/` and
`tests/`. `make check` validates MVP plan links and minimum plan scaffolding.
`make test` runs the focused Python unit tests for the fixture demo generator
and local motion contract. `make build` builds a wheel under ignored
`outputs/dist/`. `neodojo motion-record create` writes fixture-backed SMPL-X
motion-record and teaching-track manifests under the selected ignored output
directory, or imports an external GVHMR teaching-joints JSON export with
`--from-gvhmr-json`. If the import JSON carries `smplx_parameters`, the motion
record preserves them in `motion-record/smplx-parameters.json` with a
`neodojo.smplx_parameters.v1` metadata summary. `neodojo annotations detect`
writes an explicit
SMPL-X-only annotation manifest plus routine feedback report for opening
stance, settled support, and raised-hands apex anchors, then feeds those anchors
into the public-demo lane. `neodojo smplx-surface proxy` writes a visual-only
SMPL-X capsule surface proxy derived from teaching joints; it does not require
or bundle licensed SMPL-X model assets. `neodojo smplx-surface register-assets`
writes a local-only descriptor for an existing licensed SMPL-X model file
without copying it, and `neodojo smplx-surface mesh` imports a local
`neodojo.smplx_mesh_frames.v1` JSON from an external licensed SMPL-X renderer
into `outputs/smplx-mesh/surfaces/smplx/manifest.json`. The command rejects
joint-only motion records, validates mesh-ready SMPL-X pose/shape parameters,
local asset descriptor presence, vertices, faces, and frame count, and keeps the
mesh layer visual-only rather than a scoring source.
`neodojo robot-model register` and
`neodojo tracks build` write fixture G1 model/visual-track manifests and a
comparison report that keeps G1 non-scoring. `neodojo tracks normalize-gmr-pkl`
parses the native YanjieZe/GMR robot-motion pickle shape written by
`scripts/*_to_robot.py --save_path` and writes a normalized G1 JSON export plus
adapter report. `neodojo tracks import-gmr-json` imports an external
normalized `neodojo.gmr_unitree_g1_track.v1` export with Unitree G1 joint-angle
frames into the same non-scoring G1 track contract; it does not run GMR
locally or claim support for every native upstream GMR output format.
`neodojo render g1`
writes local SVG/HTML front/side/top render evidence and a render manifest from
a G1 model descriptor plus G1 track; fixture model descriptors require explicit
`--allow-fixture-model`, and this is not MuJoCo/Genesis simulator mesh
rendering. `neodojo render mujoco-g1` is an optional MuJoCo offscreen renderer
for registered URDF/MJCF descriptors; install the `sim` extra or `mujoco` and
provide local untracked robot assets before using it for real G1 evidence. If
the G1 track carries imported GMR joint angles, matching MuJoCo hinge/slide
joints are applied to `qpos` and summarized in the render manifest.
`neodojo demo play` writes
`outputs/teaching-demo/index.html` and a playback manifest from the SMPL-X,
optional SMPL-X surface proxy or mesh surface, and G1 manifests. `neodojo demo export-rerun` writes
`outputs/public-demo/index.html`, `outputs/public-demo/scene.json`,
`outputs/public-demo/screenshot.svg`, and `outputs/public-demo/neodojo-demo.rrd`;
by default, the `.rrd` is a JSON fallback artifact, not a real Rerun SDK
recording. Passing `--use-rerun-sdk` with the optional `rerun` extra installed
writes a true Rerun recording. `make demo-public` regenerates the full fixture
public-demo lane, including detected annotations, the SMPL-X surface proxy, and
the Viser runtime preview screenshots and generated capture bundle, then runs
the smoke check. `make smoke-public`
validates an existing `outputs/public-demo` artifact set. `make demo-html`
writes `outputs/html-demo/index.html`, `outputs/html-demo/manifest.json`, and
the local motion/track manifests it consumes. These artifacts use synthetic
fixture motion only; they validate UI plumbing, trajectory drawing, timeline
sync, the local SMPL-X/G1 scoring boundary, the visual-only SMPL-X surface
proxy, and one SMPL-X-based geometry check, not qigong correctness.

`neodojo demo browser-smoke` serves the generated public-demo directory over a
local HTTP server, renders it in headless Chromium through the optional
Playwright browser extra, checks the expected fixture/SMPL-X/G1 labels in the
browser-rendered body, verifies the stage image loaded, and writes
`outputs/browser-capture/manifest.json` plus
`outputs/browser-capture/public-demo-browser.png`. `make demo-public-browser`
runs the full fixture lane, then adds this browser evidence to
`outputs/capture/manifest.json`.

`neodojo capture recorder` consumes an existing optional MuJoCo offscreen render
directory from `neodojo render mujoco-g1`, validates its front/side/top PNG
frames and nonblank checks, and writes a `neodojo.recorder_capture.v1`
manifest under `outputs/recorder-capture/`. This is direct simulator recorder
evidence, not a roboharness integration, and it remains optional because MuJoCo
and registered robot assets are local dependencies.

`neodojo demo serve-viser` writes `outputs/viser-runtime/viser-runtime.json`,
`outputs/viser-runtime/scene.json`, and generated front/side/top SVG previews
under `outputs/viser-runtime/screenshots/`, then starts a local Viser server
when the optional `viser` extra is installed. The first runtime consumes the
same scene/timeline contract as the public-demo lane, converts the current y-up
coordinates into Viser z-up coordinates, and displays synchronized SMPL-X/G1
tracks, trajectory overlays, camera preset buttons, annotation-anchor buttons,
frame stepping, playback-speed metadata, layer visibility toggles, feedback
drilldown, and scoring-source labels. The runtime manifest includes
`neodojo.viser_teaching_ui.v1` review-loop metadata. Use
`--write-contract-only` to write the Viser runtime contract and preview
screenshots without importing Viser, or `--smoke-start` to start, populate, and
stop the server for local verification.

`neodojo capture bundle` consumes an existing public-demo directory, Viser
runtime directory, and G1 render directory, then writes
`outputs/capture/manifest.json` using `neodojo.capture_bundle.v1`. It checks
that public-demo smoke validation passes, Viser front/side/top preview
screenshots are present with expected labels, and G1 front/side/top render
frames are nonblank. When `--browser-capture` is supplied, it also validates
the headless Chromium public-demo screenshot manifest. When
`--recorder-capture` is supplied, it also validates direct MuJoCo simulator
recorder evidence. It preserves SMPL-X as the scoring source and records that
direct roboharness/live-runtime recording remains follow-on.

`neodojo real-conversion prepare` writes ignored source/trim metadata for the
later GPU run and does not download video or execute GVHMR. When a local video
is supplied, it records checksum data and optional ffprobe duration,
resolution, codec, and frame-rate metadata. It can either select an official
source-index row with `--id` or preserve custom local/user-supplied provenance
with `--local-source-id --local-video`. `neodojo real-conversion
materialize-source` consumes that prep manifest and a local video to write a
source-materialization manifest. With `--dry-run`, it records the ffmpeg trim
and reference-frame extraction commands without processing media. Without
`--dry-run`, it requires ffmpeg and writes ignored trimmed-video and frame
artifacts for the later GPU GVHMR input handoff. `make real-handoff
LOCAL_VIDEO=...` runs prep, dry-run source materialization by default, and GPU
handoff packaging in one command; set `REAL_LOCAL_SOURCE_ID=...` for custom
local-source provenance and `REAL_DRY_RUN=0` to actually trim/extract media when
ffmpeg is installed. `make real-handoff-smoke` runs that same local
handoff path with an ignored placeholder `.mp4` and is included in
`make verify`. `neodojo real-conversion
package-gpu-handoff` packages that manifest into a GPU handoff directory with a
machine-readable status, export template, provenance fields, upstream command
template, copyable source-materialization metadata, GPU-side neodojo export
helper, executable GPU runner, and local return command; it does not copy media
or run GVHMR locally.
`make real-gpu-archive LOCAL_VIDEO=...` chains non-dry-run source
materialization, GPU handoff packaging, media-including GPU input bundle
creation, and transfer archive creation in one local command for the external
GPU operator. It requires ffmpeg and does not run GVHMR locally.
`make real-gpu-run-request LOCAL_VIDEO=...` runs the same local archive
preparation and then writes the generated GPU operator request under
`GVHMR_RUN_REQUEST_OUT`, so one local command produces both the ignored transfer
archive and the request README/manifest.
`neodojo real-conversion probe-gpu-execution` and `make gpu-execution-probe`
write `outputs/gvhmr-gpu-execution-probe/manifest.json`, a
`neodojo.gvhmr_gpu_execution_probe.v1` manifest that records local CUDA command
presence, Docker GPU runtime visibility, provider CLI presence, and
provider-related environment variable names without recording secret values or
running GVHMR. When invoked with `--github-repo OWNER/REPO`, or through
`make gpu-execution-probe GPU_PROBE_GITHUB_REPO=OWNER/REPO`, it also records
self-hosted GitHub GPU runner availability and repository secret counts through
`gh` without recording secret values or secret names. The default
`make verify` path does not call the GitHub API.
`neodojo real-conversion package-gpu-input` and `make gpu-input-bundle
GPU_HANDOFF=... GPU_INPUT_INCLUDE_MEDIA=1` create an ignored copyable GPU input
bundle with `RUN_ON_GPU.md`, handoff metadata, `run_gvhmr_neodojo.sh`, exporter
helper, template, and the materialized `source/trimmed-clip.mp4`. This is a
transfer bundle for the selected GPU machine and must not be committed or
published.
`neodojo real-conversion archive-gpu-input` and `make gpu-input-archive
GPU_INPUT=...` write a single ignored `.tar.gz` transfer archive plus manifest
from that bundle.
`neodojo real-conversion write-gpu-run-request` and `make gvhmr-run-request
GPU_INPUT_ARCHIVE=...` turn that archive manifest into a concise
`neodojo.gvhmr_gpu_run_request.v1` operator request plus README with archive
hash, required GPU assets, expected return artifact, GPU command, and local
return checks. `make gvhmr-run-request-smoke` covers the metadata-only path in
`make verify`; media-containing requests stay ignored with their source archive.
`make real-gpu-colab-notebook LOCAL_VIDEO=...` chains the local archive,
operator request, and Colab notebook handoff into one command for operators who
will run GVHMR from a notebook runtime.
`make real-gpu-operator-package LOCAL_VIDEO=...` continues that chain by
collocating the archive, request, notebook, and package README/manifest into
one ignored operator package directory, then validating that copied package
before returning.
`neodojo real-conversion write-colab-notebook` and `make gvhmr-colab-notebook
GVHMR_RUN_REQUEST=...` turn that request manifest into a Colab-ready operator
notebook plus `neodojo.gvhmr_colab_operator_notebook.v1` sidecar manifest. The
notebook verifies archive checksum, unpacks the archive, checks the runner help,
keeps GVHMR execution guarded behind `RUN_GVHMR = False` by default, and records
the local `make real-artifact-intake` / `make verify-real` return commands.
`make gvhmr-colab-notebook-smoke` covers the metadata-only path in
`make verify`; media-containing notebooks stay ignored with their source
archive/request.
`neodojo real-conversion package-operator` and `make gvhmr-operator-package`
validate matching archive, request, and notebook checksums, then copy them into
one `neodojo.gvhmr_operator_package.v1` handoff directory; the Make target also
validates the copied package before returning. `neodojo real-conversion
validate-operator-package` and `make
gvhmr-operator-package-validate` validate an already-collocated package's
schemas, archive/request/notebook checksums, media flags, and expected return
schema before transfer. `make gvhmr-operator-package-smoke` covers the
metadata-only package path and package validation in `make verify`;
media-containing operator packages stay ignored.
`neodojo real-conversion archive-operator-package` and `make
gvhmr-operator-package-archive GVHMR_OPERATOR_PACKAGE=...` validate that
collocated package and write a single
`neodojo.gvhmr_operator_package_archive.v1` transfer `.tar.gz` plus manifest.
`make gvhmr-operator-package-archive-smoke` covers the metadata-only archive in
`make verify`; media-containing package archives stay ignored and unsafe for
git.
`neodojo real-conversion
inspect-gvhmr-result` writes a result
inspection manifest for a returned `hmr4d_results.pt` when `torch` is available
in the GVHMR/GPU environment, or for a JSON summary/export locally. It reports
top-level keys, candidate SMPL-X parameter blocks, and export guidance, but does
not convert raw GVHMR `.pt` files locally. `neodojo real-conversion
validate-source` compares the source-materialization manifest with GVHMR export
provenance, writes a validation report, and emits a validated JSON import copy
when source id, trim, input path/checksum, and duration checks pass. `neodojo
real-conversion import-demo` wraps validation, motion import, annotations,
surface proxy, G1 visual/render, teaching playback, public-demo, Viser preview,
and capture-bundle generation for that external artifact under
`outputs/real-demo/`. By default, the G1 visual companion remains fixture-derived
until an external G1 track is supplied. `make real-artifact-intake
REAL_ARTIFACT_GVHMR_JSON=...` is the simpler wrapper for the standard returned
artifact path.

## Remaining Non-GPU Gaps

- No unblocked fixture/public-demo non-GPU pipeline gaps are currently known.
  The local SMPL-X mesh surface path now accepts externally generated licensed
  mesh frames and references them in teaching/public playback. Built-in official
  SMPL-X body-model execution remains outside the repo until local licensed
  assets and a renderer dependency are deliberately added.

## Next Safe Task

The next default MVP capability remains
`docs/plans/mvp-real-conversion-gate.md` for the later GPU artifact import
path. Do not run GVHMR
full-video inference on this macOS CPU workspace; use a GPU-capable machine to
export a GVHMR SMPL-X teaching-joints JSON artifact, then import it through
`neodojo motion-record create --from-gvhmr-json`.

The current blocker is external to the local non-GPU pipeline: no GPU-produced
`neodojo.gvhmr_smplx_joints.v1` export is present in this workspace. A local
ignored Bilibili Baduanjin source candidate has been materialized under
`outputs/real-handoff-local-bilibili/`, the default source-materialization path
exists under `outputs/real-conversion-source/source-materialization.json`, and
a copyable media-including GPU input bundle exists under
`outputs/gvhmr-gpu-input-local-bilibili/`, with a
`run_gvhmr_neodojo.sh` runner, rights marked unconfirmed, and media kept out of
git. The same media-containing archive can now be regenerated in one command
with `make real-gpu-archive LOCAL_VIDEO=...`, or regenerated with a matching
operator request in one command via `make real-gpu-run-request LOCAL_VIDEO=...`.
For a notebook-based GPU operator, the archive, request, and Colab notebook can
now be regenerated together with `make real-gpu-colab-notebook LOCAL_VIDEO=...`.
For a single copyable handoff folder, those files can be collocated with
`make real-gpu-operator-package LOCAL_VIDEO=...`; for a single transfer file,
the collocated package can be wrapped with
`make real-gpu-operator-package-archive LOCAL_VIDEO=...`. The default ignored
package at `outputs/gvhmr-operator-package/` is ready for external GPU operator
handoff and marked unsafe for git because it contains media.
That operator request can also generate a Colab-ready notebook with
`make gvhmr-colab-notebook GVHMR_RUN_REQUEST=outputs/gvhmr-gpu-run-request` for
manual GPU execution in a notebook runtime; the current ignored local proof
notebook lives under `outputs/gvhmr-colab-operator-local-bilibili/`.
A local ignored transfer archive has also been generated at
`outputs/gvhmr-gpu-input-archive-local-bilibili/neodojo-gvhmr-gpu-input.tar.gz`;
its manifest reports `archive_with_media`, `media_included: true`, and
`safe_for_git: false`, and the extracted archive has been checked to contain
`run_gvhmr_neodojo.sh`, `RUN_ON_GPU.md`, `export_neodojo_gvhmr.py`,
`gvhmr-smplx-joints.template.json`, source metadata, and the trimmed clip. The
archive writer now rejects missing required GPU-operator files, including stale
bundles that omit the runner script. The tracked operator checklist is
`docs/runbooks/gvhmr-external-gpu.md`. The optional manual
`.github/workflows/gvhmr-self-hosted-gpu.yml` workflow can run the same bundle
or collocated operator package on a user-managed self-hosted GPU runner when
one exists, then immediately run real-artifact intake and strict completion
audit in that workflow. The separate
manual `.github/workflows/promote-real-demo-pages.yml` workflow can publish a
validated self-hosted real-demo artifact to Pages only after the operator
selects the source run, confirms replacement, and enables
`NEODOJO_DEPLOY_REAL_PAGES=true`. A
local/provider/GitHub execution probe found no CUDA runtime, no configured
GPU-provider environment variables or provider CLIs, zero self-hosted GitHub
Actions runners for `MiaoDX/neodojo`, and zero repository secrets; Docker is
available locally but does not expose a GPU runtime. The next external step is
therefore to copy the bundle or archive to a GPU-capable machine or
self-hosted GPU runner, run GVHMR, and return or upload the neodojo export.
Until then, `make verify-real` is expected to fail as the strict end-to-end
completion gate. Once that artifact exists, the remaining task is to validate
it with `real-conversion import-demo`, then inspect the generated
`outputs/real-demo/` artifacts.

## Background Evidence

- `docs/technical-roadmap.md` is the long technical research report.
- `docs/humanoid-platform-evaluation.md` records the G1 + SMPL-X dual-track
  platform decision.
- `docs/plans/mvp-implementation-phases.md` indexes the current executable MVP
  plan slices.
