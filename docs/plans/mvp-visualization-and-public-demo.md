# MVP Visualization And Public Demo Plan

Status: PLANNED NON-GPU SLICE

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
- Annotation manifest with the first manual key-frame feedback proof.
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
   - Treat the current HTML playback state as one consumer, not the source of
     truth.
   - Represent SMPL-X, G1, reference video, trajectories, annotations, cameras,
     and timing in one compact structure.
   - Keep scoring permissions explicit per track.

2. Implement Rerun export as the first public artifact.
   - Export track points, bones or line strips, trajectories, labels, cameras,
     and key-frame markers into `.rrd`.
   - Include clear fixture-only labels when the source data is synthetic.
   - Keep generated `.rrd` files out of tracked source.

3. Add a static Rerun Web Viewer page.
   - Load the generated `.rrd` artifact from the publish output.
   - Make the page usable as a static artifact for CI and GitHub Pages.
   - Avoid presenting it as the final teaching UI.

4. Capture public-demo visual evidence.
   - Generate a screenshot or short GIF from the static page.
   - Verify that the page is nonblank and shows expected SMPL-X/G1 tracks,
     trajectories, labels, and fixture-only status.
   - Store generated images under ignored output or publish artifact staging.

5. Keep Viser as a later local/server runtime.
   - Preserve scene contract fields Viser will need: synchronized viewports,
     timeline state, selected joints, annotations, and optional reference video.
   - Do not require Viser to complete the first public demo.

6. Treat simulator renders as evidence inputs.
   - Use MuJoCo or Genesis frames when available to prove real model rendering.
   - Do not make MuJoCo the public UI surface for the first demo.
   - Keep MeshCat as an optional compatibility adapter only.

7. Update human docs only after publishing exists.
   - README.md and README.zh.md must link to the GitHub Pages demo and embed
     the generated screenshot or GIF only after the command and publish artifact
     exist.
   - The docs must clearly mark fixture-only demos as fixture-only.

## Acceptance Evidence

- A scene/timeline manifest can be produced from existing playback artifacts.
- A Rerun `.rrd` export is generated under ignored output from fixture data.
- A static Rerun Web Viewer page can load the recording locally.
- A screenshot or GIF shows nonblank SMPL-X/G1 tracks, trajectory labels, and
  fixture-only status.
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

Stop when a fixture-only but honest Rerun Web Viewer demo can be generated,
visually smoke-tested, and staged for GitHub Pages through artifacts, with the
scene/timeline contract ready for later Viser integration.
