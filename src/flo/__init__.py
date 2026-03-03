"""FLO package public surface.

Keep the package import lightweight: importing the top-level package should
not import CLI-related heavy dependencies (like `click`). Use the console
entrypoint (`flo`) or import from `flo.core.cli` explicitly where needed,
instead of exposing CLI modules at package import time.
"""

from __future__ import annotations

__all__: list[str] = []

