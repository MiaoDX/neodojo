# MVP DevEx And CI Surface Plan

Status: PLANNED NON-GPU SLICE

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
surface and workflow exist.

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
   - Prefer one Make target if it matches the current repo shape.
   - Use a Python CLI command only when it keeps artifact paths and validation
     more explicit.
   - Keep commands small and reproducible.

2. Add minimal dev setup only when necessary.
   - Add package metadata, dependency groups, or scripts if CI needs them.
   - Do not add install/lint/build claims before the commands exist and pass.
   - Keep optional heavyweight visualization dependencies out of the default
     path unless they are required for the public demo.

3. Build the local demo-public flow.
   - Generate motion-record and teaching-track fixtures.
   - Generate G1 visual-track fixtures or consume the current fixture manifest.
   - Generate teaching playback HTML/manifest.
   - Export Rerun `.rrd` and static viewer page.
   - Capture screenshot/GIF evidence.
   - Write a public-demo manifest.

4. Add CI validation.
   - Run `make test` or the focused equivalent.
   - Run the public demo generation command.
   - Validate every generated manifest.
   - Upload generated outputs as CI artifacts without committing them.

5. Add visual smoke checks.
   - Open generated HTML/Rerun pages in headless browser automation.
   - Check that pages are nonblank.
   - Check expected text or scene labels for SMPL-X, G1, fixture-only status,
     selected trajectories, and scoring-source metadata.
   - Save screenshots as artifacts.

6. Publish to GitHub Pages.
   - Stage only static public-demo assets in the Pages artifact.
   - Do not publish source videos, generated motion files, checkpoints, logs, or
     large private artifacts.
   - Keep repository owner setup steps explicit if Pages permissions are not
     configured in code.

7. Update docs after verification.
   - README.md and README.zh.md may link to the GitHub Pages demo only after
     the workflow and artifact exist.
   - STATUS.md should list new commands only after they run locally.
   - Keep fixture-only limitations visible in every user-facing mention.

## Acceptance Evidence

- One local command regenerates the fixture public-demo artifacts from a clean
  ignored output directory.
- Unit tests and manifest validation pass locally and in CI.
- CI uploads the generated Rerun recording, static viewer page, screenshot/GIF,
  and public-demo manifest as artifacts.
- The visual smoke check proves the generated pages are nonblank and include
  expected tracks/labels.
- GitHub Pages can publish only safe static demo assets.
- README.md and README.zh.md mention the public demo only after the Pages URL
  exists and both clearly mark it fixture-only.
- Generated outputs, screenshots, `.rrd`, videos, logs, and large artifacts
  remain out of tracked source except for deliberate publish artifacts.

## Non-Goals

- Running GVHMR, GMR, HAMER, or any GPU inference in CI.
- Adding broad lint or build systems unless the implementation actually needs
  and verifies them.
- Publishing official source videos or generated motion artifacts.
- Making CI the proof of qigong correctness.
- Replacing later real-artifact or Viser work.

## Stop Condition

Stop when a clean checkout can run one non-GPU public-demo command locally, CI
can regenerate and visually smoke-test the same artifact set, and GitHub Pages
publishing can run without tracking generated outputs in the source branch.
