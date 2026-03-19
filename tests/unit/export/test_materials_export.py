from __future__ import annotations

from types import SimpleNamespace

import flo.export.ingredients_export as ingredients_export
import flo.export.materials_export as materials_export


def test_materials_export_returns_none_when_metadata_missing():
    ir = SimpleNamespace()
    out = materials_export.ir_to_materials_text(ir)
    assert out == "Materials and Equipment\n- none"


def test_materials_export_adds_section_none_when_collection_has_no_renderable_items():
    ir = SimpleNamespace(
        process_metadata={
            "materials": ["skip", 3],
            "equipment": {},
        }
    )
    out = materials_export.ir_to_materials_text(ir)
    assert "- Materials" in out
    assert "- Equipment" in out
    assert out.count("  - none") == 2


def test_materials_export_renders_nested_groups_and_entries_without_items_label():
    ir = SimpleNamespace(
        process_metadata={
            "materials": {
                "name": "Kitchen Inventory",
                "dry": {
                    "name": "Dry Goods",
                    "items": [
                        {"id": "flour", "name": "Flour", "quantity": {"kind": "measure", "value": 250, "unit": "g"}},
                    ],
                },
                "tools": [{"id": "bowl", "name": "Bowl"}],
                "entries": [{"id": "salt", "name": "Salt"}],
            }
        }
    )

    out = materials_export.ir_to_materials_text(ir)
    assert "Kitchen Inventory" in out
    assert "Dry Goods" in out
    assert "Flour: 250 g" in out
    assert "- tools" in out
    assert "Bowl" in out
    assert "Salt" in out
    assert "- items" not in out


def test_materials_quantity_formatter_covers_dict_and_legacy_shapes():
    assert materials_export._format_quantity({"quantity": {"kind": "count", "value": 2, "unit": "each", "qualifier": "large"}}) == "2 each (large)"
    assert materials_export._format_quantity({"quantity": {"kind": "measure", "value": 1.5, "unit": "kg"}}) == "1.5 kg"
    assert materials_export._format_quantity({"quantity": {"kind": "count", "value": None, "unit": "each"}}) == ""

    assert materials_export._format_quantity({"quantity": 3, "unit": "each", "qualifier": "large"}) == "3 each (large)"
    assert materials_export._format_quantity({"quantity": True, "unit": "each"}) == ""


def test_materials_and_ingredients_aliases_return_same_output():
    ir = SimpleNamespace(process_metadata={"materials": [{"id": "flour", "name": "Flour"}]})

    materials_out = materials_export.ir_to_materials_text(ir)
    ingredients_out = materials_export.ir_to_ingredients_text(ir)
    shim_out = ingredients_export.ir_to_ingredients_text(ir)

    assert materials_out == ingredients_out
    assert shim_out == ingredients_out
    assert ingredients_export.ir_to_materials_text(ir) == materials_out
