"""Supported spatial units and the Pint conversion boundary for movement analysis."""

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pint import UnitRegistry

SPATIAL_UNITS = frozenset({"mm", "cm", "m", "in", "ft"})


@cache
def _registry() -> UnitRegistry:
    from pint import UnitRegistry

    return UnitRegistry()


def length_in_metres(value: float, unit: str) -> float:
    """Convert a supported authored length without broadening FLO's unit grammar."""
    if unit not in SPATIAL_UNITS:
        raise ValueError(f"Unsupported spatial unit: {unit}")
    return float(_registry().Quantity(value, unit).to("m").magnitude)
