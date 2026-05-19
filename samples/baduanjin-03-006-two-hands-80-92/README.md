# Baduanjin 03-006 Two Hands Hold Up The Heavens, 80s-92s

This sample contains the small source clip and derived JSON artifacts for the
real-demo CI lane:

- `source/video/original-clip.mp4` is the trimmed `80s-92s` source clip used by
  the HTML and README GIF.
- `source/source-materialization.json` records the source provenance and trim.
- `gvhmr/gvhmr-smplx-joints.json` is the returned GVHMR SMPL-X teaching-joints export.
- `gmr/gmr-unitree-g1.json` is the normalized Unitree G1 GMR visual-track export.

Source provenance is documented as public index item `03-006` in
`video/original_videos.md`, using trim `80s-92s`.

The sample intentionally does not include extracted source frames, native
GVHMR/GMR checkpoints, pickles, or rendered PNG outputs. CI regenerates the
motion contract, G1 track, MuJoCo render frames, public HTML, and README GIF
from these sample artifacts.

Larger source videos should be downloaded by helper scripts for local
reproducibility rather than committed directly.
