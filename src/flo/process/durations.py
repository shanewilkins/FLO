"""Shared scalar-duration checks for validation, analysis, and presentation."""

from __future__ import annotations

from math import isfinite

SECONDS_PER_UNIT = {"s": 1.0, "m": 60.0, "min": 60.0, "hr": 3600.0, "d": 86400.0}


def duration_number(value: object) -> float | None:
    """Accept finite nonnegative numbers, excluding booleans and numeric text."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except OverflowError:
        return None
    return number if isfinite(number) and number >= 0 else None


def duration_seconds(raw: object) -> float | None:
    """Normalize an explicit value/unit pair without supplying missing data."""
    if not isinstance(raw, dict):
        return None
    value = duration_number(raw.get("value"))
    unit = raw.get("unit")
    if value is None or not isinstance(unit, str):
        return None
    factor = SECONDS_PER_UNIT.get(unit.strip().lower())
    if factor is None:
        return None
    seconds = value * factor
    return seconds if isfinite(seconds) else None
