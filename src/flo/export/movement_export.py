"""Human-readable inferred movement report exporter."""

from __future__ import annotations

from typing import Any

from flo.compiler.analysis import (
    infer_material_movements,
    aggregate_material_movements,
    infer_people_movements,
    aggregate_people_movements,
)


def ir_to_movement_text(ir: Any) -> str:
    """Render inferred material and people movement as a readable summary."""
    material_movements = infer_material_movements(ir)
    material_aggregates = aggregate_material_movements(material_movements)
    people_movements = infer_people_movements(ir)
    people_aggregates = aggregate_people_movements(people_movements)

    lines: list[str] = []
    _append_movement_section(
        lines=lines,
        title="Inferred Material Movement",
        movements=material_movements,
        routes=material_aggregates,
        entities_field="items",
    )
    lines.append("")
    _append_movement_section(
        lines=lines,
        title="Inferred People Movement",
        movements=people_movements,
        routes=people_aggregates,
        entities_field="workers",
    )
    return "\n".join(lines)


def _append_movement_section(
    lines: list[str],
    title: str,
    movements: list[dict[str, Any]],
    routes: list[dict[str, Any]],
    entities_field: str,
) -> None:
    lines.append(title)
    lines.append(f"- hops: {len(movements)}")
    lines.append(f"- routes: {len(routes)}")

    if not routes:
        lines.append("- none")
        return

    for route in routes:
        source = str(route.get("from_location") or "unknown")
        target = str(route.get("to_location") or "unknown")
        count = int(route.get("count") or 0)
        entities = route.get(entities_field) if isinstance(route.get(entities_field), list) else []

        detail_parts = [f"count={count}"]
        if entities:
            detail_parts.append(f"{entities_field}=" + ", ".join(str(item) for item in entities))

        distance = route.get("distance")
        if isinstance(distance, dict):
            value = distance.get("value")
            unit = distance.get("unit")
            if isinstance(value, (int, float)) and unit:
                detail_parts.append(f"distance={value:.2f} {unit}")

        lines.append(f"- {source} -> {target} ({'; '.join(detail_parts)})")
