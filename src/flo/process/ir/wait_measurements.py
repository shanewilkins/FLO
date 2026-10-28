"""Shared projection relationships for canonical waiting evidence."""

from flo.process.measurements import measurement_reference

from .models import IR

WORK_NODE_TYPES = frozenset({"task", "system_task", "subprocess"})


def queue_wait_projections(process: IR) -> dict[str, frozenset[str]]:
    """Resolve queue projections to the work node carrying source evidence."""
    return {
        node.id: frozenset({reference[0]})
        for node in process.nodes
        if node.type.lower() in {"queue", "wait"}
        if (reference := measurement_reference(node.wait_time)) is not None
    }
