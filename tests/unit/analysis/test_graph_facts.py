"""Independent topology checks, transition multiplicity and large graph safety."""

from dataclasses import FrozenInstanceError
from itertools import pairwise, product

import pytest

from flo.process.graph import GraphFacts
from flo.process.ir.models import Edge


def test_transition_ordinals_preserve_multiplicity_without_exposing_mutable_ir():
    edges = [Edge("a", "b", id="one"), Edge("a", "b", id="two")]
    graph = GraphFacts.build(["a", "b"], edges)
    assert [(edge.key, edge.source, edge.target) for edge in graph.transitions] == [
        (0, "a", "b"),
        (1, "a", "b"),
    ]
    assert graph.outgoing_records["a"] == graph.incoming_records["b"] == 2
    assert graph.successors["a"] == ("b",) and graph.predecessors["b"] == ("a",)
    assert [edges[edge.key].id for edge in graph.transitions] == ["one", "two"]
    edges[0].target = "different"
    assert graph.transitions[0].target == "b"
    with pytest.raises(TypeError):
        graph.successors["a"] = ()
    with pytest.raises(FrozenInstanceError):
        graph.transitions[0].source = "changed"


def test_unresolved_endpoint_does_not_create_a_ghost_node():
    with pytest.raises(ValueError, match="endpoint unresolved"):
        GraphFacts.build(["a"], [Edge("a", "missing")])


def test_sccs_match_mutual_reachability_for_every_three_node_digraph():
    nodes = ("a", "b", "c")
    pairs = list(product(nodes, repeat=2))
    for bits in range(1 << len(pairs)):
        edges = [
            Edge(a, b) for index, (a, b) in enumerate(pairs) if bits & (1 << index)
        ]
        graph = GraphFacts.build(nodes, edges)
        # Floyd-Warshall is an independent oracle, not another DFS/SCC algorithm.
        reachable = {
            (a, b): a == b or any(e.source == a and e.target == b for e in edges)
            for a, b in pairs
        }
        for via in nodes:
            for a, b in pairs:
                reachable[a, b] |= reachable[a, via] and reachable[via, b]
        expected = {
            tuple(b for b in nodes if reachable[a, b] and reachable[b, a])
            for a in nodes
        }
        assert set(graph.components()) == expected, bits
        expected_cycles = {
            group
            for group in expected
            if len(group) > 1 or any(e.source == e.target == group[0] for e in edges)
        }
        assert set(graph.cyclic_components()) == expected_cycles, bits
        assert graph.reachable(["a"]) == {b for b in nodes if reachable["a", b]}


@pytest.mark.parametrize("cyclic", [False, True])
def test_deep_graphs_do_not_depend_on_python_recursion_limit(cyclic):
    nodes = [f"n{index:05}" for index in range(5000)]
    edges = [Edge(a, b) for a, b in pairwise(nodes)]
    if cyclic:
        edges.append(Edge(nodes[-1], nodes[0]))
    graph = GraphFacts.build(nodes, edges)
    assert len(graph.reachable([nodes[0]])) == 5000
    if cyclic:
        assert graph.cyclic_components() == (tuple(nodes),)
    else:
        assert graph.cyclic_components() == ()
        assert len(graph.components()) == 5000


def test_empty_graph_has_no_components_or_invented_reachability():
    graph = GraphFacts.build([], [])
    assert graph.components() == () and graph.cyclic_components() == ()
    assert graph.reachable([]) == set()


def test_multisource_and_reverse_reachability_share_the_frozen_topology():
    graph = GraphFacts.build("abcde", [Edge("a", "c"), Edge("b", "c"), Edge("c", "d")])
    assert graph.reachable(["a", "b"]) == set("abcd")
    assert graph.reachable(["d"], reverse=True) == set("abcd")
    assert graph.reachable(["d", "e"], reverse=True) == set("abcde")
    assert graph.reachable(["e"]) == {"e"}
