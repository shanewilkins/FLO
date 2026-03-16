import json

from flo.compiler.ir.models import IR, Node
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
            ]
        },
    )
    out = export_ir(ir, options={"export": "ingredients"})
    assert "Materials and Ingredients" in out
    assert "Flour: 250 g" in out


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
