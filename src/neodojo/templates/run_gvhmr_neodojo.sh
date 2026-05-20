#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Run GVHMR and export a neodojo GVHMR SMPL-X JSON artifact.

Run this inside a copied neodojo GPU input bundle on a CUDA machine.

Usage:
  ./run_gvhmr_neodojo.sh [--install] [--skip-gvhmr] [--skip-export]

Important environment variables:
  GVHMR_REPO        Local GVHMR checkout. Default: ./GVHMR inside the bundle.
  GVHMR_REMOTE      GVHMR git remote. Default: https://github.com/zju3dv/GVHMR.git
  GVHMR_REV         GVHMR revision to checkout when --install is used. Default: main.
  VIDEO             Trimmed clip path. Default: ./source/trimmed-clip.mp4.
  OUTPUT_ROOT       GVHMR output root. Default: ./gvhmr-output.
  SMPLX_MODEL_DIR   Required for export; local licensed SMPL-X body_models root,
                    nested smplx directory, or direct SMPLX_NEUTRAL.npz path.
  HMR4D_RESULTS     Existing result path when --skip-gvhmr is used.
  RETURNED_EXPORT   Output neodojo JSON path. Default: ./gvhmr-smplx-joints.json.
  STATIC_CAM        1 adds GVHMR -s / --static_cam. Default: 1.
  USE_DPVO          1 adds GVHMR --use_dpvo. Default: 0.
  F_MM              Optional GVHMR --f_mm focal length.
  PARAMETER_BLOCK   GVHMR parameter block for export. Default: smpl_params_global.
  FPS               Export fps. Default: detected from VIDEO with ffprobe;
                    falls back to 30 when detection is unavailable.
  ROUTINE           Export routine label. Default: Baduanjin.
  FORM              Export form label. Default: Two Hands Hold Up the Heavens.
  RUNTIME           Runtime provenance string.
  UPSTREAM_VERSION  GVHMR provenance string.
  NEODOJO_DRY_RUN   1 prints commands without running them.

The script never downloads SMPL-X assets. Put licensed SMPL-X assets in your
own local directory and pass SMPLX_MODEL_DIR.
EOF
}

INSTALL=0
RUN_GVHMR=1
RUN_EXPORT=1
for arg in "$@"; do
  case "$arg" in
    --install)
      INSTALL=1
      ;;
    --skip-gvhmr)
      RUN_GVHMR=0
      ;;
    --skip-export)
      RUN_EXPORT=0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $arg" >&2
      usage >&2
      exit 2
      ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GVHMR_REMOTE="${GVHMR_REMOTE:-https://github.com/zju3dv/GVHMR.git}"
GVHMR_REV="${GVHMR_REV:-main}"
GVHMR_REPO="${GVHMR_REPO:-$ROOT_DIR/GVHMR}"
VIDEO="${VIDEO:-$ROOT_DIR/source/trimmed-clip.mp4}"
OUTPUT_ROOT="${OUTPUT_ROOT:-$ROOT_DIR/gvhmr-output}"
VIDEO_BASENAME="$(basename "$VIDEO")"
VIDEO_STEM="${VIDEO_BASENAME%.*}"
HMR4D_RESULTS="${HMR4D_RESULTS:-$OUTPUT_ROOT/$VIDEO_STEM/hmr4d_results.pt}"
RETURNED_EXPORT="${RETURNED_EXPORT:-$ROOT_DIR/gvhmr-smplx-joints.json}"
SMPLX_MODEL_DIR="${SMPLX_MODEL_DIR:-}"
STATIC_CAM="${STATIC_CAM:-1}"
USE_DPVO="${USE_DPVO:-0}"
F_MM="${F_MM:-}"
PARAMETER_BLOCK="${PARAMETER_BLOCK:-smpl_params_global}"
FPS="${FPS:-}"
ROUTINE="${ROUTINE:-Baduanjin}"
FORM="${FORM:-Two Hands Hold Up the Heavens}"
RUNTIME="${RUNTIME:-$(uname -a)}"
UPSTREAM_VERSION="${UPSTREAM_VERSION:-$GVHMR_REV}"
NEODOJO_DRY_RUN="${NEODOJO_DRY_RUN:-0}"
GPU_COMMAND_TEXT=""

detect_video_fps() {
  local video_path="$1"
  local rate
  if ! command -v ffprobe >/dev/null 2>&1 || [[ ! -f "$video_path" ]]; then
    return 0
  fi
  rate="$(
    ffprobe -v error -select_streams v:0 \
      -show_entries stream=avg_frame_rate \
      -of default=noprint_wrappers=1:nokey=1 "$video_path" 2>/dev/null \
      | head -n 1
  )"
  if [[ -z "$rate" || "$rate" == "0/0" ]]; then
    return 0
  fi
  awk -v rate="$rate" 'BEGIN {
    split(rate, parts, "/")
    if (length(parts[2]) > 0) {
      if (parts[2] + 0 > 0) {
        printf "%.6f", (parts[1] + 0) / (parts[2] + 0)
      }
    } else if (parts[1] + 0 > 0) {
      printf "%.6f", parts[1] + 0
    }
  }'
}

if [[ -z "$FPS" ]]; then
  FPS="$(detect_video_fps "$VIDEO" || true)"
fi
FPS="${FPS:-30}"

run_cmd() {
  printf '+'
  printf ' %q' "$@"
  printf '\n'
  if [[ "$NEODOJO_DRY_RUN" != "1" ]]; then
    "$@"
  fi
}

require_file() {
  local path="$1"
  local label="$2"
  if [[ ! -f "$path" ]]; then
    echo "missing $label: $path" >&2
    exit 2
  fi
}

require_dir() {
  local path="$1"
  local label="$2"
  if [[ ! -d "$path" ]]; then
    echo "missing $label: $path" >&2
    exit 2
  fi
}

require_path() {
  local path="$1"
  local label="$2"
  if [[ ! -e "$path" ]]; then
    echo "missing $label: $path" >&2
    exit 2
  fi
}

if [[ "$INSTALL" == "1" ]]; then
  if [[ ! -d "$GVHMR_REPO/.git" ]]; then
    run_cmd git clone "$GVHMR_REMOTE" "$GVHMR_REPO"
  fi
  run_cmd git -C "$GVHMR_REPO" fetch --tags --depth 1 origin "$GVHMR_REV"
  run_cmd git -C "$GVHMR_REPO" checkout "$GVHMR_REV"
  run_cmd python -m pip install -r "$GVHMR_REPO/requirements.txt"
  run_cmd python -m pip install -e "$GVHMR_REPO"
fi

if [[ "$RUN_GVHMR" == "1" ]]; then
  require_file "$VIDEO" "trimmed source clip"
  require_file "$GVHMR_REPO/tools/demo/demo.py" "GVHMR demo.py; set GVHMR_REPO or run with --install"

  gvhmr_cmd=(python tools/demo/demo.py --video "$VIDEO" --output_root "$OUTPUT_ROOT")
  if [[ "$STATIC_CAM" == "1" ]]; then
    gvhmr_cmd+=(-s)
  fi
  if [[ "$USE_DPVO" == "1" ]]; then
    gvhmr_cmd+=(--use_dpvo)
  fi
  if [[ -n "$F_MM" ]]; then
    gvhmr_cmd+=(--f_mm "$F_MM")
  fi
  GPU_COMMAND_TEXT="$(printf '%q ' "${gvhmr_cmd[@]}")"
  (
    cd "$GVHMR_REPO"
    run_cmd "${gvhmr_cmd[@]}"
  )
fi

if [[ "$RUN_EXPORT" == "1" ]]; then
  if [[ -z "$SMPLX_MODEL_DIR" ]]; then
    echo "SMPLX_MODEL_DIR is required for neodojo export" >&2
    exit 2
  fi
  require_path "$SMPLX_MODEL_DIR" "licensed SMPL-X model path"
  require_file "$HMR4D_RESULTS" "GVHMR hmr4d_results.pt"
  require_file "$ROOT_DIR/export_neodojo_gvhmr.py" "neodojo GVHMR exporter"
  require_file "$ROOT_DIR/gvhmr-smplx-joints.template.json" "neodojo export template"
  require_file "$ROOT_DIR/source-materialization.json" "source materialization manifest"

  export_cmd=(
    python "$ROOT_DIR/export_neodojo_gvhmr.py"
    --hmr4d-results "$HMR4D_RESULTS"
    --smplx-model-dir "$SMPLX_MODEL_DIR"
    --template "$ROOT_DIR/gvhmr-smplx-joints.template.json"
    --source-materialization "$ROOT_DIR/source-materialization.json"
    --out "$RETURNED_EXPORT"
    --parameter-block "$PARAMETER_BLOCK"
    --fps "$FPS"
    --routine "$ROUTINE"
    --form "$FORM"
    --runtime "$RUNTIME"
    --upstream-version "$UPSTREAM_VERSION"
    --gpu-command "${GPU_COMMAND_TEXT:-python tools/demo/demo.py --video $VIDEO --output_root $OUTPUT_ROOT}"
  )
  run_cmd "${export_cmd[@]}"
fi

echo "neodojo GPU run complete"
echo "GVHMR result: $HMR4D_RESULTS"
echo "Returned export: $RETURNED_EXPORT"
