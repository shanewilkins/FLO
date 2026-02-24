"""FLO package public surface.

Keep the package import lightweight: importing the top-level package should
not import CLI-related heavy dependencies (like `click`). Import the CLI
entrypoint explicitly (``from flo import cli`` or ``import flo.cli``) where
needed instead of exposing it at package import time.
"""

from __future__ import annotations

__all__: list[str] = []

