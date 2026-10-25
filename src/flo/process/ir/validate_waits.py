"""Validation of repeated and aggregate waiting measurements."""

from math import fsum, isclose

from flo.errors import ValidationError
from flo.process.durations import (
    duration_measurement_id,
    duration_measurement_refs,
    duration_seconds,
)

from .metadata import extract_node_metadata
from .models import IR, Node
from .wait_measurements import WORK_NODE_TYPES


def validate_wait_measurements(process: IR) -> None:
    """Reject contradictory identities and unsupported aggregate assertions."""
    work_waits = _work_waits(process)
    identified: dict[str, tuple[float, float]] = {}
    projection_refs: dict[str, frozenset[str]] = {}
    for node in sorted(process.nodes, key=lambda item: item.id):
        field = "wait_before" if node.type.lower() in WORK_NODE_TYPES else "wait_time"
        if node.type.lower() not in WORK_NODE_TYPES | {"queue"}:
            continue
        wait = extract_node_metadata(node).get(field)
        _validate_identity(node, field, wait, identified)
        if node.type.lower() == "queue":
            _validate_projection(node, work_waits)
            _validate_aggregate_identity(node, wait, projection_refs)
    _validate_adjacent_waits(process)


def _validate_identity(
    node: Node, field: str, wait: object, identified: dict[str, tuple[float, float]]
) -> None:
    seconds, measurement_id = duration_seconds(wait), duration_measurement_id(wait)
    if measurement_id is None or seconds is None:
        return
    smallest, largest = identified.get(measurement_id, (seconds, seconds))
    smallest, largest = min(smallest, seconds), max(largest, seconds)
    if not isclose(smallest, largest, rel_tol=1e-9, abs_tol=0):
        raise ValidationError(
            f"E1509: node '{node.id}' metadata.{field} contradicts "
            f"wait measurement_id '{measurement_id}'. Repeated "
            "measurements must have equivalent durations."
        )
    identified[measurement_id] = smallest, largest


def _validate_aggregate_identity(
    node: Node, wait: object, projection_refs: dict[str, frozenset[str]]
) -> None:
    refs = frozenset(duration_measurement_refs(wait))
    measurement_id = duration_measurement_id(wait)
    if measurement_id is None or not refs:
        return
    previous = projection_refs.setdefault(measurement_id, refs)
    if previous != refs:
        raise ValidationError(
            f"E1510: node '{node.id}' metadata.wait_time contradicts "
            f"the measurement_refs for aggregate '{measurement_id}'."
        )


def _work_waits(process: IR) -> dict[str, dict]:
    waits: dict[str, dict] = {}
    for node in process.nodes:
        if node.type.lower() not in WORK_NODE_TYPES:
            continue
        wait = extract_node_metadata(node).get("wait_before")
        if not isinstance(wait, dict):
            continue
        measurement_id = duration_measurement_id(wait)
        if measurement_id is None:
            continue
        if measurement_id in waits:
            raise ValidationError(
                f"E1506: node '{node.id}' duplicates work wait measurement_id "
                f"'{measurement_id}'. Give each distinct work wait a unique ID."
            )
        waits[measurement_id] = wait
    return waits


def _validate_projection(node: Node, work_waits: dict[str, dict]) -> None:
    wait = extract_node_metadata(node).get("wait_time")
    refs = duration_measurement_refs(wait)
    for ref in refs:
        if ref not in work_waits:
            raise ValidationError(
                f"E1507: node '{node.id}' metadata.wait_time references unknown "
                f"work wait measurement_id '{ref}'."
            )
    if not refs:
        return
    shared_id = duration_measurement_id(wait)
    if shared_id in work_waits and set(refs) != {shared_id}:
        raise ValidationError(
            f"E1510: node '{node.id}' metadata.wait_time cannot use a work "
            "measurement_id while projecting different measurements."
        )
    values = [duration_seconds(work_waits[ref]) for ref in refs]
    if any(value is None for value in values):
        raise ValidationError(
            f"E1510: node '{node.id}' metadata.wait_time references invalid waiting evidence."
        )
    try:
        total = fsum(value for value in values if value is not None)
    except OverflowError as exc:
        raise ValidationError(
            f"E1510: node '{node.id}' metadata.wait_time referenced sum "
            "must remain finite in seconds."
        ) from exc
    seconds = duration_seconds(wait)
    if seconds is None or not isclose(seconds, total, rel_tol=1e-9, abs_tol=0):
        raise ValidationError(
            f"E1510: node '{node.id}' metadata.wait_time must equal the sum "
            "of its distinct measurement_refs after conversion to seconds."
        )


def _validate_adjacent_waits(process: IR) -> None:
    nodes = {node.id: node for node in process.nodes}
    for edge in process.edges:
        source, target = nodes.get(edge.source), nodes.get(edge.target)
        if source is None or target is None:
            continue
        if source.type.lower() != "queue" or target.type.lower() not in WORK_NODE_TYPES:
            continue
        queue_wait = extract_node_metadata(source).get("wait_time")
        work_wait = extract_node_metadata(target).get("wait_before")
        if not isinstance(queue_wait, dict) or not isinstance(work_wait, dict):
            continue
        queue_id, work_id = (
            duration_measurement_id(queue_wait),
            duration_measurement_id(work_wait),
        )
        refs = duration_measurement_refs(queue_wait)
        linked = work_id is not None and (queue_id == work_id or work_id in refs)
        independent = work_id is not None and (queue_id is not None or bool(refs))
        if not linked and not independent:
            raise ValidationError(
                f"E1505: queue '{source.id}' wait_time and work node '{target.id}' "
                "wait_before describe the same queue-to-work boundary without a "
                "clear measurement relationship. Link a repeated measurement, give "
                "independent measurements distinct non-empty measurement_id values, or "
                "keep the measurement on only one node."
            )
