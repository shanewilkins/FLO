"""Check FLO's existing MPI palette against a supplied pinned producer checkout."""

from __future__ import annotations

import argparse
import csv
import json
import tomllib
from pathlib import Path

from flo.render.mpi_palette import MPI_COLORS, MPI_FONT_FAMILY, MPI_THEME_VERSION


def check_palette(producer_root: Path) -> None:
    """Fail on version or shared-token drift, without importing producer code."""
    project = tomllib.loads((producer_root / "pyproject.toml").read_text())["project"]
    if project["name"] != "mpi-theme" or project["version"] != MPI_THEME_VERSION:
        raise ValueError(f"Expected mpi-theme {MPI_THEME_VERSION}")
    tokens = json.loads((producer_root / "mpi_theme/assets/tokens.json").read_text())
    for name, expected in MPI_COLORS.items():
        actual = tokens.get(f"--mpi-{name}")
        if not isinstance(actual, str) or actual.upper() != expected:
            raise ValueError(f"MPI token drift: --mpi-{name}: {actual!r} != {expected}")
    font = next(
        csv.reader([tokens.get("--mpi-font-heading", "")], skipinitialspace=True)
    )
    if tuple(font) != MPI_FONT_FAMILY:
        raise ValueError("MPI token drift: --mpi-font-heading")


def main() -> None:
    """Check an explicit producer source; ordinary FLO installs need no peer repo."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--producer-root", type=Path, required=True)
    args = parser.parse_args()
    check_palette(args.producer_root)
    print(f"MPI palette matches mpi-theme {MPI_THEME_VERSION}")


if __name__ == "__main__":
    main()
