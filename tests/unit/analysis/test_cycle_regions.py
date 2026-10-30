"""Cycle findings derive from topology and preserve canonical edge evidence."""

from copy import deepcopy
from dataclasses import asdict, replace

from flo.process.analysis import analyze_process_structure, scc_condense
from flo.process.analysis.cycles import analyze_cycles
from flo.process.ir._internal_shape import ir_to_internal_dict
from flo.process.ir.models import IR, Edge, Node


def process():
    return IR(
        name="regions",
        nodes=[Node(key, "task") for key in ["s", "a", "b", "c", "e"]],
        edges=[
            Edge("s", "a", id="entry", handoff={"type": "information"}),
            Edge("a", "b", id="forward"),
            Edge(
                "b",
                "a",
                id="rework",
                rework={"reason": "Correct"},
                extensions={"example:evidence": {"count": 2}},
            ),
            Edge("a", "a", id="self"),
            Edge("b", "c", id="between"),
            Edge("c", "c", id="loop"),
            Edge("c", "e", id="exit"),
        ],
    )


def test_regions_include_internal_self_loop_and_boundary_evidence():
    model = process()
    before = ir_to_internal_dict(model)
    first, second = analyze_cycles(model)
    assert first.node_ids == ("a", "b") and first.self_loop_node_ids == ("a",)
    assert {edge["id"] for edge in first.internal_edges} == {
        "forward",
        "rework",
        "self",
    }
    assert first.entry_edges == (asdict(model.edges[0]),)
    assert first.exit_edges == second.entry_edges == (asdict(model.edges[4]),)
    assert second.node_ids == second.self_loop_node_ids == ("c",)
    assert second.exit_edges == (asdict(model.edges[-1]),)
    assert next(edge for edge in first.internal_edges if edge["id"] == "rework")[
        "extensions"
    ] == {"example:evidence": {"count": 2}}
    payload = first.as_dict()
    payload["entry_edges"][0]["handoff"]["type"] = "changed"
    assert first.entry_edges[0]["handoff"]["type"] == "information"
    assert ir_to_internal_dict(model) == before


def test_region_and_structural_outputs_are_independent_of_declaration_order():
    model = process()
    shuffled = replace(
        model, nodes=list(reversed(model.nodes)), edges=list(reversed(model.edges))
    )
    assert [region.as_dict() for region in analyze_cycles(model)] == [
        region.as_dict() for region in analyze_cycles(shuffled)
    ]
    assert (
        analyze_process_structure(model).as_dict()
        == analyze_process_structure(shuffled).as_dict()
    )


def test_acyclic_edges_against_source_order_do_not_produce_cycle_or_rework_findings():
    model = IR(
        name="DAG",
        nodes=[
            Node("e", "end"),
            Node("b", "task"),
            Node("s", "start"),
            Node("a", "task"),
        ],
        edges=[Edge("s", "a"), Edge("a", "b"), Edge("b", "e")],
    )
    result = analyze_process_structure(model)
    assert result.cycle_regions == () and result.rework_edges == ()
    assert not any(
        "cycle" in item.code or "backward" in item.code for item in result.diagnostics
    )
    assert [path.node_ids for path in result.paths] == [("s", "a", "b", "e")]


def test_overlapping_cycles_form_one_maximal_region_without_cycle_enumeration():
    model = IR(
        name="overlap",
        nodes=[Node(key, "task") for key in "abcd"],
        edges=[
            Edge("a", "b"),
            Edge("b", "a"),
            Edge("b", "c"),
            Edge("c", "b"),
            Edge("c", "d"),
        ],
    )
    (region,) = analyze_cycles(model)
    assert region.node_ids == ("a", "b", "c")
    assert len(region.internal_edges) == 4 and region.exit_edges[0]["target"] == "d"


def test_self_loop_only_and_isolated_nodes_are_distinguished():
    model = IR(
        name="self",
        nodes=[Node("a", "task"), Node("b", "task")],
        edges=[Edge("a", "a")],
    )
    (region,) = analyze_cycles(model)
    assert region.node_ids == region.self_loop_node_ids == ("a",)
    assert region.entry_edges == region.exit_edges == ()


def test_condensation_avoids_id_collisions_and_preserves_external_multiplicity():
    model = process()
    model.nodes.append(Node("scc_0", "task"))
    model.edges.extend([Edge("a", "e", id="a-exit"), Edge("b", "e", id="b-exit")])
    before = deepcopy(ir_to_internal_dict(model))
    condensed = scc_condense(model)
    assert len({node.id for node in condensed.nodes}) == len(condensed.nodes)
    assert any(node.id == "scc_0" and node.type == "task" for node in condensed.nodes)
    assert {edge.id for edge in condensed.edges} == {
        "entry",
        "between",
        "loop",
        "exit",
        "a-exit",
        "b-exit",
    }
    assert next(edge for edge in condensed.edges if edge.id == "entry").handoff == {
        "type": "information"
    }
    assert ir_to_internal_dict(model) == before
