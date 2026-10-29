from __future__ import annotations

from types import SimpleNamespace

import flo.process.export.items_export as materials_export


def test_materials_export_returns_none_when_metadata_missing():
    ir = SimpleNamespace()
    out = materials_export.ir_to_items_text(ir)
    assert out == "Items and Resources\n- none"


def test_materials_export_adds_section_none_when_collection_has_no_renderable_items():
    ir = SimpleNamespace(items=["skip", 3], resources={})
    out = materials_export.ir_to_items_text(ir)
    assert "- Items" in out
    assert "- Resources" in out
    assert out.count("  - none") == 2


def test_materials_export_renders_nested_groups_and_entries_without_items_label():
    ir = SimpleNamespace(
        items={
            "name": "Kitchen Inventory",
            "dry": {
                "name": "Dry Goods",
                "items": [
                    {
                        "id": "flour",
                        "name": "Flour",
                        "quantity": {"kind": "measure", "value": 250, "unit": "g"},
                    }
                ],
            },
            "tools": [{"id": "bowl", "name": "Bowl"}],
            "entries": [{"id": "salt", "name": "Salt"}],
        }
    )

    out = materials_export.ir_to_items_text(ir)
    assert "Kitchen Inventory" in out
    assert "Dry Goods" in out
    assert "Flour: 250 g" in out
    assert "- tools" in out
    assert "Bowl" in out
    assert "Salt" in out
    assert "- items" not in out


def test_materials_quantity_formatter_covers_dict_and_legacy_shapes():
    assert (
        materials_export._format_quantity(
            {
                "quantity": {
                    "kind": "count",
                    "value": 2,
                    "unit": "each",
                    "qualifier": "large",
                }
            }
        )
        == "2 each (large)"
    )
    assert (
        materials_export._format_quantity(
            {"quantity": {"kind": "measure", "value": 1.5, "unit": "kg"}}
        )
        == "1.5 kg"
    )
    assert (
        materials_export._format_quantity(
            {"quantity": {"kind": "count", "value": None, "unit": "each"}}
        )
        == ""
    )

    assert (
        materials_export._format_quantity(
            {"quantity": 3, "unit": "each", "qualifier": "large"}
        )
        == ""
    )
    assert materials_export._format_quantity({"quantity": True, "unit": "each"}) == ""


def test_items_export_registry_uses_the_canonical_exporter():
    from flo.process.export import export_ir

    ir = SimpleNamespace(items=[{"id": "flour", "name": "Flour"}])
    assert export_ir(
        ir, options={"export": "items"}
    ) == materials_export.ir_to_items_text(ir)


def test_materials_export_prefers_canonical_items_and_resources():
    ir = SimpleNamespace(
        items=[
            {"id": "ticket", "name": "Work Ticket", "kind": "information"},
            {"id": "flour", "name": "Flour", "kind": "material"},
        ],
        resources=[
            {"id": "baker", "name": "Baker", "kind": "person"},
            {"id": "mixer", "name": "Mixer", "kind": "equipment"},
        ],
        process_metadata={
            "materials": [{"id": "legacy_flour", "name": "Legacy Flour"}]
        },
    )

    out = materials_export.ir_to_items_text(ir)
    assert out.startswith("Items and Resources")
    assert "- Items" in out
    assert "Work Ticket" in out
    assert "Flour" in out
    assert "- Resources" in out
    assert "Baker" in out
    assert "Mixer" in out
    assert "Legacy Flour" not in out
