#!/bin/bash
# Daily Rhino Finance video analysis
# Usage: ./scripts/daily_rhino.sh [output_dir]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="${1:-$PROJECT_DIR/output}"
DATE=$(date +%Y-%m-%d)

mkdir -p "$OUTPUT_DIR"

echo "[$(date)] Starting daily Rhino Finance analysis..."

# Run analysis
python3 "$SCRIPT_DIR/analyze.py" \
  --channel "https://www.youtube.com/@RhinoFinance" \
  -o "$OUTPUT_DIR/${DATE}_rhino_summary.md" \
  2>&1 | tee "$OUTPUT_DIR/${DATE}_rhino.log"

echo "[$(date)] Done. Summary saved to $OUTPUT_DIR/${DATE}_rhino_summary.md"
