#!/usr/bin/env python3
"""Report the current SPPM refactor baseline.

This wrapper keeps the reusable implementation in `src/flo/core/` while
providing a simple script entrypoint for issue tracking and local reuse.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def main(argv: list[str]) -> int:
    """Run the reusable SPPM baseline reporter."""
    from flo.core._sppm_refactor_baseline import main as run_main

    return run_main(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
