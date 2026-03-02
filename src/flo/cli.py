"""Compatibility CLI entrypoint for package scripts.

This module preserves the historical `flo.cli:main` entrypoint while the
implementation lives under `flo.core.cli`.
"""

from __future__ import annotations

from flo.core.cli import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
