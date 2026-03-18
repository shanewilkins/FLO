import json

from flo.compiler.ir.models import Edge, IR, Node
from flo.export import export_ir


def test_export_ir_defaults_to_json_projection():
    ir = IR(name="p", nodes=[Node(id="start", type="start", attrs={})], edges=[])
    out = export_ir(ir)
    payload = json.loads(out)
    assert payload["process"]["id"] == "p"
    assert payload["nodes"][0]["id"] == "start"


def test_export_ir_honors_json_indent_option():
    ir = IR(name="p", nodes=[Node(id="start", type="start", attrs={})], edges=[])
    out = export_ir(ir, options={"export": "json", "json_indent": 0})
    assert "\n" not in out


def test_export_ir_ingredients_mode_outputs_header_and_items():
    ir = IR(
        name="cookie",
        nodes=[Node(id="start", type="start", attrs={})],
        edges=[],
        process_metadata={
            "materials": [
                {"id": "flour", "name": "Flour", "quantity": {"kind": "measure", "value": 250, "unit": "g"}},
            ],
            "equipment": [
                {"id": "oven", "name": "Oven", "quantity": {"kind": "count", "value": 1, "unit": "each"}},
            ],
        },
    )
    out = export_ir(ir, options={"export": "ingredients"})
    assert "Materials and Equipment" in out
    assert "Flour: 250 g" in out
    assert "Oven: 1 each" in out


def test_export_ir_ingredients_mode_outputs_group_labels():
    ir = IR(
        name="cookie",
        nodes=[Node(id="start", type="start", attrs={})],
        edges=[],
        process_metadata={
            "materials": {
                "dry": {
                    "name": "Dry Ingredients",
                    "items": [
                        {"id": "flour", "name": "Flour"},
                    ],
                }
            }
        },
    )
    out = export_ir(ir, options={"export": "ingredients"})
    assert "Dry Ingredients" in out
    assert "Flour" in out


def test_export_ir_movement_mode_outputs_inferred_route_summary():
    ir = IR(
        name="cookie",
        nodes=[
            Node(id="start", type="start", attrs={}),
            Node(
                id="gather",
                type="task",
                attrs={
                    "location": "pantry",
                    "outputs": ["flour"],
                },
            ),
            Node(
                id="mix",
                type="task",
                attrs={
                    "location": "prep_bench",
                    "inputs": ["flour"],
                },
            ),
            Node(id="end", type="end", attrs={}),
        ],
        edges=[
            Edge(source="gather", target="mix"),
        ],
        process_metadata={
            "locations": [
                {"id": "pantry", "name": "Pantry", "metadata": {"spatial": {"x": 0.0, "y": 0.0, "unit": "m"}}},
                {"id": "prep_bench", "name": "Prep Bench", "metadata": {"spatial": {"x": 3.0, "y": 4.0, "unit": "m"}}},
            ]
        },
    )
    out = export_ir(ir, options={"export": "movement"})
    assert "Inferred Material Movement" in out
    assert "pantry -> prep_bench" in out
    assert "items=flour" in out


def test_export_ir_movement_mode_includes_people_movement_section():
    ir = IR(
        name="cookie_people",
        nodes=[
            Node(
                id="gather",
                type="task",
                attrs={
                    "location": "pantry",
                    "workers": ["assistant_baker"],
                },
            ),
            Node(
                id="mix",
                type="task",
                attrs={
                    "location": "prep_bench",
                    "workers": ["assistant_baker"],
                },
            ),
        ],
        edges=[Edge(source="gather", target="mix")],
    )

    out = export_ir(ir, options={"export": "movement"})
    assert "Inferred People Movement" in out
    assert "pantry -> prep_bench" in out
    assert "workers=assistant_baker" in out
