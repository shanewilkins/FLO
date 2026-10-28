"""Queue waiting projections resolve directly to work-step evidence."""

import pytest

from flo.errors import ValidationError
from flo.process.ir.models import IR, Edge, Node
from flo.process.ir.validate import validate_ir


def _profile(value=60, unit="s"):
    return {
        "basis": "observed",
        "results": {
            "mean": {"method": "mean", "value": value, "unit": unit},
        },
        "primary": "mean",
        "analysis_input": "mean",
    }


def _process(queue_wait, *, work_wait=None):
    nodes = [
        Node("start", "start"),
        Node("queue", "queue", wait_time=queue_wait),
        Node(
            "work",
            "task",
            cycle_time=_profile(1),
            wait_time=work_wait,
        ),
        Node("end", "end"),
    ]
    return IR(
        "Evidence",
        nodes,
        [
            Edge("start", "queue"),
            Edge("queue", "work"),
            Edge("work", "end"),
        ],
    )


def test_queue_reference_resolves_to_work_wait_time():
    validate_ir(_process({"ref": "work.wait_time"}, work_wait=_profile(1, "min")))


def test_queue_reference_rejects_unknown_target():
    with pytest.raises(ValidationError, match=r"E1507.*unknown"):
        validate_ir(_process({"ref": "missing.wait_time"}))


def test_queue_reference_rejects_non_wait_field():
    with pytest.raises(ValidationError, match=r"E1507.*work step's wait_time"):
        validate_ir(_process({"ref": "work.cycle_time"}, work_wait=_profile()))


def test_queue_reference_rejects_missing_target_measurement():
    with pytest.raises(ValidationError, match=r"E1507.*missing"):
        validate_ir(_process({"ref": "work.wait_time"}))


def test_queue_reference_cannot_chain():
    process = _process({"ref": "work.wait_time"}, work_wait=_profile())
    process.nodes[2].wait_time = {"ref": "other.wait_time"}
    with pytest.raises(ValidationError, match="E1510"):
        validate_ir(process)


def test_only_queue_nodes_may_reference_wait_time():
    process = _process(_profile(), work_wait={"ref": "queue.wait_time"})
    with pytest.raises(ValidationError, match="E1504"):
        validate_ir(process)
