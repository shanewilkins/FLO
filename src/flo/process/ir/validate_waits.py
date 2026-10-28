"""Validation of direct queue-to-work measurement references."""

from flo.errors import ValidationError
from flo.process.measurements import measurement_reference

from .models import IR
from .wait_measurements import WORK_NODE_TYPES


def validate_wait_measurements(process: IR) -> None:
    """Require queue projections to resolve to work-step waiting profiles."""
    nodes = {node.id: node for node in process.nodes}
    for node in process.nodes:
        reference = measurement_reference(node.wait_time)
        if reference is None:
            continue
        if node.type.lower() not in {"queue", "wait"}:
            raise ValidationError(
                f"E1504: node '{node.id}' may reference wait_time only when kind is queue or wait"
            )
        target_id, field = reference
        target = nodes.get(target_id)
        if target is None:
            raise ValidationError(
                f"E1507: queue '{node.id}' wait_time references unknown step '{target_id}'"
            )
        if target.type.lower() not in WORK_NODE_TYPES or field != "wait_time":
            raise ValidationError(
                f"E1507: queue '{node.id}' wait_time must reference a work step's wait_time"
            )
        if measurement_reference(target.wait_time) is not None:
            raise ValidationError(
                f"E1510: queue '{node.id}' wait_time cannot reference another measurement reference"
            )
        if target.wait_time is None:
            raise ValidationError(
                f"E1507: queue '{node.id}' references missing '{target_id}.wait_time'"
            )
