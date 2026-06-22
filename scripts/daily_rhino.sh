#!/bin/bash
# Daily Rhino Finance video analysis
# Usage: ./scripts/daily_rhino.sh [output_dir]
#
# Ensures dependencies are installed before running.
# Safe to run from cron/launchd (minimal PATH).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="${1:-$PROJECT_DIR/output}"
DATE=$(date +%Y-%m-%d)

mkdir -p "$OUTPUT_DIR"

# ---- Ensure dependencies ----
echo "[$(date)] Checking dependencies..."

# yt-dlp
if ! command -v yt-dlp &>/dev/null; then
    echo "Installing yt-dlp..."
    python3 -m pip install --user --quiet yt-dlp 2>/dev/null || pip3 install --quiet yt-dlp
fi

# youtube-transcript-api
if ! python3 -c "import youtube_transcript_api" 2>/dev/null; then
    echo "Installing youtube-transcript-api..."
    python3 -m pip install --user --quiet youtube-transcript-api 2>/dev/null || pip3 install --quiet youtube-transcript-api
fi

# ffmpeg (warn only, can't auto-install)
if ! command -v ffmpeg &>/dev/null; then
    echo "WARNING: ffmpeg not found. Frame extraction will be skipped."
    echo "Install with: brew install ffmpeg"
fi

# ---- Run analysis ----
echo "[$(date)] Starting daily Rhino Finance analysis..."

python3 "$SCRIPT_DIR/analyze.py" \
  --channel "https://www.youtube.com/@RhinoFinance" \
  -o "$OUTPUT_DIR/${DATE}_rhino_summary.md" \
  2>&1 | tee "$OUTPUT_DIR/${DATE}_rhino.log"

echo "[$(date)] Done. Summary saved to $OUTPUT_DIR/${DATE}_rhino_summary.md"
