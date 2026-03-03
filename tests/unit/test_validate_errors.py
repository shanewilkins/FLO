import pytest
from flo.compiler.ir.validate import validate_ir
from flo.compiler.ir.models import IR, Node, Edge
from flo.services.errors import ValidationError


def test_validate_ir_wrong_type():
    with pytest.raises(ValidationError):
        validate_ir(object())


def test_validate_ir_empty_nodes(ir_factory):
    ir = ir_factory(name="x", nodes=[])
    with pytest.raises(ValidationError):
        validate_ir(ir)


@pytest.mark.parametrize("ids", [["dup", "dup"], ["a", "a", "a"]])
def test_validate_ir_duplicate_ids(ir_factory, node_factory, ids):
    nodes = [node_factory(i) for i in ids]
    ir = ir_factory(name="dup", nodes=nodes)
    with pytest.raises(ValidationError):
        validate_ir(ir)


def test_validate_ir_unresolved_edge_raises():
    ir = IR(
        name="x",
        nodes=[Node(id="start", type="start"), Node(id="end", type="end")],
        edges=[Edge(source="start", target="missing")],
    )
    with pytest.raises(ValidationError):
        validate_ir(ir)


def test_validate_ir_decision_requires_two_outgoing_edges():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="gate", type="decision"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="gate"),
            Edge(source="gate", target="end"),
        ],
    )
    with pytest.raises(ValidationError):
        validate_ir(ir)


def test_validate_ir_non_start_node_requires_predecessor():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="mid", type="task"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="end"),
            Edge(source="mid", target="end"),
        ],
    )
    with pytest.raises(ValidationError, match="E1006"):
        validate_ir(ir)


def test_validate_ir_non_end_node_requires_successor():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="mid", type="task"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="mid"),
        ],
    )
    with pytest.raises(ValidationError, match="E1007"):
        validate_ir(ir)


def test_validate_ir_decision_error_precedes_generic_successor_rule():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="gate", type="decision"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="gate"),
            Edge(source="gate", target="end"),
        ],
    )
    with pytest.raises(ValidationError, match="E1005"):
        validate_ir(ir)


def test_validate_ir_node_unreachable_from_start_raises():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="a", type="task"),
            Node(id="end", type="end"),
            Node(id="x", type="task"),
            Node(id="y", type="task"),
            Node(id="z", type="end"),
        ],
        edges=[
            Edge(source="start", target="a"),
            Edge(source="a", target="end"),
            Edge(source="x", target="y"),
            Edge(source="y", target="x"),
            Edge(source="y", target="z"),
        ],
    )
    with pytest.raises(ValidationError, match="E1008"):
        validate_ir(ir)


def test_validate_ir_node_cannot_reach_any_end_raises():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="loop", type="task"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="loop"),
            Edge(source="loop", target="loop"),
            Edge(source="start", target="end"),
        ],
    )
    with pytest.raises(ValidationError, match="E1009"):
        validate_ir(ir)


def test_validate_ir_requires_at_least_one_end_node():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="task", type="task"),
        ],
        edges=[
            Edge(source="start", target="task"),
            Edge(source="task", target="start"),
        ],
    )
    with pytest.raises(ValidationError, match="E1010"):
        validate_ir(ir)
