"""I/O helpers placed under the `services` layer.

This module provides `read_input` and `write_output` and is the
canonical location for IO code in the services layer.
"""
from __future__ import annotations

import sys
from typing import Tuple

from flo.services.errors import EXIT_RENDER_ERROR


def read_input(path: str) -> Tuple[int, str, str]:
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
    try:
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(out)
        else:
            print(out)
    except OSError as e:
        return EXIT_RENDER_ERROR, f"I/O error writing {path}: {e}"
    return 0, ""
