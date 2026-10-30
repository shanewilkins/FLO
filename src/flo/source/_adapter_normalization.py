"""Adapter-facing normalization helpers for compilation.

This module owns adapter payload normalization concerns: process metadata,
source node extraction/flattening, and attribute normalization.
"""

from __future__ import annotations

from typing import Any

from flo.process.identity import validate_lane_ids
from flo.process.validation_errors import LocatedValidationError

from .models import (
    BranchConfig,
    SourceDocument,
    SourceShapeError,
    source_path,
    validate_source_shape,
)


def validate_adapter_contract(adapter: dict[str, Any]) -> SourceDocument:
    """Validate source shapes once, then check source-specific relationships."""
    document = validate_source_shape(SourceDocument, adapter)
    seen_ids: set[str] = set()
    _validate_step_entries(adapter["steps"], (), seen_ids)
    try:
        validate_lane_ids(adapter.get("lanes") or [])
    except LocatedValidationError as exc:
        raise SourceShapeError(str(exc), exc.location, code="E1035") from exc
    for path, entries in (
        (("process", "business_units"), adapter["process"].get("business_units")),
    ):
        ids = [entry["id"] for entry in entries or []]
        if len(set(ids)) != len(ids):
            raise SourceShapeError(f"duplicate {source_path(path)} id detected", path)
    return document


def _validate_step_entries(
    steps: list[dict], parent: tuple, seen_ids: set[str]
) -> None:
    for index, step in enumerate(steps):
        path = (*parent, "steps", index) if not parent else (*parent, index)
        step_id = step["id"]
        if step_id in seen_ids:
            raise SourceShapeError(
                f"duplicate step id '{step_id}' detected at {source_path(path)}",
                (*path, "id"),
            )
        seen_ids.add(step_id)
        kind = step["kind"]
        _validate_named_paths(step, path)
        branch = step.get("branch")
        branch_path = (*path, "branch")
        if kind == "branch" and "branch" not in step:
            validate_source_shape(BranchConfig, branch, branch_path)
        nested_key = "steps"
        if kind == "subprocess" and nested_key in step:
            _validate_step_entries(step[nested_key], (*path, nested_key), seen_ids)


def _validate_named_paths(step: dict, path: tuple) -> None:
    for field, duplicate in (
        ("outcomes", "E0204"),
        ("routes", "E0213"),
    ):
        if field not in step:
            continue
        location = (*path, field)
        names = [_normalized_outcome_name(name).casefold() for name in step[field]]
        if len(names) != len(set(names)):
            raise SourceShapeError(
                f"{duplicate}: {source_path(location)} contains duplicate branch names",
                location,
            )


def _normalized_outcome_name(value: Any) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return value.strip()


def flatten_source_nodes(
    source_nodes: list[Any],
    parent_subprocess: str | None = None,
) -> list[dict[str, Any]]:
    """Flatten nested subprocess nodes into linear node entries."""
    flattened: list[dict[str, Any]] = []
    for a_node in source_nodes:
        node_entry: dict[str, Any] = dict(a_node)
        if parent_subprocess and not node_entry.get("subprocess_parent"):
            node_entry["subprocess_parent"] = parent_subprocess

        nested_nodes = node_entry.pop("steps", None)
        flattened.append(node_entry)

        if nested_nodes is not None:
            flattened.extend(
                flatten_source_nodes(nested_nodes, parent_subprocess=node_entry["id"])
            )

    return flattened
