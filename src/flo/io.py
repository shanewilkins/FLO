"""I/O helpers: read input from file or stdin and write output."""

from __future__ import annotations

import sys
from typing import Tuple

from flo.services.errors import EXIT_RENDER_ERROR


def read_input(path: str) -> Tuple[int, str, str]:
    """Read content from `path` or stdin when `path` == '-'.

    Returns a tuple `(rc, content, err)` where `rc` is non-zero on error
    and `err` contains a human-readable message.
    """
    try:
        if path == "-":
            content = sys.stdin.read()
        else:
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
    except OSError as e:
        return EXIT_RENDER_ERROR, "", f"I/O error reading {path}: {e}"
    return 0, content, ""


def write_output(out: str, path: str | None) -> Tuple[int, str]:
    """Write `out` to `path` or stdout when `path` is None.

    Returns `(rc, err)` where `rc` is non-zero on I/O error.
    """
    try:
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(out)
        else:
            print(out)
    except OSError as e:
        return EXIT_RENDER_ERROR, f"I/O error writing {path}: {e}"
    return 0, ""
