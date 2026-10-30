"""Shared identity rules for authored and canonical declarations."""

from typing import Any

from .validation_errors import LocatedValidationError


def validate_lane_ids(lanes: list[dict[str, Any]] | None) -> None:
    """Reject a repeated lane identity at its second declaration."""
    if not isinstance(lanes, list):
        return  # Local boundary validation owns collection shape.
    seen: set[str] = set()
    for index, lane in enumerate(lanes):
        lane_id = lane.get("id") if isinstance(lane, dict) else None
        if not isinstance(lane_id, str):
            continue  # Local boundary validation owns malformed lane shapes.
        if lane_id in seen:
            raise LocatedValidationError(
                f"E1035: duplicate lane id '{lane_id}'",
                ("lanes", index, "id"),
            )
        seen.add(lane_id)
