"""Shared identity and projection relationships for canonical waiting evidence."""

from flo.process.durations import duration_measurement_id, duration_measurement_refs

from .metadata import extract_node_metadata
from .models import IR

WORK_NODE_TYPES = frozenset({"task", "system_task", "subprocess"})


def work_wait_measurements(process: IR) -> dict[str, str]:
    """Index labelled work waits; validation separately rejects duplicate IDs."""
    return {
        measurement_id: node.id
        for node in process.nodes
        if node.type.lower() in WORK_NODE_TYPES
        if (
            measurement_id := duration_measurement_id(
                extract_node_metadata(node).get("wait_before")
            )
        )
        is not None
    }


def queue_wait_projections(process: IR) -> dict[str, frozenset[str]]:
    """Resolve queue projections to the work nodes carrying replacement evidence."""
    work_waits = work_wait_measurements(process)
    shared_refs = _shared_queue_references(process)
    projections: dict[str, frozenset[str]] = {}
    for node in process.nodes:
        if node.type.lower() != "queue":
            continue
        wait = extract_node_metadata(node).get("wait_time")
        references = duration_measurement_refs(wait)
        measurement_id = duration_measurement_id(wait)
        if not references and measurement_id is not None:
            references = shared_refs.get(measurement_id, ())
        if (
            not references
            and measurement_id is not None
            and measurement_id in work_waits
        ):
            references = (measurement_id,)
        if references and all(reference in work_waits for reference in references):
            projections[node.id] = frozenset(work_waits[ref] for ref in references)
    return projections


def _shared_queue_references(process: IR) -> dict[str, tuple[str, ...]]:
    return {
        measurement_id: refs
        for node in process.nodes
        if node.type.lower() == "queue"
        if (
            measurement_id := duration_measurement_id(
                wait := extract_node_metadata(node).get("wait_time")
            )
        )
        is not None
        if (refs := duration_measurement_refs(wait))
    }
