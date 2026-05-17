# MVP Rerun Pages Release Plan

Status: PLANNED; BLOCKED ON RERUN SDK INSTALL AND REPOSITORY PAGES SETTINGS

## Goal

Replace the current `.rrd` JSON fallback with a true Rerun recording and verify
the live public demo path:

```text
scene/timeline contract
  -> rerun-sdk recording export
  -> static web viewer assets
  -> CI artifact
  -> GitHub Pages deployment
  -> README screenshot/GIF and live link
```

The current static fallback remains honest and useful until the SDK and Pages
environment are proven.

## Dependencies

- [mvp-visualization-and-public-demo.md](mvp-visualization-and-public-demo.md)
  provides the public-demo scene contract and fallback artifact.
- [mvp-devex-ci-surface.md](mvp-devex-ci-surface.md) provides CI artifact and
  Pages workflow scaffolding.
- Rerun SDK can be installed in local/CI environments without unacceptable
  runtime or cache cost.
- GitHub Pages is enabled for the repository.

## Inputs

- Public-demo scene/timeline JSON.
- Optional G1 render manifest and screenshot.
- Rerun SDK version.
- GitHub Actions Pages settings and workflow permissions.

## Outputs

- True Rerun SDK `.rrd` recording.
- Static viewer page that loads the real `.rrd` or clearly falls back.
- CI smoke that validates recording presence and page nonblank state.
- README.md and README.zh.md live demo link plus generated screenshot/GIF once
  Pages is verified.

## Execution Tasks

1. Add optional SDK export.
   - [ ] Add dependency strategy for `rerun-sdk`.
   - [ ] Log SMPL-X, G1, annotation, and camera tracks into a true `.rrd`.
   - [ ] Keep fallback JSON path available when SDK is absent.

2. Harden CI/Page publish.
   - [ ] Cache/install SDK efficiently.
   - [ ] Verify artifact upload and Pages deployment.
   - [ ] Capture or generate a screenshot/GIF from the published artifact.

3. Update public docs.
   - [ ] Add live demo link only after Pages URL is verified.
   - [ ] Mark the demo fixture-only until a real GVHMR artifact enters.

## Acceptance Evidence

- A true `.rrd` opens in Rerun tooling or the Rerun web viewer.
- CI produces and uploads the real recording and static viewer artifact.
- The live GitHub Pages URL is verified.
- README.md and README.zh.md link to the live fixture-only demo with matching
  language.

## Non-Goals

- Replacing the future Viser teaching runtime.
- Claiming qigong correctness from fixture data.
- Requiring source videos or GPU work in CI.
- Publishing raw/generated media outside the deliberate Pages artifact.

## Stop Condition

Stop when the real Rerun SDK recording and live GitHub Pages fixture demo are
verified, or when blockers are classified as SDK install, CI cache, or Pages
configuration issues.
