"""Build or verify the deterministic White Belt wash-and-fold book SVG."""

from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_sppm_baseline_artifacts import (  # noqa: E402
    DEFAULT_MANIFEST,
    DEFAULT_OUTDIR,
    _build_case,
    _filter_cases,
    _load_cases,
    _resolve_repo_path,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CASE_ID = "washnfold_white_belt"
DEFAULT_OUTPUT = REPO_ROOT / "renders" / "reference" / "washnfold_white_belt.svg"
SVG_BACKGROUND = b'<rect width="100%" height="100%" fill="#fffdf8" />\n'


def main() -> int:
    """Regenerate the canonical case, then copy or verify the requested asset."""
    parser = argparse.ArgumentParser(prog="build_white_belt_book_artifact.py")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Book asset path to write or verify.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that --output is byte-identical instead of writing it.",
    )
    parser.add_argument(
        "--transparent",
        action="store_true",
        help="Remove the page background from the generated book SVG.",
    )
    args = parser.parse_args()

    output = args.output.resolve()
    case = _filter_cases(
        _load_cases(_resolve_repo_path(DEFAULT_MANIFEST)), case_ids=[CASE_ID]
    )[0]
    committed_svg = _resolve_repo_path(DEFAULT_OUTDIR) / CASE_ID / "render.svg"
    if not committed_svg.is_file():
        raise FileNotFoundError(f"Committed White Belt SVG is missing: {committed_svg}")

    with tempfile.TemporaryDirectory(prefix="flo-white-belt-") as temp_dir:
        generated_root = Path(temp_dir) / "generated"
        _build_case(case=case, outdir=generated_root)
        generated_svg = generated_root / CASE_ID / "render.svg"
        generated_bytes = generated_svg.read_bytes()

    committed_bytes = committed_svg.read_bytes()
    if generated_bytes != committed_bytes:
        raise SystemExit(
            "White Belt golden drift detected; regenerate and review the SPPM baseline."
        )

    output_bytes = (
        _without_background(generated_bytes) if args.transparent else generated_bytes
    )

    if args.check:
        if not output.is_file():
            raise SystemExit(f"White Belt book asset is missing: {output}")
        if output.read_bytes() != output_bytes:
            raise SystemExit(
                f"White Belt book asset differs from the generated artifact: {output}"
            )
        action = "Verified"
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(output_bytes)
        action = "Built"

    digest = hashlib.sha256(output_bytes).hexdigest()
    print(f"{action}: {output}")
    print(f"SHA-256: {digest}")
    return 0


def _without_background(svg_bytes: bytes) -> bytes:
    """Remove the renderer's single page-covering background rectangle."""
    if svg_bytes.count(SVG_BACKGROUND) != 1:
        raise ValueError("Expected exactly one White Belt SVG background rectangle")
    return svg_bytes.replace(SVG_BACKGROUND, b"", 1)


if __name__ == "__main__":
    raise SystemExit(main())
