import json

from flo.process.export import export_ir
from flo.process.ir import validate_ir
from flo.process.ir.models import IR, Edge, Node


def test_export_ir_defaults_to_json_projection():
    ir = IR(name="p", nodes=[Node(id="start", type="start")], edges=[])
    out = export_ir(ir)
    payload = json.loads(out)
    assert payload["process"]["id"] == "p"
    assert payload["nodes"][0]["id"] == "start"


def test_export_ir_honors_json_indent_option():
    ir = IR(name="p", nodes=[Node(id="start", type="start")], edges=[])
    out = export_ir(ir, options={"export": "json", "json_indent": 0})
    assert "\n" not in out


def test_export_ir_ingredients_mode_outputs_header_and_items():
    ir = IR(
        name="cookie",
        nodes=[Node(id="start", type="start")],
        edges=[],
        items=[
            {
                "id": "flour",
                "name": "Flour",
                "quantity": {"kind": "measure", "value": 250, "unit": "g"},
            }
        ],
        resources=[
            {
                "id": "oven",
                "name": "Oven",
                "quantity": {"kind": "count", "value": 1, "unit": "each"},
            }
        ],
    )
    out = export_ir(ir, options={"export": "items"})
    assert "Items and Resources" in out
    assert "Flour: 250 g" in out
    assert "Oven: 1 each" in out


def test_export_ir_ingredients_mode_outputs_group_labels():
    ir = IR(
        name="cookie",
        nodes=[Node(id="start", type="start")],
        edges=[],
        items={
            "dry": {
                "name": "Dry Ingredients",
                "items": [{"id": "flour", "name": "Flour"}],
            }
        },
    )
    out = export_ir(ir, options={"export": "items"})
    assert "Dry Ingredients" in out
    assert "Flour" in out


def test_export_ir_ingredients_mode_prefers_canonical_items_and_resources():
    ir = IR(
        name="canonical_cookie",
        nodes=[Node(id="start", type="start")],
        edges=[],
        items=[
            {
                "id": "ticket",
                "name": "Work Ticket",
                "quantity": {"kind": "count", "value": 1, "unit": "each"},
            }
        ],
        resources=[
            {
                "id": "mixer",
                "name": "Mixer",
                "quantity": {"kind": "count", "value": 1, "unit": "each"},
            }
        ],
        process_metadata={
            "materials": [{"id": "legacy_flour", "name": "Legacy Flour"}]
        },
    )

    out = export_ir(ir, options={"export": "items"})

    assert "Items and Resources" in out
    assert "Work Ticket: 1 each" in out
    assert "Mixer: 1 each" in out
    assert "Legacy Flour" not in out


def test_export_ir_movement_mode_outputs_inferred_route_summary():
    ir = IR(
        name="cookie",
        nodes=[
            Node(id="start", type="start"),
            Node(id="gather", type="task", location="pantry", produces=["flour"]),
            Node(id="mix", type="task", location="prep_bench", consumes=["flour"]),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="gather"),
            Edge(source="gather", target="mix"),
            Edge(source="mix", target="end"),
        ],
        items=[{"id": "flour", "name": "Flour", "kind": "material"}],
        locations=[
            {
                "id": "pantry",
                "name": "Pantry",
                "spatial": {"x": 0.0, "y": 0.0, "unit": "m"},
            },
            {
                "id": "prep_bench",
                "name": "Prep Bench",
                "spatial": {"x": 3.0, "y": 4.0, "unit": "m"},
            },
        ],
    )
    validate_ir(ir)
    out = export_ir(ir, options={"export": "movement"})
    assert "Inferred Material Movement" in out
    assert "pantry -> prep_bench" in out
    assert "items=flour" in out
    assert "distance=5.00 m" in out


def test_export_ir_movement_mode_includes_people_movement_section():
    ir = IR(
        name="cookie_people",
        nodes=[
            Node(id="start", type="start"),
            Node(
                id="gather",
                type="task",
                location="pantry",
                performed_by=["assistant_baker"],
            ),
            Node(
                id="mix",
                type="task",
                location="prep_bench",
                performed_by=["assistant_baker"],
            ),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="gather"),
            Edge(source="gather", target="mix"),
            Edge(source="mix", target="end"),
        ],
        resources=[
            {"id": "assistant_baker", "name": "Assistant Baker", "kind": "person"}
        ],
        locations=[
            {"id": "pantry", "name": "Pantry"},
            {"id": "prep_bench", "name": "Prep Bench"},
        ],
    )
    validate_ir(ir)

    out = export_ir(ir, options={"export": "movement"})
    assert "Inferred People Movement" in out
    assert "pantry -> prep_bench" in out
    assert "workers=assistant_baker" in out


def test_export_ir_movement_mode_prefers_canonical_relations():
    ir = IR(
        name="canonical_movement",
        nodes=[
            Node(id="start", type="start"),
            Node(
                id="shape",
                type="task",
                location="bench",
                produces=["dough"],
                performed_by=["baker"],
            ),
            Node(
                id="pack",
                type="task",
                location="sealer",
                consumes=["dough"],
                performed_by=["baker"],
            ),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="shape"),
            Edge(source="shape", target="pack"),
            Edge(source="pack", target="end"),
        ],
        items=[{"id": "dough", "name": "Dough", "kind": "material"}],
        resources=[{"id": "baker", "name": "Baker", "kind": "person"}],
        locations=[
            {"id": "bench", "name": "Bench"},
            {"id": "sealer", "name": "Sealer"},
        ],
    )
    validate_ir(ir)

    out = export_ir(ir, options={"export": "movement"})

    assert "Inferred Material Movement" in out
    assert "bench -> sealer" in out
    assert "items=dough" in out
    assert "Inferred People Movement" in out
    assert "workers=baker" in out
