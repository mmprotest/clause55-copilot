#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/out/sample"

mkdir -p "$OUT_DIR"

c55 run \
  --site "$ROOT_DIR/src/c55copilot/assets/samples/site_fitzroy.json" \
  --massing "$ROOT_DIR/src/c55copilot/assets/samples/massing_two_townhouses.json" \
  --property "$ROOT_DIR/src/c55copilot/assets/samples/property_report_mock.json" \
  --out "$OUT_DIR"

cp "$ROOT_DIR/src/c55copilot/assets/samples/report_sample.svg" "$OUT_DIR/report_preview.svg"

echo "Sample pack generated in $OUT_DIR"
