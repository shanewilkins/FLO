import pytest

from flo.process.analysis.scc import scc_condense
from flo.process.ir.models import Edge


def test_scc_no_edges_returns_same(ir_factory, node_factory):
    ir = ir_factory(name="noedges", nodes=[node_factory("a"), node_factory("b")])
    out = scc_condense(ir)
    # no edges -> identity
    assert out is ir


def test_scc_cycle_condenses(ir_factory, node_factory):
    # create a simple cycle a->b->a
    a = node_factory("a")
    b = node_factory("b")
    ir = ir_factory(
        name="cycle",
        nodes=[a, b],
        edges=[Edge(source="a", target="b"), Edge(source="b", target="a")],
    )
    out = scc_condense(ir)
    # should produce a condensed IR with one scc node
    assert len(out.nodes) == 1
    assert out.nodes[0].id.startswith("scc_")


def test_scc_three_node_cycle_condenses_to_one_scc(ir_factory, node_factory):
    a = node_factory("a")
    b = node_factory("b")
    c = node_factory("c")
    ir = ir_factory(
        name="tricycle",
        nodes=[a, b, c],
        edges=[
            Edge(source="a", target="b"),
            Edge(source="b", target="c"),
            Edge(source="c", target="a"),
        ],
    )
    out = scc_condense(ir)
    assert len(out.nodes) == 1
    scc_node = out.nodes[0]
    assert scc_node.id.startswith("scc_")
    assert set(scc_node.extensions["flo:scc_members"]) == {"a", "b", "c"}


def test_scc_two_separate_cycles_condense_independently(ir_factory, node_factory):
    # Two disjoint cycles: a<->b and c<->d
    a = node_factory("a")
    b = node_factory("b")
    c = node_factory("c")
    d = node_factory("d")
    ir = ir_factory(
        name="twin_cycles",
        nodes=[a, b, c, d],
        edges=[
            Edge(source="a", target="b"),
            Edge(source="b", target="a"),
            Edge(source="c", target="d"),
            Edge(source="d", target="c"),
        ],
    )
    out = scc_condense(ir)
    assert len(out.nodes) == 2
    scc_ids = {n.id for n in out.nodes}
    assert all(nid.startswith("scc_") for nid in scc_ids)


def test_scc_cycle_with_external_predecessor_and_successor(ir_factory, node_factory):
    # x -> a <-> b -> y: condense {a,b} to scc_N, preserve x->scc_N->y
    x = node_factory("x")
    a = node_factory("a")
    b = node_factory("b")
    y = node_factory("y")
    ir = ir_factory(
        name="wrapped_cycle",
        nodes=[x, a, b, y],
        edges=[
            Edge(source="x", target="a"),
            Edge(source="a", target="b"),
            Edge(source="b", target="a"),
            Edge(source="b", target="y"),
        ],
    )
    out = scc_condense(ir)
    node_ids = {n.id for n in out.nodes}
    # x and y survive; a and b collapse into one scc node
    assert "x" in node_ids
    assert "y" in node_ids
    scc_nodes = [n for n in out.nodes if n.id.startswith("scc_")]
    assert len(scc_nodes) == 1
    assert set(scc_nodes[0].extensions["flo:scc_members"]) == {"a", "b"}
    # scc node should have an outgoing edge to y
    assert any(
        edge.source == scc_nodes[0].id and edge.target == "y" for edge in out.edges
    )


def test_scc_dag_with_no_cycle_returns_same_ir(ir_factory, node_factory):
    # Pure DAG: a -> b -> c (no cycle) should return original IR unchanged
    a = node_factory("a")
    b = node_factory("b")
    c = node_factory("c")
    ir = ir_factory(
        name="dag",
        nodes=[a, b, c],
        edges=[Edge(source="a", target="b"), Edge(source="b", target="c")],
    )
    out = scc_condense(ir)
    assert out is ir


def test_condense_scc_raises_for_non_ir():
    with pytest.raises(TypeError):
        scc_condense({"not": "an ir"})
