#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REF_DIR="$REPO_ROOT/examples/reference"
OUT_DIR="$REPO_ROOT/renders/reference"

mkdir -p "$OUT_DIR"

build_svg() {
  local input_rel="$1"
  local output_rel="$2"
  shift 2

  local input="$REPO_ROOT/$input_rel"
  local output="$REPO_ROOT/$output_rel"

  uv run flo run "$input" --export svg --render-backend svg --render-to "$output" "$@"
  echo "Built: $output_rel"
}

build_text_export() {
  local input_rel="$1"
  local output_rel="$2"

  local input="$REPO_ROOT/$input_rel"
  local output="$REPO_ROOT/$output_rel"

  uv run flo run "$input" --export ingredients -o "$output"
  echo "Built: $output_rel"
}

# Canonical reference renders.
build_svg "examples/reference/bakery_setup_vs_queue.flo" "renders/reference/bakery_setup_vs_queue.svg" --diagram sppm --orientation lr
build_svg "examples/reference/chocolate_chip_cookies.flo" "renders/reference/chocolate_chip_cookies.svg" --diagram flowchart
build_svg "examples/reference/chocolate_chip_cookies.flo" "renders/reference/chocolate_chip_cookies_topdown.svg" --diagram flowchart --orientation tb
build_svg "examples/reference/chocolate_chip_cookies.flo" "renders/reference/chocolate_chip_cookies_spaghetti.svg" --diagram spaghetti
build_text_export "examples/reference/chocolate_chip_cookies.flo" "renders/reference/chocolate_chip_cookies_ingredients.md"
build_svg "examples/reference/linear.flo" "renders/reference/linear.svg" --diagram sppm --orientation lr
build_svg "examples/reference/linear.flo" "renders/reference/linear_elk_flowchart.svg" --diagram flowchart --render-backend svg
build_svg "examples/reference/rework_loop.flo" "renders/reference/rework_loop.svg" --diagram sppm --orientation lr
build_svg "examples/reference/sppm_feature_showcase.flo" "renders/reference/sppm_feature_showcase.svg" --diagram sppm --orientation lr
build_svg "examples/reference/sppm_feature_showcase.flo" "renders/reference/sppm_feature_showcase_elk.svg" --diagram sppm --render-backend svg
build_svg "examples/reference/sppm_feature_showcase_wrapped.flo" "renders/reference/sppm_feature_showcase_wrapped.svg" --diagram sppm --orientation lr --layout-wrap auto --layout-target-columns 3 --publication-page-format letter
build_svg "examples/reference/sppm_long_label_stress.flo" "renders/reference/sppm_long_label_stress.svg" --diagram sppm --orientation lr
# TODO: Re-enable once direct SVG backend supports swimlane rendering.
# build_svg "examples/reference/swimlane.flo" "renders/reference/swimlane.svg" --diagram swimlane
build_svg "examples/reference/washnfold.flo" "renders/reference/washnfold.svg" --diagram sppm --orientation lr
build_svg "examples/reference/washnfold.flo" "renders/reference/washnfold_sppm_wrap800.svg" --diagram sppm --orientation lr --layout-wrap auto --layout-max-width-px 800

echo "Done: reference artifacts built in $OUT_DIR"
