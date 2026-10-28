"""SPPM metadata field schema and extraction helpers.

This module centralizes metadata field definitions and provides safe accessor
functions to avoid duplicating schema knowledge across rendering helpers.

It ensures that metadata field access patterns are consistent and that
adding new fields requires updates in one place only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flo.process.durations import duration_number, duration_seconds
from flo.process.measurements import selected_result
from flo.process.units import convert_duration

__all__ = [
    "SppmMetadataValue",
    "get_metadata_changeover_time",
    "get_metadata_cycle_time",
    "get_metadata_description",
    "get_metadata_field",
    "get_metadata_value_class",
    "get_metadata_wait_time_minutes",
]


@dataclass(frozen=True)
class SppmMetadataValue:
    """Typed wrapper for a metadata value spec with value and optional unit."""

    value: Any
    unit: str | None = None

    @property
    def numeric_value(self) -> float | None:
        """Return a finite duration value, preserving invalid or missing as None."""
        if duration_seconds({"value": self.value, "unit": self.unit}) is None:
            return None
        return duration_number(self.value)


def get_metadata_field(
    metadata: dict[str, Any] | None,
    field_name: str,
    *,
    expected_type: type | None = None,
) -> Any:
    """Safely extract a metadata field by name with optional type checking.

    Args:
        metadata: The metadata dict (may be None).
        field_name: The field name to extract.
        expected_type: If provided, validate the extracted value is this type.

    Returns:
        The field value if present and type-correct, None otherwise.
    """
    if not isinstance(metadata, dict):
        return None
    value = metadata.get(field_name)
    if expected_type is not None and not isinstance(value, expected_type):
        return None
    return value


def get_metadata_value_class(metadata: dict[str, Any] | None) -> str | None:
    """Extract value_class field from metadata.

    Returns:
        String value_class, or None if absent/invalid.
    """
    return get_metadata_field(metadata, "value_class", expected_type=str)


def _parse_time_spec(time_spec: Any) -> SppmMetadataValue | None:
    """Parse a profile's primary result into a renderable duration."""
    result = selected_result(time_spec, "primary")
    if result is None or duration_seconds(result) is None:
        return None
    return SppmMetadataValue(value=result["value"], unit=result["unit"])


def get_metadata_wait_time_minutes(
    metadata: dict[str, Any] | None,
) -> int | float | None:
    """Extract the primary waiting result normalized to minutes."""
    if not isinstance(metadata, dict):
        return None
    seconds = duration_seconds(selected_result(metadata.get("wait_time"), "primary"))
    return None if seconds is None else convert_duration(seconds, "s", "min")


def get_metadata_cycle_time(
    metadata: dict[str, Any] | None,
) -> SppmMetadataValue | None:
    """Extract cycle_time from metadata as SppmMetadataValue, or None if absent."""
    time_spec = get_metadata_field(metadata, "cycle_time", expected_type=dict)
    return _parse_time_spec(time_spec)


def get_metadata_changeover_time(
    metadata: dict[str, Any] | None,
) -> SppmMetadataValue | None:
    """Extract the primary changeover-time result."""
    time_spec = get_metadata_field(metadata, "changeover_time", expected_type=dict)
    return _parse_time_spec(time_spec)


def get_metadata_description(metadata: dict[str, Any] | None) -> str:
    """Extract description from metadata, defaulting to empty string."""
    desc = get_metadata_field(metadata, "description", expected_type=str)
    return desc or ""
