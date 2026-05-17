# MVP Rerun Pages Release Plan

Status: IMPLEMENTED OPTIONAL SDK EXPORT; LIVE PAGES VERIFICATION PENDING

## Goal

Add a true Rerun recording path alongside the current `.rrd` JSON fallback and
verify the live public demo path:

```text
scene/timeline contract
  -> rerun-sdk recording export
  -> static web viewer assets
  -> CI artifact
  -> GitHub Pages deployment
  -> README screenshot/GIF and live link
```

The current static fallback remains honest and useful for default CI. The
optional SDK path writes a true `.rrd` when `rerun-sdk` is installed. Live Pages
verification still waits on repository settings.

## Dependencies

- [mvp-visualization-and-public-demo.md](mvp-visualization-and-public-demo.md)
  provides the public-demo scene contract and fallback artifact.
- [mvp-devex-ci-surface.md](mvp-devex-ci-surface.md) provides CI artifact and
  Pages workflow scaffolding.
- Rerun SDK can be installed locally through the optional `rerun` extra.
- GitHub Pages is enabled for the repository, and the repository variable
  `NEODOJO_DEPLOY_PAGES=true` is set when deployment should run.

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
- CLI command:

  ```bash
  PYTHONPATH=src python -m neodojo demo export-rerun \
    --playback outputs/teaching-demo/manifest.json \
    --g1-render outputs/g1-render/manifest.json \
    --use-rerun-sdk \
    --out outputs/public-demo/neodojo-demo.rrd
  ```

## Execution Tasks

1. Add optional SDK export.
   - [x] Add dependency strategy for `rerun-sdk` via the optional `rerun` extra.
   - [x] Log SMPL-X and G1 joint/bone tracks plus public labels into a true
     `.rrd`.
   - [x] Keep fallback JSON path available when SDK is absent or not requested.

2. Harden CI/Page publish.
   - [ ] Cache/install SDK efficiently if CI should publish true `.rrd` instead
     of the default fallback.
   - [ ] Verify artifact upload and Pages deployment.
   - [ ] Capture or generate a screenshot/GIF from the published artifact.

3. Update public docs.
   - [ ] Add live demo link only after Pages URL is verified.
   - [ ] Mark the demo fixture-only until a real GVHMR artifact enters.

## Acceptance Evidence

- Optional smoke writes a true `.rrd` with `rerun.actual_rrd: true` when
  `rerun-sdk` is installed.
- Default CI continues to produce and upload the fallback recording and static
  viewer artifact without a heavy default dependency, verified by GitHub
  Actions run `25998306700`.
- The live GitHub Pages URL is verified before README links are added.
- Default CI remains green and still uploads the public-demo artifact when Pages
  deployment is not enabled.
- README.md and README.zh.md link to the live fixture-only demo with matching
  language only after Pages verification.

## Non-Goals

- Replacing the future Viser teaching runtime.
- Claiming qigong correctness from fixture data.
- Requiring source videos or GPU work in CI.
- Publishing raw/generated media outside the deliberate Pages artifact.

## Stop Condition

Stopped for the SDK slice when the optional exporter wrote a true Rerun SDK
recording and the fallback path remained available. Continue only when CI cache
policy, repository Pages settings, and the `NEODOJO_DEPLOY_PAGES` deploy toggle
are available for live URL verification.
