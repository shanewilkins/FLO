"""Build or verify the deterministic White Belt wash-and-fold book SVG."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile

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

    if args.check:
        if not output.is_file():
            raise SystemExit(f"White Belt book asset is missing: {output}")
        if output.read_bytes() != generated_bytes:
            raise SystemExit(
                f"White Belt book asset differs from the generated artifact: {output}"
            )
        action = "Verified"
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(committed_svg, output)
        action = "Built"

    digest = hashlib.sha256(generated_bytes).hexdigest()
    print(f"{action}: {output}")
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
