"""SPPM metadata field schema and extraction helpers.

This module centralizes metadata field definitions and provides safe accessor
functions to avoid duplicating schema knowledge across rendering helpers.

It ensures that metadata field access patterns are consistent and that
adding new fields requires updates in one place only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = [
    "SppmMetadataValue",
    "get_metadata_value_class",
    "get_metadata_wait_time_minutes",
    "get_metadata_cycle_time",
    "get_metadata_crossover_time",
    "get_metadata_changeover_time",
    "get_metadata_description",
    "get_metadata_field",
]


@dataclass(frozen=True)
class SppmMetadataValue:
    """Typed wrapper for a metadata value spec with value and optional unit."""

    value: Any
    unit: str | None = None

    @property
    def numeric_value(self) -> float:
        """Return numeric value, defaulting to 0 if invalid."""
        try:
            return float(self.value) if self.value is not None else 0.0
        except ValueError, TypeError:
            return 0.0


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
    """Parse a time spec dict into SppmMetadataValue, or None if invalid."""
    if not isinstance(time_spec, dict):
        return None
    value = time_spec.get("value")
    unit = time_spec.get("unit", "min")
    return SppmMetadataValue(value=value, unit=unit)


def get_metadata_wait_time_minutes(metadata: dict[str, Any] | None) -> Any:
    """Extract wait_time (queue delay) from metadata, defaulting to 0.

    Wait time represents queue/idle delay caused by unavailability of the next
    resource or step. This is distinct from changeover/setup time, which is
    reconfiguration time within a step itself.

    Returns the raw numeric value (int or float) to preserve formatting,
    or 0 if absent/invalid.
    """
    time_spec = get_metadata_field(metadata, "wait_time", expected_type=dict)
    if not isinstance(time_spec, dict):
        return 0
    value = time_spec.get("value")
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return value
    return 0


def get_metadata_cycle_time(
    metadata: dict[str, Any] | None,
) -> SppmMetadataValue | None:
    """Extract cycle_time from metadata as SppmMetadataValue, or None if absent."""
    time_spec = get_metadata_field(metadata, "cycle_time", expected_type=dict)
    return _parse_time_spec(time_spec)


def get_metadata_crossover_time(
    metadata: dict[str, Any] | None,
) -> SppmMetadataValue | None:
    """Extract changeover/setup time using canonical precedence.

    Changeover time represents setup/reconfiguration time required to transition
    a step to the next product, batch, or mode. This is distinct from wait time
    (queue delay), which is caused by unavailability of resources.

    Precedence order for metadata field lookup:
    1. ``crossover_time`` (preferred)
    2. ``transfer_time``
    3. ``changeover_time`` (legacy alias)

    Note: The distinction between wait time and changeover time is pedagogically
    important. Both are non-value-adding, but they have different root causes
    and solutions: queues are solved by scheduling/pull; setup is solved by
    standardization/SMED.
    """
    for field_name in ("crossover_time", "transfer_time", "changeover_time"):
        time_spec = get_metadata_field(metadata, field_name, expected_type=dict)
        parsed = _parse_time_spec(time_spec)
        if parsed is not None:
            return parsed
    return None


def get_metadata_changeover_time(
    metadata: dict[str, Any] | None,
) -> SppmMetadataValue | None:
    """Backward-compatible alias for crossover/transfer/changeover time extraction.

    This function delegates to get_metadata_crossover_time() for compatibility.
    Prefer get_metadata_crossover_time() in new code.
    """
    return get_metadata_crossover_time(metadata)


def get_metadata_description(metadata: dict[str, Any] | None) -> str:
    """Extract description from metadata, defaulting to empty string."""
    desc = get_metadata_field(metadata, "description", expected_type=str)
    return desc or ""
