"""Human-readable inferred movement report exporter."""

from __future__ import annotations

from typing import Any

from flo.compiler.analysis import infer_material_movements, aggregate_material_movements


def ir_to_movement_text(ir: Any) -> str:
    """Render inferred material movement as a readable summary."""
    movements = infer_material_movements(ir)
    aggregates = aggregate_material_movements(movements)

    lines: list[str] = ["Inferred Material Movement"]
    lines.append(f"- hops: {len(movements)}")
    lines.append(f"- routes: {len(aggregates)}")

    if not aggregates:
        lines.append("- none")
        return "\n".join(lines)

    for route in aggregates:
        source = str(route.get("from_location") or "unknown")
        target = str(route.get("to_location") or "unknown")
        count = int(route.get("count") or 0)
        items = route.get("items") if isinstance(route.get("items"), list) else []

        detail_parts = [f"count={count}"]
        if items:
            detail_parts.append("items=" + ", ".join(str(item) for item in items))

        distance = route.get("distance")
        if isinstance(distance, dict):
            value = distance.get("value")
            unit = distance.get("unit")
            if isinstance(value, (int, float)) and unit:
                detail_parts.append(f"distance={value:.2f} {unit}")

        lines.append(f"- {source} -> {target} ({'; '.join(detail_parts)})")

    return "\n".join(lines)
