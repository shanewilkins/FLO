"""Supported FLO units and the shared lazy Pint conversion boundary."""

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pint import UnitRegistry

SPATIAL_UNITS = frozenset({"mm", "cm", "m", "in", "ft"})
_DURATION_UNIT_NAMES = {
    "s": "second",
    "m": "minute",
    "min": "minute",
    "hr": "hour",
    "d": "day",
}
DURATION_UNITS = frozenset(_DURATION_UNIT_NAMES)


@cache
def _registry() -> UnitRegistry:
    from pint import UnitRegistry

    return UnitRegistry()


def length_in_metres(value: float, unit: str) -> float:
    """Convert a supported authored length without broadening FLO's unit grammar."""
    if unit not in SPATIAL_UNITS:
        raise ValueError(f"Unsupported spatial unit: {unit}")
    return float(_registry().Quantity(value, unit).to("m").magnitude)


def convert_duration(value: float, source_unit: str, target_unit: str) -> float:
    """Convert only FLO duration units, interpreting duration ``m`` as minutes."""
    source = source_unit.strip().lower()
    target = target_unit.strip().lower()
    for unit in (source, target):
        if unit not in DURATION_UNITS:
            raise ValueError(f"Unsupported duration unit: {unit}")
    return float(
        _registry()
        .Quantity(value, _DURATION_UNIT_NAMES[source])
        .to(_DURATION_UNIT_NAMES[target])
        .magnitude
    )
