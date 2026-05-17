# MVP Source Media Probing Plan

Status: IMPLEMENTED METADATA PROBE

## Goal

Record richer local source-media metadata before the GPU conversion gate:

```text
local/user-supplied video path
  -> checksum and suffix validation
  -> optional ffprobe metadata
  -> source-media manifest
  -> trim/reference sync metadata
```

The probe is advisory and non-blocking. It should improve provenance without
copying media into the repo or requiring ffprobe in CI.

## Dependencies

- [mvp-pipeline-contract-hardening.md](mvp-pipeline-contract-hardening.md)
  defines the source-media contract and local-only media policy.
- [mvp-real-conversion-gate.md](mvp-real-conversion-gate.md) owns the later GPU
  source clip path and trim metadata.
- [mvp-source-media-materialization.md](mvp-source-media-materialization.md)
  consumes the validated local source path when a real trim/frame handoff is
  needed.

## Inputs

- Optional `--local-video` path passed to `neodojo real-conversion prepare`.
- Optional `--local-source-id` path for local/user-supplied sources that should
  derive duration/resolution from the local file instead of an official
  source-index row.
- Source-index duration/resolution metadata.
- Local `ffprobe` executable when available.

## Outputs

- `source_media.probe` using schema `neodojo.media_probe.v1`.
- Parsed format duration, file size, bit rate, format name, video codec,
  resolution, frame rate, and duration when ffprobe succeeds.
- Probe availability/failure messages when ffprobe is missing or the local file
  is not a valid video.
- `source_media.validation.media_probe_succeeded`.

## Execution Tasks

1. Add optional media probing.
   - [x] Detect `ffprobe` on PATH.
   - [x] Run ffprobe with JSON output when local video exists.
   - [x] Parse the first video stream and format metadata.
   - [x] Keep failures advisory, not fatal.
   - [x] Require successful ffprobe duration only for custom local-source prep,
     where no source-index duration exists.

2. Preserve artifact policy.
   - [x] Do not copy local video.
   - [x] Keep only path, checksum, probe metadata, and sync metadata.

3. Verify.
   - [x] Unit-test ffprobe payload parsing.
   - [x] Unit-test prep manifests include probe metadata fields for local
     video input.

## Acceptance Evidence

- `make test` covers probe parsing and manifest presence.
- `neodojo real-conversion prepare --local-video ...` records probe success or
  failure without copying media.
- `neodojo real-conversion prepare --local-source-id ... --local-video ...`
  can derive duration and resolution from a valid local file while keeping that
  source's provenance separate from official source-index rows.
- Missing or failing ffprobe does not block fixture/source-prep flows.

## Non-Goals

- Downloading official videos.
- Trimming or transcoding clips.
- Extracting frames.
- Requiring ffmpeg/ffprobe in CI.
- Proving GVHMR compatibility.

## Stop Condition

Stopped when local source-video prep records optional ffprobe metadata and
continues safely when ffprobe is unavailable or the local file is not a valid
video.
