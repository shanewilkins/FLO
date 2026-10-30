"""Graph identity checks preserve distinct transitions and evidence."""

from copy import deepcopy

import pytest

from flo.errors import ValidationError
from flo.process.ir import validate_ir
from flo.process.ir._internal_shape import ir_from_internal_dict, ir_to_internal_dict
from flo.process.ir.models import IR, Edge, Node
from flo.process.ir.validate_identity import validate_graph_identity


def parallel():
    return IR(
        name="parallel",
        nodes=[
            Node("s", "start"),
            Node("p", "parallel_split"),
            Node("j", "parallel_join"),
            Node("e", "end"),
        ],
        edges=[Edge("s", "p"), Edge("p", "j"), Edge("p", "j"), Edge("j", "e")],
    )


def test_repeated_edge_does_not_establish_parallel_branches_and_is_not_repaired():
    process = parallel()
    before = ir_to_internal_dict(process)
    with pytest.raises(ValidationError, match="E1033") as error:
        validate_ir(process)
    assert error.value.location == ("edges", 2)
    assert ir_to_internal_dict(process) == before
    restored = ir_from_internal_dict(before)
    with pytest.raises(ValidationError, match="E1033"):
        validate_ir(restored)


def test_distinct_parallel_paths_remain_valid():
    process = parallel()
    process.nodes.extend([Node("a", "task"), Node("b", "task")])
    process.edges[1:3] = [
        Edge("p", "a"),
        Edge("p", "b"),
        Edge("a", "j"),
        Edge("b", "j"),
    ]
    validate_ir(process)


@pytest.mark.parametrize(
    "field,values",
    [
        ("id", ["left", "right"]),
        ("outcome", ["yes", "no"]),
        ("route", ["left", "right"]),
        ("label", ["One", "Two"]),
        ("handoff", [{}, {"type": "information"}]),
        ("rework", [{}, {"reason": "Correction"}]),
        ("extensions", [{"example:flag": True}, {"example:flag": 1}]),
    ],
)
def test_differing_canonical_fields_are_not_silently_collapsed(field, values):
    edges = [Edge("a", "b", **{field: deepcopy(value)}) for value in values]
    process = IR(name="distinct", nodes=[], edges=edges)
    before = ir_to_internal_dict(process)
    validate_graph_identity(process)
    assert ir_to_internal_dict(process) == before


def test_duplicate_nested_evidence_is_independent_of_mapping_order():
    one = Edge("a", "b", extensions={"example:data": {"a": [1, 2], "b": 3}})
    two = Edge("a", "b", extensions={"example:data": {"b": 3, "a": [1, 2]}})
    with pytest.raises(ValidationError, match="E1033"):
        validate_graph_identity(IR(name="duplicate", nodes=[], edges=[one, two]))


def test_optional_transition_ids_use_a_separate_namespace_from_nodes():
    process = IR(
        name="identity",
        nodes=[Node("s", "start"), Node("e", "end")],
        edges=[Edge("s", "e", id="s")],
    )
    validate_ir(process)


def test_distinct_decision_outcomes_can_share_target():
    process = IR(
        name="decision",
        nodes=[Node("s", "start"), Node("d", "decision"), Node("e", "end")],
        edges=[
            Edge("s", "d"),
            Edge("d", "e", outcome="yes"),
            Edge("d", "e", outcome="no"),
        ],
    )
    validate_ir(process)
    assert [edge.outcome for edge in process.edges[1:]] == ["yes", "no"]
