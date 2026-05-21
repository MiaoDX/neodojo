# Full Routine Samples

This directory contains committed static routine reports for the three tracked
Bilibili routines. The Pages workflow publishes this gallery as the site
homepage and keeps a compatibility mirror under `/samples/routines/`.

| Routine | Local report | Homepage URL after deploy | Mirror URL after deploy |
| --- | --- | --- | --- |
| Baduanjin | [`baduanjin/html/index.html`](baduanjin/html/index.html) | `https://miaodx.com/neodojo/baduanjin/html/` | `https://miaodx.com/neodojo/samples/routines/baduanjin/html/` |
| Wu Qin Xi | [`wuqinxi/html/index.html`](wuqinxi/html/index.html) | `https://miaodx.com/neodojo/wuqinxi/html/` | `https://miaodx.com/neodojo/samples/routines/wuqinxi/html/` |
| Yi Jin Jing | [`yijinjing/html/index.html`](yijinjing/html/index.html) | `https://miaodx.com/neodojo/yijinjing/html/` | `https://miaodx.com/neodojo/samples/routines/yijinjing/html/` |

Each report is a lean self-contained playback artifact with one representative
round per phase, local Original video clips, SMPL-X Teaching Track playback,
and 5 fps Unitree G1 Model Replay MP4 media. Bulky debug evidence such as
MuJoCo replay PNG frame trees, native GVHMR `.pt` files, GMR `.pkl` files, and
logs are intentionally not committed.

The full source videos remain licensing-sensitive and are not committed. The
reproducible command surface for rebuilding local reports from user-supplied
source media is documented in the repository README and `STATUS.md`.
