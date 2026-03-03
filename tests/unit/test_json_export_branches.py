from __future__ import annotations

import json

from flo.compiler.ir.models import Edge, IR, Node
from flo.export.json_export import ir_to_schema_dict, ir_to_schema_json


def test_schema_dict_defaults_generated_process_name():
    ir = IR(name="", nodes=[Node(id="n", type="task", attrs={})], edges=[])
    payload = ir_to_schema_dict(ir)
    assert payload["process"]["id"] == "generated"
    assert payload["process"]["name"] == "generated"


def test_node_to_schema_skips_non_dict_attrs():
    ir = IR(name="p", nodes=[Node(id="n", type="task", attrs="bad")], edges=[])
    payload = ir_to_schema_dict(ir)
    assert payload["nodes"][0] == {"id": "n", "kind": "task"}


def test_edge_to_schema_omits_none_and_non_dict_metadata():
    ir = IR(
        name="p",
        nodes=[],
        edges=[
            Edge(source="a", target="b", metadata="not-dict"),
            Edge(source="b", target="c", id="e2", outcome="no", label="reject", metadata={"m": 1}),
        ],
    )
    payload = ir_to_schema_dict(ir)
    first = payload["edges"][0]
    second = payload["edges"][1]
    assert first == {"source": "a", "target": "b"}
    assert second["id"] == "e2"
    assert second["outcome"] == "no"
    assert second["label"] == "reject"
    assert second["metadata"] == {"m": 1}


def test_legacy_edges_from_node_attrs_handles_non_list_and_casts_targets():
    ir = IR(
        name="p",
        nodes=[
            Node(id="a", type="task", attrs={"edges": ["b", 123]}),
            Node(id="bad", type="task", attrs={"edges": "not-list"}),
            Node(id="none", type="task", attrs=None),
        ],
        edges=[],
    )

    payload = ir_to_schema_dict(ir)
    assert payload["edges"] == [
        {"id": "e_0", "source": "a", "target": "b"},
        {"id": "e_1", "source": "a", "target": "123"},
    ]


def test_schema_json_indent_none_and_positive():
    ir = IR(name="p", nodes=[Node(id="n", type="task", attrs={})], edges=[])
    compact = ir_to_schema_json(ir, indent=None)
    pretty = ir_to_schema_json(ir, indent=2)
    assert "\n" not in compact
    assert "\n" in pretty
    assert json.loads(compact)["process"]["id"] == "p"
