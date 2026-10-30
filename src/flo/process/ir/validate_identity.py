"""Transition-record and declared-lane identity validation."""

from dataclasses import asdict
from typing import Any

from flo.process.identity import validate_lane_ids

from .models import IR
from .validation_errors import _LocatedValidationError


def validate_graph_identity(process: IR) -> None:
    """Preserve all transitions and reject duplicate identity or full content."""
    validate_lane_ids(process.lanes)
    seen_ids: set[str] = set()
    records: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for index, edge in enumerate(process.edges):
        if isinstance(edge.id, str):
            if edge.id in seen_ids:
                raise _LocatedValidationError(
                    f"E1034: duplicate transition id '{edge.id}'",
                    ("edges", index, "id"),
                )
            seen_ids.add(edge.id)
        record = asdict(edge)
        candidates = records.setdefault((edge.source, edge.target), [])
        if any(_same_record(record, previous) for previous in candidates):
            raise _LocatedValidationError(
                f"E1033: duplicate transition '{edge.source}' -> '{edge.target}'",
                ("edges", index),
            )
        candidates.append(record)


def _same_record(left: Any, right: Any) -> bool:
    """Compare unordered mappings without conflating Boolean/numeric evidence."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _same_record(value, right[key]) for key, value in left.items()
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _same_record(a, b) for a, b in zip(left, right, strict=True)
        )
    return left == right
