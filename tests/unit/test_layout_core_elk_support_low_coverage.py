from __future__ import annotations

from types import SimpleNamespace

from flo.render.layout_core import elk_support


def test_extract_nodes_and_edges_handles_none_and_unknown_input():
    assert elk_support.extract_nodes_and_edges(None) == ([], [])
    assert elk_support.extract_nodes_and_edges(object()) == ([], [])


def test_extract_nodes_and_edges_from_ir_object_preserves_attrs_and_lists():
    process = SimpleNamespace(
        nodes=[
            SimpleNamespace(
                id="n1",
                type="task",
                attrs={
                    "name": "Node One",
                    "lane": "ops",
                    "note": "note",
                    "subprocess_parent": "p0",
                    "location": "A1",
                    "metadata": {"k": "v"},
                    "workers": ["w1"],
                    "equipment": ["eq1"],
                    "inputs": ["in1"],
                    "outputs": ["out1"],
                },
            )
        ],
        edges=[
            SimpleNamespace(
                source="n1",
                target="n2",
                outcome="yes",
                label="ok",
                edge_type="rework",
                rework=True,
                metadata={"rate": 0.1},
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
            "note": "note",
            "subprocess_parent": "p0",
            "location": "A1",
            "metadata": {"k": "v"},
            "workers": ["w1"],
            "equipment": ["eq1"],
            "inputs": ["in1"],
            "outputs": ["out1"],
        }
    ]
    assert edges == [
        {
            "source": "n1",
            "target": "n2",
            "outcome": "yes",
            "label": "ok",
            "edge_type": "rework",
            "rework": True,
            "metadata": {"rate": 0.1},
        }
    ]


def test_extract_nodes_and_edges_from_graph_dict_promotes_parent_and_filters_edges():
    process = {
        "nodes": [
            {"id": "a", "attrs": {"subprocess_parent": "parent-a"}},
            "skip",
        ],
        "edges": [
            {"source": "a", "target": "b"},
            "skip",
        ],
    }

    nodes, edges = elk_support.extract_nodes_and_edges(process)

    assert nodes == [
        {
            "id": "a",
            "attrs": {"subprocess_parent": "parent-a"},
            "subprocess_parent": "parent-a",
        }
    ]
    assert edges == [{"source": "a", "target": "b"}]


def test_extract_nodes_and_edges_from_adapter_dict_with_transitions_and_synthesized_edges():
    nodes, edges = elk_support.extract_nodes_and_edges(
        {
            "transitions": [{"source": "s", "target": "t"}, "skip"],
        }
    )
    assert nodes == []
    assert edges == [{"source": "s", "target": "t"}]

    synthesized_nodes, synthesized_edges = elk_support.extract_nodes_and_edges(
        {
            "steps": [
                {
                    "id": "a",
                    "kind": "task",
                    "outcomes": {
                        True: {
                            "target": "b",
                            "edge_type": "rework",
                            "rework": True,
                            "metadata": {"reason": "retry"},
                        },
                        False: None,
                    },
                },
                {"id": "b", "kind": "end"},
                {"id": "c", "kind": "task"},
                {"id": "parent", "subnodes": [{"id": "child"}, "skip"]},
            ]
        }
    )

    child = next(node for node in synthesized_nodes if node.get("id") == "child")
    assert child.get("subprocess_parent") == "parent"

    assert {
        "source": "a",
        "target": "b",
        "outcome": "yes",
        "edge_type": "rework",
        "rework": True,
        "metadata": {"reason": "retry"},
    } in synthesized_edges
    assert {"source": "c", "target": "parent"} in synthesized_edges
    assert {"source": "parent", "target": "child"} in synthesized_edges


def test_project_parent_only_subprocess_view_collapses_hidden_edges_and_semantics():
    nodes = [
        {"id": "a", "name": "Visible A"},
        {"id": "h1", "subprocess_parent": "a"},
        {"id": "h2", "metadata": {"subprocess_parent": "a"}},
        {"id": "b", "name": "Visible B"},
    ]
    edges = [
        {
            "source": "a",
            "target": "h1",
            "outcome": "no",
            "edge_type": "rework",
            "rework": True,
            "metadata": {"reason": "loop"},
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
            "edge_type": "rework",
            "rework": True,
            "metadata": {"reason": "loop"},
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
