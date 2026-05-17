# MVP Pipeline Contract Hardening Plan

Status: IMPLEMENTED

## Goal

Harden the project-owned artifact contracts before the GPU conversion gate:

```text
local source media metadata
  -> source-prep manifest
  -> GVHMR SMPL-X import manifest
  -> normalized SMPL-X motion record
  -> SMPL-X teaching track
  -> G1 visual track
  -> render/playback/public-demo manifests
  -> annotation and local reference-video sync metadata
```

The goal is not to add new model inference. The goal is to make every local and
imported artifact explicit enough that later real GVHMR, GMR, rendering, and
public-demo work can fail at a named contract boundary instead of leaking
special cases into downstream code.

## Dependencies

- [mvp-local-motion-contract.md](mvp-local-motion-contract.md) provides the
  current fixture and external GVHMR teaching-joints JSON import boundary.
- [mvp-g1-visual-track.md](mvp-g1-visual-track.md) provides the derived G1
  visual-track boundary and `g1_scoring_allowed: false` convention.
- [mvp-teaching-playback-demo.md](mvp-teaching-playback-demo.md) provides the
  first playback manifest and manual SMPL-X feedback proof.
- [mvp-g1-real-model-rendering.md](mvp-g1-real-model-rendering.md) may add the
  first real render manifest; this hardening slice should preserve that shape
  instead of replacing it.
- No GVHMR, GMR, HAMER, MuJoCo, Genesis, Viser, Rerun, or CI runtime is
  required to complete this slice.

## Implemented Local Path

The local artifact writers now emit explicit schema ids at the motion,
teaching-track, G1-track, render, playback, HTML-demo, annotation, source-media,
and real-conversion prep boundaries. Existing readers validate schema versions
before consuming motion, SMPL-X track, G1 track, and G1 model manifests.

Motion, G1-track, render, and playback manifests carry shared timing,
coordinate, floor-height, and advisory foot-contact metadata. The contact
metadata is derived from normalized ankle height and is not a physics contact
solve.

`real-conversion prepare` records a `source_media` contract. When
`--local-video` is supplied, it validates the local file, records size, suffix,
and SHA-256 checksum, and stores local-only reference-video sync metadata. When
no local video is supplied, the planned path remains metadata-only and the
manifest records that the local file was not validated.

`demo play` accepts annotation manifests using `neodojo.annotation.v1` and can
preserve optional local-only reference-video sync metadata. The legacy
`{"key_frame": ...}` annotation shape is normalized into the v1 manifest shape
for compatibility.

## Inputs

- Existing motion-record, teaching-track, G1 visual-track, playback, and
  real-conversion prep manifests.
- Existing fixture data and any externally exported GVHMR teaching-joints JSON
  samples used for local validation.
- Local/user-supplied source video path metadata, without committing media.
- Optional local original-video path for synchronized reference playback.
- Manual key-frame annotation notes for the first Baduanjin opening-form proof.
- Artifact and licensing policy from `AGENTS.md`, `STATUS.md`, and
  `ARCHITECTURE.md`.

## Outputs

- Versioned schema identifiers and validators for:
  - source-prep manifests
  - motion records
  - SMPL-X teaching-track manifests
  - G1 visual-track manifests
  - render manifests
  - playback manifests
  - annotation manifests
  - public-demo manifests
- A source-media intake contract that records local file validation,
  probe-derived trim metadata, provenance, checksums, and rights notes without
  copying source media into the repo.
- A local-only original-video sync contract for side-by-side reference playback
  when the user has a lawful local video file.
- Coordinate, floor, facing, scale, and timing normalization fields that are
  shared by SMPL-X, G1, render, and playback consumers.
- Foot/contact metadata fields for stance, foot-lock, and drift diagnostics.
- A manual key-frame annotation format for named postures, frame ranges,
  teaching terms, selected joints, and SMPL-X geometry checks.
- Focused tests for schema migration, missing-field errors, artifact policy,
  local-media path handling, and scoring-source enforcement.

## Execution Tasks

1. Inventory current manifest fields.
   - [x] List each existing manifest type and the code paths that write/read it.
   - [x] Classify each field as stable contract, implementation detail, or
     fixture convenience through the schema-bearing manifest update.
   - [x] Identify duplicated status fields such as fixture-only, source type,
     timing, provenance, and scoring metadata.

2. Introduce explicit schema versions.
   - [x] Add stable schema ids such as `neodojo.motion_record.v1` and
     `neodojo.playback_manifest.v1`.
   - [x] Keep version checks strict enough to catch incompatible artifacts.
   - [x] Provide no migration helpers yet because no durable pre-v1 generated
     artifacts are tracked.

3. Harden source media intake.
   - [x] Validate local path existence, extension, readable size, and checksum
     when `--local-video` is supplied.
   - [x] Preserve source-index duration/resolution and trim metadata.
   - [x] Store rights notes, official source URLs, local origin notes, and
     user-supplied path references.
   - [x] Keep raw videos and generated clips ignored; never copy them into
     tracked source files.

4. Add original-video reference sync.
   - [x] Record local-only video path, trim offset, checksum, frame-zero offset,
     and sync confidence when a local reference video is supplied.
   - [x] Let playback preserve this as optional reference metadata.
   - [x] Make missing local video a soft metadata limitation, not a contract
     failure for CI fixtures.

5. Normalize coordinate semantics.
   - [x] Define world-up, facing direction, floor height, root joint, units, and
     frame timing in the motion record.
   - [x] Preserve enough metadata to compare SMPL-X and G1 tracks after
     retargeting or rendering.
   - [x] Add diagnostics for floor/contact derivation.

6. Add contact and stance metadata.
   - [x] Record per-foot contact ratio and foot-lock windows.
   - [x] Mark contact fields advisory until a real GVHMR/GMR artifact proves
     them.

7. Define manual annotation manifests.
   - [x] Support named key frames, frame ranges through keyframe entries,
     teaching terms, selected joints, and SMPL-X-only geometry checks.
   - [x] Keep annotations independent of G1 so robot visual changes do not
     affect scoring.
   - [x] Leave room for future automated key-frame detection without requiring
     it now.

8. Update commands and tests only where contracts change.
   - [x] Keep existing fixture commands working.
   - [x] Add validators to writers/readers that already exist.
   - [x] Update STATUS because the current next safe task changed.

## Acceptance Evidence

- Existing fixture commands still write valid versioned manifests.
- Invalid or future schema versions fail with clear messages.
- Source-prep validation records local media metadata, checksums, trim windows,
  provenance, and rights notes without committing media when a local file is
  supplied.
- Original-video sync metadata can be present for local playback and absent for
  fixture/CI paths.
- Motion, G1, render, playback, annotation, and public-demo manifests share
  consistent timing and coordinate semantics.
- Contact/floor/facing diagnostics are present in manifests or validation
  reports where the data exists.
- Manual key-frame annotations can drive the existing SMPL-X-only feedback
  proof.
- Tests prove that G1 and rendered/public-demo artifacts remain non-scoring.

## Non-Goals

- Running GVHMR, GMR, HAMER, or any GPU inference.
- Implementing the public Rerun/GitHub Pages demo.
- Implementing Viser, MuJoCo, Genesis, or MeshCat runtime UI work.
- Automatic key-frame detection.
- Redistributing official instructional videos or generated motion artifacts.
- Creating broad install, lint, build, or CI claims before those surfaces exist.

## Stop Condition

Stopped when every current non-GPU artifact has a versioned manifest boundary,
local media provenance can be recorded without committing media, optional
original-video sync is represented, and the existing fixture playback path still
passes through the hardened contracts.
