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


def test_node_note_is_exported_when_present():
    ir = IR(
        name="p",
        nodes=[Node(id="n", type="task", attrs={"name": "Task", "note": "Internal follow-up required"})],
        edges=[],
    )
    payload = ir_to_schema_dict(ir)
    assert payload["nodes"][0]["note"] == "Internal follow-up required"


def test_node_inputs_and_outputs_are_exported_when_present():
    ir = IR(
        name="p",
        nodes=[
            Node(
                id="mix",
                type="task",
                attrs={
                    "name": "Mix",
                    "inputs": ["flour", "water"],
                    "outputs": ["dough"],
                },
            )
        ],
        edges=[],
    )
    payload = ir_to_schema_dict(ir)
    assert payload["nodes"][0]["inputs"] == ["flour", "water"]
    assert payload["nodes"][0]["outputs"] == ["dough"]


def test_node_location_workers_and_equipment_are_exported_when_present():
    ir = IR(
        name="p",
        nodes=[
            Node(
                id="mix",
                type="task",
                attrs={
                    "name": "Mix",
                    "location": "prep_bench",
                    "workers": ["lead_baker"],
                    "equipment": ["mixer"],
                },
            )
        ],
        edges=[],
    )
    payload = ir_to_schema_dict(ir)
    assert payload["nodes"][0]["location"] == "prep_bench"
    assert payload["nodes"][0]["workers"] == ["lead_baker"]
    assert payload["nodes"][0]["equipment"] == ["mixer"]


def test_process_metadata_is_exported_when_present():
    ir = IR(
        name="cookie_process",
        nodes=[Node(id="n", type="task", attrs={"name": "Task"})],
        edges=[],
        process_metadata={
            "cycle_time_seconds": {"target": 3600},
            "yield_fraction": {"target": 0.95},
            "materials": [{"id": "flour"}],
            "equipment": [{"id": "oven"}],
            "locations": [{"id": "kitchen"}],
            "workers": [{"id": "baker"}],
        },
    )
    payload = ir_to_schema_dict(ir)
    assert payload["process"]["metadata"]["cycle_time_seconds"]["target"] == 3600
    assert payload["process"]["metadata"]["yield_fraction"]["target"] == 0.95
    assert payload["process"]["metadata"]["materials"][0]["id"] == "flour"
    assert payload["process"]["metadata"]["equipment"][0]["id"] == "oven"
    assert payload["process"]["metadata"]["locations"][0]["id"] == "kitchen"
    assert payload["process"]["metadata"]["workers"][0]["id"] == "baker"


def test_grouped_materials_are_exported_when_present():
    ir = IR(
        name="cookie_process",
        nodes=[Node(id="n", type="task", attrs={"name": "Task"})],
        edges=[],
        process_metadata={
            "materials": {
                "dry": {
                    "name": "Dry Ingredients",
                    "items": [
                        {"id": "flour", "name": "Flour"},
                    ],
                },
                "wet": {
                    "name": "Wet Ingredients",
                    "dairy": {
                        "name": "Dairy",
                        "items": [
                            {"id": "butter", "name": "Butter"},
                        ],
                    },
                },
            }
        },
    )
    payload = ir_to_schema_dict(ir)
    assert payload["process"]["metadata"]["materials"]["dry"]["name"] == "Dry Ingredients"
    assert payload["process"]["metadata"]["materials"]["dry"]["items"][0]["id"] == "flour"
    assert payload["process"]["metadata"]["materials"]["wet"]["name"] == "Wet Ingredients"
    assert payload["process"]["metadata"]["materials"]["wet"]["dairy"]["name"] == "Dairy"
    assert payload["process"]["metadata"]["materials"]["wet"]["dairy"]["items"][0]["id"] == "butter"
