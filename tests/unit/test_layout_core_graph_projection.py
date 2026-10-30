from __future__ import annotations

from flo.process.ir.models import IR, Edge, Node
from flo.render.layout_core import elk_support


def test_extract_nodes_and_edges_handles_none_and_unknown_input():
    assert elk_support.extract_nodes_and_edges(None) == ([], [])
    assert elk_support.extract_nodes_and_edges(object()) == ([], [])


def test_extract_nodes_and_edges_from_ir_object_preserves_attrs_and_lists():
    process = IR(
        name="Projection",
        nodes=[
            Node(
                id="n1",
                type="task",
                name="Node One",
                lane="ops",
                description="note",
                subprocess_parent="p0",
                location="A1",
                extensions={"example:k": "v"},
                performed_by=["w1"],
                uses=["eq1"],
                consumes=["in1"],
                produces=["out1"],
            )
        ],
        edges=[
            Edge(
                source="n1",
                target="n2",
                outcome="yes",
                label="ok",
                rework={"reason": "retry"},
            )
        ],
    )

    nodes, edges = elk_support.extract_nodes_and_edges(process)

    assert nodes == [
        {
            "id": "n1",
            "kind": "task",
            "name": "Node One",
            "lane": "ops",
            "description": "note",
            "subprocess_parent": "p0",
            "location": "A1",
            "extensions": {"example:k": "v"},
            "performed_by": ["w1"],
            "uses": ["eq1"],
            "consumes": ["in1"],
            "produces": ["out1"],
        }
    ]
    assert edges == [
        {
            "source": "n1",
            "target": "n2",
            "outcome": "yes",
            "label": "ok",
            "rework": {"reason": "retry"},
        }
    ]


def test_extract_nodes_and_edges_from_canonical_graph_preserves_parent():
    process = {
        "nodes": [{"id": "a", "subprocess_parent": "parent-a"}],
        "edges": [{"source": "a", "target": "b"}],
    }
    nodes, edges = elk_support.extract_nodes_and_edges(process)
    assert nodes == [{"id": "a", "subprocess_parent": "parent-a"}]
    assert edges == [{"source": "a", "target": "b"}]


def test_layout_rejects_uncompiled_authored_source():
    import pytest

    with pytest.raises(TypeError, match="compiled IR"):
        elk_support.extract_nodes_and_edges(
            {"steps": [{"id": "start", "kind": "start"}]}
        )


def test_project_parent_only_subprocess_view_collapses_hidden_edges_and_semantics():
    nodes = [
        {"id": "a", "name": "Visible A"},
        {"id": "h1", "subprocess_parent": "a"},
        {"id": "h2", "subprocess_parent": "a"},
        {"id": "b", "name": "Visible B"},
    ]
    edges = [
        {
            "source": "a",
            "target": "h1",
            "outcome": "no",
            "rework": {"reason": "loop"},
        },
        {"source": "h1", "target": "h2", "label": "bridge"},
        {"source": "h2", "target": "b"},
        {"source": "h1", "target": "", "label": "skip"},
        {"source": "h2", "target": "h1", "label": "cycle"},
        {"source": "a", "target": "x", "label": "external"},
    ]

    visible_nodes, collapsed_edges = elk_support.project_parent_only_subprocess_view(
        nodes,
        edges,
    )

    assert [node["id"] for node in visible_nodes] == ["a", "b"]
    assert collapsed_edges == [
        {
            "source": "a",
            "target": "b",
            "outcome": "no",
            "rework": {"reason": "loop"},
        }
    ]


def test_project_parent_only_subprocess_view_is_noop_without_hidden_parents():
    nodes = [{"id": "a"}, {"id": "b"}]
    edges = [{"source": "a", "target": "b", "label": "ok"}]

    projected_nodes, projected_edges = elk_support.project_parent_only_subprocess_view(
        nodes,
        edges,
    )

    assert projected_nodes == nodes
    assert projected_edges == edges
