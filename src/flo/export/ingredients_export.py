"""Human-readable ingredients/materials list exporter."""

from __future__ import annotations

from typing import Any


def ir_to_ingredients_text(ir: Any) -> str:
    """Render a formatted materials/ingredients list from process metadata."""
    process_metadata = getattr(ir, "process_metadata", None)
    materials = process_metadata.get("materials") if isinstance(process_metadata, dict) else None

    lines: list[str] = ["Materials and Ingredients"]
    if materials is None:
        lines.append("- none")
        return "\n".join(lines)

    _append_collection(lines=lines, label=None, collection=materials, level=0)
    if len(lines) == 1:
        lines.append("- none")

    return "\n".join(lines)


def _append_collection(lines: list[str], label: str | None, collection: Any, level: int) -> None:
    indent = "  " * level

    if isinstance(collection, list):
        if label:
            lines.append(f"{indent}- {label}")
            indent = "  " * (level + 1)
        for item in collection:
            if isinstance(item, dict):
                lines.append(f"{indent}- {_format_resource_item(item)}")
        return

    if not isinstance(collection, dict):
        return

    group_label = collection.get("name") if isinstance(collection.get("name"), str) else label
    if group_label:
        lines.append(f"{indent}- {group_label}")
        level += 1

    for key, value in collection.items():
        if key == "name":
            continue
        child_label = None if key in {"items", "entries"} else str(key)
        _append_collection(lines=lines, label=child_label, collection=value, level=level)


def _format_resource_item(item: dict[str, Any]) -> str:
    name = str(item.get("name") or item.get("id") or "item")
    quantity_text = _format_quantity(item)
    if quantity_text:
        return f"{name}: {quantity_text}"
    return name


def _format_quantity(item: dict[str, Any]) -> str:
    quantity = item.get("quantity")
    if isinstance(quantity, dict):
        kind = str(quantity.get("kind") or "").strip().lower()
        value = quantity.get("value")
        unit = quantity.get("unit")
        qualifier = quantity.get("qualifier")
        if value is None:
            return ""
        base = f"{value} {unit}".strip() if unit else str(value)
        if kind == "count" and qualifier:
            return f"{base} ({qualifier})"
        return base

    # Legacy shape support for examples still using kind/quantity/unit at item level.
    legacy_value = item.get("quantity")
    legacy_unit = item.get("unit")
    legacy_qualifier = item.get("qualifier")
    if isinstance(legacy_value, (int, float)) and not isinstance(legacy_value, bool):
        base = f"{legacy_value} {legacy_unit}".strip() if legacy_unit else str(legacy_value)
        if legacy_qualifier:
            return f"{base} ({legacy_qualifier})"
        return base

    return ""
