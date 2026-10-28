"""Book-aligned timing applicability and queue-reference validation."""

from __future__ import annotations

import pytest

from flo.errors import ValidationError
from flo.process.ir.models import IR, Edge, Node
from flo.process.ir.validate import validate_ir


def _profile(value: int | float = 5) -> dict:
    return {
        "basis": "observed",
        "results": {
            "mean": {"method": "mean", "value": value, "unit": "min"},
        },
        "primary": "mean",
        "analysis_input": "mean",
        "observation_count": 3,
        "observation_unit": "order",
    }


def _linear(node: Node) -> IR:
    return IR(
        name="timing",
        nodes=[Node(id="start", type="start"), node, Node(id="end", type="end")],
        edges=[
            Edge(source="start", target=node.id),
            Edge(source=node.id, target="end"),
        ],
    )


@pytest.mark.parametrize("kind", ["task", "system_task", "subprocess"])
def test_work_steps_accept_book_timing_fields(kind):
    validate_ir(
        _linear(
            Node(
                id="work",
                type=kind,
                cycle_time=_profile(10),
                wait_time=_profile(4),
                changeover_time=_profile(2),
            )
        )
    )


@pytest.mark.parametrize("kind", ["queue", "wait"])
def test_waiting_steps_accept_wait_time(kind):
    validate_ir(_linear(Node(id="waiting", type=kind, wait_time=_profile())))


@pytest.mark.parametrize(
    "kind",
    ["start", "end", "decision", "branch", "parallel_split", "parallel_join"],
)
def test_control_nodes_reject_operational_measurements(kind):
    node = Node(id="control", type=kind, cycle_time=_profile())
    with pytest.raises(ValidationError, match="E1508"):
        _validate_measurement_applicability(node)


@pytest.mark.parametrize("kind", ["queue", "wait"])
@pytest.mark.parametrize("field", ["cycle_time", "changeover_time"])
def test_non_work_steps_reject_work_measurements(kind, field):
    node = Node(id="waiting", type=kind, **{field: _profile()})
    with pytest.raises(ValidationError, match="E1508"):
        validate_ir(_linear(node))


def test_invalid_profile_is_rejected():
    node = Node(
        id="work",
        type="task",
        cycle_time={
            "basis": "observed",
            "results": {"mean": {"method": "mean", "value": 5, "unit": "min"}},
            "primary": "missing",
        },
    )
    with pytest.raises(ValidationError, match="E1301"):
        validate_ir(_linear(node))


def test_queue_can_reference_work_wait_without_copying_value():
    process = IR(
        name="projection",
        nodes=[
            Node(id="start", type="start"),
            Node(id="queue", type="queue", wait_time={"ref": "work.wait_time"}),
            Node(id="work", type="task", cycle_time=_profile(), wait_time=_profile(12)),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="queue"),
            Edge(source="queue", target="work"),
            Edge(source="work", target="end"),
        ],
    )

    validate_ir(process)


@pytest.mark.parametrize(
    "reference",
    ["missing.wait_time", "work.cycle_time", "queue.wait_time"],
)
def test_queue_reference_must_resolve_to_work_wait(reference):
    process = IR(
        name="projection",
        nodes=[
            Node(id="start", type="start"),
            Node(id="queue", type="queue", wait_time={"ref": reference}),
            Node(id="work", type="task", cycle_time=_profile(), wait_time=_profile()),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="queue"),
            Edge(source="queue", target="work"),
            Edge(source="work", target="end"),
        ],
    )

    with pytest.raises(ValidationError, match=r"E1507|E1510"):
        validate_ir(process)


def _validate_measurement_applicability(node: Node) -> None:
    process = IR(
        name="control",
        nodes=[
            Node(id="start", type="start"),
            Node(id="work", type="task"),
            Node(id="end", type="end"),
        ],
        edges=[Edge(source="start", target="work"), Edge(source="work", target="end")],
    )
    process.nodes[1] = node
    process.edges = [
        Edge(source="start", target=node.id),
        Edge(source=node.id, target="end"),
    ]
    validate_ir(process)
