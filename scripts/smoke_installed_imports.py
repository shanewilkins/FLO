#!/usr/bin/env python3
"""Import every installed FLO module from a clean distribution environment."""

from __future__ import annotations

import importlib
import pkgutil

import flo


def main() -> int:
    """Import the complete installed package and report a stable module count."""
    module_names = sorted(
        module.name
        for module in pkgutil.walk_packages(flo.__path__, prefix=f"{flo.__name__}.")
    )
    failures: list[tuple[str, str]] = []
    for module_name in module_names:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - exercised in clean CI smoke
            failures.append((module_name, f"{type(exc).__name__}: {exc}"))

    if failures:
        for module_name, message in failures:
            print(f"FAILED {module_name}: {message}")
        return 1

    print(f"Imported {len(module_names)} installed FLO modules successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
