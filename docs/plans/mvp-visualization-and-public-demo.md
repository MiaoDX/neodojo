# MVP Visualization And Public Demo Plan

Status: IMPLEMENTED WITH STATIC FALLBACK AND OPTIONAL RERUN SDK EXPORT; PAGES PUBLISH REMAINS FOLLOW-ON

## Goal

Create one internal visualization contract and the first public demo publishing
path:

```text
hardened motion/render/playback artifacts
  -> internal scene/timeline contract
  -> Rerun recording export (.rrd)
  -> static Rerun Web Viewer page
  -> generated screenshot or GIF
  -> GitHub Pages artifact
```

The first public target is Rerun Web Viewer because it can publish an
inspectable web artifact without committing to the future local/server teaching
runtime. Viser remains the intended richer interactive runtime later. MuJoCo is
render/simulator evidence, not the primary public UI. MeshCat is optional
compatibility only and should not block this slice.

## Implemented Local Path

`neodojo demo export-rerun` now writes the internal scene/timeline contract,
static public-demo HTML, SVG screenshot, public-demo manifest, and a
`.rrd`-named recording artifact under ignored output. By default, the `.rrd`
file is explicitly marked as a JSON fallback artifact with
`actual_rerun_rrd: false`; it is not presented as a real Rerun SDK recording.
When the optional `rerun` extra is installed and `--use-rerun-sdk` is passed,
the same command writes a true Rerun SDK recording.

The static HTML page is the current CI/publishable artifact. It is fixture-only,
shows SMPL-X and G1 labels, preserves the G1 non-scoring boundary, and embeds
the scene contract for smoke checks. Verified live GitHub Pages URL evidence
remains follow-on work. The DevEx/CI slice now stages the static artifact for
Pages and publishes from `main` when repository Pages settings allow it.

## Dependencies

- [mvp-pipeline-contract-hardening.md](mvp-pipeline-contract-hardening.md)
  provides stable manifest and scene metadata boundaries.
- [mvp-g1-real-model-rendering.md](mvp-g1-real-model-rendering.md) should
  provide real robot render evidence when available, but this public demo can
  start with fixture tracks if it is clearly labeled fixture-only.
- [mvp-teaching-playback-demo.md](mvp-teaching-playback-demo.md) provides the
  current synchronized playback semantics, trajectory joints, and one SMPL-X
  feedback proof.
- [mvp-devex-ci-surface.md](mvp-devex-ci-surface.md) will own the one-command
  orchestration, CI capture, artifact upload, and GitHub Pages publish job.

## Inputs

- Versioned SMPL-X motion-record and teaching-track manifests.
- Versioned G1 visual-track and optional render manifests.
- Annotation manifest with the first key-frame feedback proof.
- Playback manifest or internal scene metadata from the existing local demo.
- Optional generated still frames from MuJoCo/Genesis when real rendering
  exists.
- Fixture-only labels and provenance data from upstream contracts.

## Outputs

- An internal scene/timeline contract that can represent:
  - tracks, roles, and scoring permissions
  - frame timing and playback ranges
  - front/side/top camera definitions
  - selected trajectory joints and labels
  - key-frame annotations and SMPL-X feedback results
  - source/reference-video sync metadata when local-only video exists
  - fixture-vs-real provenance for each visible lane
- A Rerun export command, for example:

  ```bash
  PYTHONPATH=src python -m neodojo demo export-rerun \
    --playback outputs/teaching-demo/manifest.json \
    --out outputs/public-demo/neodojo-demo.rrd
  ```

- A static web viewer page under ignored or publish-staged output, for example
  `outputs/public-demo/index.html`.
- A generated screenshot or GIF suitable for README/README.zh embedding after
  the publish path really exists.
- A public-demo manifest recording source manifests, Rerun version, output
  paths, screenshot path, fixture-only status, and publish metadata.
- Focused tests for scene contract generation, Rerun export metadata, and
  public-demo manifest validation.

## Execution Tasks

1. Define the internal scene/timeline contract.
   - [x] Treat the current HTML playback state as one consumer, not the source
     of truth.
   - [x] Represent SMPL-X, G1, reference video, trajectories, annotations,
     cameras, and timing in one compact structure.
   - [x] Keep scoring permissions explicit per track.

2. Implement Rerun export as the first public artifact.
   - [x] Export track points, bones, trajectories, labels, cameras, and
     key-frame markers into a `.rrd`-named fallback artifact.
   - [x] Include clear fixture-only labels when the source data is synthetic.
   - [x] Keep generated `.rrd` files out of tracked source.
   - [x] Add an optional true Rerun SDK `.rrd` path while preserving the default
     fallback artifact.

3. Add a static Rerun Web Viewer page.
   - [x] Generate a static HTML public-demo page from the scene/timeline
     contract.
   - [x] Make the page usable as a static artifact for CI and GitHub Pages.
   - [x] Avoid presenting it as the final teaching UI or a real Rerun Web
     Viewer while the SDK export is absent.

4. Capture public-demo visual evidence.
   - [x] Generate an SVG screenshot from the scene contract.
   - [x] Verify through tests and smoke-searchable labels that the page is
     nonblank and shows expected SMPL-X/G1 tracks, labels, and fixture-only
     status.
   - [x] Store generated images under ignored output or publish artifact
     staging.

5. Keep Viser as a separate local/server runtime.
   - [x] Preserve scene contract fields the Viser runtime needs: synchronized
     viewports, timeline state, selected joints, annotations, and optional
     reference video.
   - [x] Do not require Viser to complete the first public demo.

6. Treat simulator renders as evidence inputs.
   - [x] Consume G1 render evidence when available.
   - [x] Do not make MuJoCo the public UI surface for the first demo.
   - [x] Keep MeshCat as an optional compatibility adapter only.

7. Update human docs only after publishing exists.
   - [x] README.md and README.zh.md document the local command and fixture-only
     status without claiming GitHub Pages publication.
   - [ ] Add the GitHub Pages link and embedded screenshot/GIF only after the
     workflow publishes the artifact.

## Acceptance Evidence

- A scene/timeline manifest can be produced from existing playback artifacts.
- A `.rrd`-named fallback export is generated under ignored output from fixture
  data and is explicitly marked `actual_rerun_rrd: false`.
- An optional SDK export can generate a true `.rrd` and mark
  `rerun.actual_rrd: true`.
- A static public-demo page can load the scene locally.
- An SVG screenshot shows nonblank SMPL-X/G1 tracks, labels, and fixture-only
  status.
- The public-demo manifest records provenance, Rerun/Web Viewer versions,
  generated paths, and scoring-source metadata.
- README.md and README.zh.md are updated only after the GitHub Pages artifact
  exists, and both clearly label fixture-only status.
- No generated `.rrd`, screenshots, GIFs, videos, logs, or large artifacts are
  committed to the normal source branch.

## Non-Goals

- Building the final Viser teaching UI.
- Making MuJoCo, Genesis, or MeshCat the primary public web UI.
- Running GPU conversion or proving qigong correctness.
- Publishing source videos or generated motion artifacts.
- Replacing the local fixture HTML playback command.
- Adding a broad frontend application before the artifact contract is stable.

## Stop Condition

Stopped when a fixture-only but honest static public demo can be generated,
visually smoke-tested, and staged for GitHub Pages through artifacts, with the
scene/timeline contract ready for the optional Viser runtime. Verified live
Pages publication remains follow-on work.
