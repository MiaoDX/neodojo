# MVP DevEx And CI Surface Plan

Status: IMPLEMENTED

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
artifact, SVG screenshot, and public-demo manifest. It then runs
`neodojo demo smoke` against `outputs/public-demo`.

`.github/workflows/public-demo.yml` installs the package, runs `make test`,
runs `make demo-public`, uploads `outputs/public-demo` as a workflow artifact,
and uploads the same directory as the GitHub Pages artifact. The deploy job runs
only on `main` outside pull requests. Pages still requires repository Pages
configuration to expose a live URL.

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

4. Add CI validation.
   - [x] Run `make test`.
   - [x] Run `make demo-public`.
   - [x] Validate generated public-demo artifacts with `neodojo demo smoke`.
   - [x] Upload generated outputs as CI artifacts without committing them.

5. Add visual smoke checks.
   - [x] Check generated HTML, scene, `.rrd` fallback, and SVG screenshot are
     nonblank.
   - [x] Check expected text or scene labels for SMPL-X, G1, fixture-only
     status, and scoring-source metadata.
   - [x] Save SVG screenshots as artifacts.
   - [ ] Add browser-rendered screenshot capture if/when a browser dependency
     becomes part of CI.

6. Publish to GitHub Pages.
   - [x] Stage only static public-demo assets in the Pages artifact.
   - [x] Do not publish source videos, generated motion files, checkpoints,
     logs, or large private artifacts.
   - [x] Keep repository owner setup implicit in GitHub Pages settings; no live
     URL is claimed in docs.

7. Update docs after verification.
   - [x] README.md and README.zh.md describe the local command and workflow but
     do not link a Pages URL.
   - [x] STATUS.md lists new commands only after they run locally.
   - [x] Keep fixture-only limitations visible in every user-facing mention.

## Acceptance Evidence

- One local command regenerates the fixture public-demo artifacts from a clean
  ignored output directory.
- Unit tests and manifest validation pass locally; CI is configured to run the
  same commands.
- CI uploads the generated `.rrd` fallback recording, static viewer page, SVG
  screenshot, and public-demo manifest as artifacts.
- The visual smoke check proves the generated pages are nonblank and include
  expected tracks/labels.
- GitHub Pages can publish only safe static demo assets once repository Pages is
  enabled.
- README.md and README.zh.md mention the public demo command and workflow
  without claiming a live Pages URL.
- Generated outputs, screenshots, `.rrd`, videos, logs, and large artifacts
  remain out of tracked source except for deliberate publish artifacts.

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
