from __future__ import annotations

import json

import pytest

from flo.process.export.json_export import ir_to_schema_dict, ir_to_schema_json
from flo.process.ir.models import IR, Edge, Node


def test_schema_dict_defaults_generated_process_name():
    ir = IR(name="", nodes=[Node(id="n", type="task")], edges=[])
    payload = ir_to_schema_dict(ir)
    assert payload["process"]["id"] == "generated"
    assert payload["process"]["name"] == "generated"


def test_schema_dict_prefers_authored_process_id_and_name_from_metadata():
    ir = IR(
        name="compiled_fallback_name",
        nodes=[Node(id="n", type="task")],
        edges=[],
        process_metadata={
            "process_id": "authored_process_id",
            "process_name": "Authored Process Name",
        },
    )

    payload = ir_to_schema_dict(ir)
    assert payload["process"]["id"] == "authored_process_id"
    assert payload["process"]["name"] == "Authored Process Name"


def test_retired_node_attrs_fail_instead_of_being_discarded():
    with pytest.raises(TypeError, match="attrs"):
        Node(id="n", type="task", attrs="bad")


def test_edge_to_schema_omits_absent_optional_fields():
    ir = IR(
        name="p",
        nodes=[],
        edges=[
            Edge(source="a", target="b"),
            Edge(
                source="b",
                target="c",
                id="e2",
                outcome="no",
                label="reject",
                rework={"reason": "Rejected"},
                extensions={"example:m": 1},
            ),
        ],
    )
    payload = ir_to_schema_dict(ir)
    first = payload["edges"][0]
    second = payload["edges"][1]
    assert first == {"source": "a", "target": "b"}
    assert second["id"] == "e2"
    assert second["outcome"] == "no"
    assert second["label"] == "reject"
    assert second["rework"] == {"reason": "Rejected"}
    assert second["extensions"] == {"example:m": 1}


def test_export_uses_only_explicit_canonical_edges():
    ir = IR(
        name="p",
        nodes=[Node(id="a", type="task"), Node(id="b", type="end")],
        edges=[Edge(source="a", target="b", id="e_0")],
    )
    assert ir_to_schema_dict(ir)["edges"] == [
        {"id": "e_0", "source": "a", "target": "b"}
    ]
    ir.edges = []
    assert ir_to_schema_dict(ir)["edges"] == []


def test_schema_json_indent_none_and_positive():
    ir = IR(name="p", nodes=[Node(id="n", type="task")], edges=[])
    compact = ir_to_schema_json(ir, indent=None)
    pretty = ir_to_schema_json(ir, indent=2)
    assert "\n" not in compact
    assert "\n" in pretty
    assert json.loads(compact)["process"]["id"] == "p"


def test_node_note_is_exported_when_present():
    ir = IR(
        name="p",
        nodes=[
            Node(
                id="n",
                type="task",
                name="Task",
                description="Internal follow-up required",
            )
        ],
        edges=[],
    )
    payload = ir_to_schema_dict(ir)
    assert payload["nodes"][0]["description"] == "Internal follow-up required"


def test_node_inputs_and_outputs_are_exported_when_present():
    ir = IR(
        name="p",
        nodes=[
            Node(
                id="mix",
                type="task",
                name="Mix",
                consumes=["flour", "water"],
                produces=["dough"],
            )
        ],
        edges=[],
    )
    payload = ir_to_schema_dict(ir)
    assert payload["nodes"][0]["consumes"] == ["flour", "water"]
    assert payload["nodes"][0]["produces"] == ["dough"]


def test_node_location_workers_and_equipment_are_exported_when_present():
    ir = IR(
        name="p",
        nodes=[
            Node(
                id="mix",
                type="task",
                name="Mix",
                location="prep_bench",
                performed_by=["lead_baker"],
                uses=["mixer"],
            )
        ],
        edges=[],
    )
    payload = ir_to_schema_dict(ir)
    assert payload["nodes"][0]["location"] == "prep_bench"
    assert payload["nodes"][0]["performed_by"] == ["lead_baker"]
    assert payload["nodes"][0]["uses"] == ["mixer"]


def test_node_canonical_relations_are_exported_when_present():
    ir = IR(
        name="p",
        nodes=[
            Node(
                id="mix",
                type="task",
                name="Mix",
                consumes=["flour", "water"],
                produces=["dough"],
                performed_by=["lead_baker"],
                uses=["mixer"],
            )
        ],
        edges=[],
    )
    payload = ir_to_schema_dict(ir)
    assert payload["nodes"][0]["consumes"] == ["flour", "water"]
    assert payload["nodes"][0]["produces"] == ["dough"]
    assert payload["nodes"][0]["performed_by"] == ["lead_baker"]
    assert payload["nodes"][0]["uses"] == ["mixer"]


def test_edge_handoff_is_exported_when_present():
    ir = IR(
        name="p",
        nodes=[Node(id="a", type="start"), Node(id="b", type="end")],
        edges=[Edge(source="a", target="b", handoff={"type": "responsibility"})],
    )
    payload = ir_to_schema_dict(ir)
    assert payload["edges"][0]["handoff"] == {"type": "responsibility"}


def test_process_evidence_and_entities_are_exported_when_present():
    lead_time = {
        "basis": "target",
        "primary": "target",
        "results": {"target": {"method": "mean", "value": 3600, "unit": "s"}},
    }
    items = [{"id": "flour", "name": "Flour", "kind": "material"}]
    resources = [
        {"id": "oven", "name": "Oven", "kind": "equipment"},
        {"id": "baker", "name": "Baker", "kind": "person"},
    ]
    locations = [{"id": "kitchen", "name": "Kitchen"}]
    ir = IR(
        name="cookie_process",
        nodes=[],
        edges=[],
        lead_time=lead_time,
        extensions={"example:yield_fraction": {"target": 0.95}},
        items=items,
        resources=resources,
        locations=locations,
    )
    process = ir_to_schema_dict(ir)["process"]
    assert process["lead_time"] == lead_time
    assert process["extensions"]["example:yield_fraction"]["target"] == 0.95
    assert process["items"] == items
    assert process["resources"] == resources
    assert process["locations"] == locations


def test_item_group_annotations_are_exported_as_extensions():
    # Grouping is annotation; typed item identity remains available to consumers.
    groups = {
        "dry": {"name": "Dry Ingredients", "items": ["flour"]},
        "wet": {
            "name": "Wet Ingredients",
            "dairy": {"name": "Dairy", "items": ["butter"]},
        },
    }
    ir = IR(
        name="cookie_process",
        nodes=[],
        edges=[],
        items=[
            {"id": item, "name": item.title(), "kind": "material"}
            for item in ("flour", "butter")
        ],
        extensions={"example:item_groups": groups},
    )
    process = ir_to_schema_dict(ir)["process"]
    exported = process["extensions"]["example:item_groups"]
    assert exported["dry"]["name"] == "Dry Ingredients"
    assert exported["dry"]["items"] == ["flour"]
    assert exported["wet"]["name"] == "Wet Ingredients"
    assert exported["wet"]["dairy"]["name"] == "Dairy"
    assert exported["wet"]["dairy"]["items"] == ["butter"]
    assert {item["id"] for item in process["items"]} == {"flour", "butter"}
