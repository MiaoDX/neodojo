# Baduanjin 03-006 Two Hands Hold Up The Heavens, 80s-92s

This sample contains small derived JSON artifacts for the real-demo CI lane:

- `source/source-materialization.json` records the source provenance and trim.
- `gvhmr/gvhmr-smplx-joints.json` is the returned GVHMR SMPL-X teaching-joints export.
- `gmr/gmr-unitree-g1.json` is the normalized Unitree G1 GMR visual-track export.

Source provenance is documented as public index item `03-006` in
`video/original_videos.md`, using trim `80s-92s`.

The sample intentionally does not include raw video, extracted source frames,
native GVHMR/GMR checkpoints, pickles, or rendered PNG outputs. CI regenerates
the motion contract, G1 track, MuJoCo render frames, and public HTML from these
JSON artifacts.
