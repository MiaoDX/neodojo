# Video Assets

This directory keeps video work reproducible without downloading every large
source file by default.

## Current Local Files

- `bilibili/`: the first Bilibili batch, downloaded as compact 480p MP4 files.
- `bilibili/routines.json`: manual first-demo phase boundaries for the tracked
  八段锦, 易筋经, and 五禽戏 Bilibili videos.
- `original_videos.*`: an index of the 131 official Shenzhen site source MP4s.
- `manifest.json`: source metadata and English filename mapping for the official
  Shenzhen site videos.
- `download_originals.py`: helper for selectively downloading official source
  MP4s from the saved index.

The official source index is intentionally lightweight. The 131 original site
videos total about 6.67 GiB, so do not download all originals unless that is
explicitly needed.

## Fast, Stable Download Rules

1. Prefer metadata first.
   - Use `original_videos.csv` or `original_videos.md` to choose exact IDs by
     size, duration, category, and resolution.
   - Keep original URLs and source sizes in manifests so higher-quality files can
     be fetched later without rediscovery.

2. Download selectively.
   - Use explicit IDs or categories, not broad recursive downloads.
   - Dry-run before downloading:

```bash
./video/download_originals.py --id 03-001 --dry-run
./video/download_originals.py --category 01_dawu --dry-run
```

3. Use resumable transfers.
   - `download_originals.py` uses `curl -C -` so interrupted files can resume.
   - Completed files are checked against the source `Content-Length`.

4. Use range/segmented downloads for slow CDNs.
   - Some government and Bilibili CDN streams are slow as one large connection.
   - For large batches, split by byte ranges, download chunks concurrently, then
     merge and verify size. This was much faster and more reliable than one
     long-running `curl`.

5. Verify every MP4 after download.

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,codec_name:format=duration,size,bit_rate \
  -of json video/bilibili/01_baduanjin-complete-routine-with-breathing-cues.mp4

ffmpeg -v error -xerror -i video/bilibili/01_baduanjin-complete-routine-with-breathing-cues.mp4 -f null -
```

`ffprobe` confirms metadata. `ffmpeg -xerror` catches corrupt streams that still
look valid by size alone.

## Bilibili Notes

The three Bilibili videos currently downloaded are:

- `BV1gT4y1m7ec`: 八段锦, `852x480`, about 75 MiB
- `BV1sF411F7Tg`: 易筋经, `852x480`, about 18 MiB
- `BV1J3411s7Ph`: 五禽戏, `852x480`, about 25 MiB

Unauthenticated Bilibili API calls exposed 480p and 360p stream URLs. The API
listed 720p/1080p as available, but did not return those stream URLs without
additional authenticated context. If higher quality is needed later, resolve
fresh media URLs using the saved BVID/AID/CID in `bilibili/manifest.json`,
ideally with browser cookies or an authenticated downloader.

Bilibili media URLs expire. Do not commit or rely on transient `playurl`
responses; treat BVID/AID/CID as the stable re-download identifiers.

The project-owned Bilibili helper uses `yt-dlp` to resolve fresh media from the
stable BVID page URLs:

```bash
PYTHONPATH=src python -m neodojo bilibili download --quality 480p --dry-run --out outputs/bilibili-download
PYTHONPATH=src python -m neodojo bilibili download --routine baduanjin --quality best --cookies-from-browser chrome --out outputs/bilibili-download
```

Authenticated cookies may be required for higher-quality Bilibili streams. The
download report records stable metadata and commands only; it does not preserve
transient media URLs. When downloads run, the helper validates each MP4 with
`ffprobe` and an `ffmpeg -xerror` decode smoke.

## Routine Phase Clips

`bilibili/routines.json` is the canonical manual phase manifest for the three
tracked Bilibili routines. Each phase has `name_zh`, `name_en`,
`start_seconds`, `end_seconds`, and `selection_rule: first_demo_only`.

Dry-run or materialize local phase clips and GPU handoffs:

```bash
PYTHONPATH=src python -m neodojo routine split \
  --routine baduanjin \
  --source-video video/bilibili/01_baduanjin-complete-routine-with-breathing-cues.mp4 \
  --dry-run \
  --out outputs/routines/baduanjin/source

PYTHONPATH=src python -m neodojo routine prepare-gpu-runs \
  --routine baduanjin \
  --clips outputs/routines/baduanjin/source \
  --out outputs/routines/baduanjin/gvhmr-runs

PYTHONPATH=src python -m neodojo routine assemble \
  --routine baduanjin \
  --source-materializations outputs/routines/baduanjin/source \
  --gvhmr-json-root outputs/routines/baduanjin/gvhmr-runs \
  --gmr-json-root outputs/routines/baduanjin/gmr-json \
  --out outputs/routines/baduanjin/html
```

Remove `--dry-run` after the source MP4 is downloaded and `ffmpeg` is available
to write actual ignored phase clips under `outputs/`.

The routine HTML is local-only and fail-closed: missing GVHMR, GMR, or render
artifacts are shown as missing, while SMPL-X remains the teaching/scoring
source and G1 remains visual-only.

## Official Shenzhen Source Notes

Use the index to choose originals:

```bash
python3 - <<'PY'
import csv
rows = list(csv.DictReader(open('video/original_videos.csv', encoding='utf-8')))
for r in sorted(rows, key=lambda x: float(x['source_size_mib']))[:20]:
    print(r['category_order'], r['item_order'], r['source_size_mib'], r['resolution'], r['article_title_chinese'])
PY
```

Download one official original:

```bash
./video/download_originals.py --id 03-001
```

Download a bounded set:

```bash
./video/download_originals.py --all --max-total-mib 300 --dry-run
```

Use `--dry-run` first because the complete official source set is several GiB.
