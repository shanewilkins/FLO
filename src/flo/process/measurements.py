"""Plain-value helpers for validated measurement profiles."""

from __future__ import annotations

from typing import Any


def selected_result(
    measurement: object, selector: str = "analysis_input"
) -> dict[str, Any] | None:
    """Return the named result selected by a validated measurement profile."""
    if not isinstance(measurement, dict) or "ref" in measurement:
        return None
    result_name = measurement.get(selector)
    results = measurement.get("results")
    if not isinstance(result_name, str) or not isinstance(results, dict):
        return None
    result = results.get(result_name)
    return result if isinstance(result, dict) else None


def measurement_reference(measurement: object) -> tuple[str, str] | None:
    """Split a validated ``step.field`` measurement reference."""
    if not isinstance(measurement, dict):
        return None
    raw = measurement.get("ref")
    if not isinstance(raw, str) or "." not in raw:
        return None
    node_id, field = raw.rsplit(".", 1)
    return (node_id, field)


__all__ = ["measurement_reference", "selected_result"]
