"""Movement inference helpers for material and people flow projections."""

from __future__ import annotations

from math import sqrt
from typing import Any, TypeGuard


def infer_material_movements(process: Any) -> list[dict[str, Any]]:
    """Infer material movement hops from control-flow transitions.

    A movement is inferred when:
    - source and target nodes both declare `location`
    - locations differ

    Material items are inferred as the intersection of source `outputs` and
    target `inputs`.
    """
    return _infer_movements(
        process=process,
        source_field="outputs",
        target_field="inputs",
        entities_field="items",
        require_shared_entities=False,
    )


def infer_people_movements(process: Any) -> list[dict[str, Any]]:
    """Infer people movement hops from worker continuity across edges.

    A movement is inferred when:
    - source and target nodes both declare `location`
    - locations differ
    - source and target share at least one worker id
    """
    return _infer_movements(
        process=process,
        source_field="workers",
        target_field="workers",
        entities_field="workers",
        require_shared_entities=True,
    )


def aggregate_material_movements(movements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate inferred movements by route + item set."""
    return _aggregate_movements(
        movements=movements,
        entities_field="items",
        key_by_entities=True,
    )


def aggregate_people_movements(movements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate inferred people movements by route and merge worker sets."""
    return _aggregate_movements(
        movements=movements,
        entities_field="workers",
        key_by_entities=False,
    )


def aggregate_people_movements_by_worker(movements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate inferred people movements by route and individual worker."""
    worker_movements: list[dict[str, Any]] = []
    for movement in movements:
        workers = _as_text_list(movement.get("workers"))
        for worker in workers:
            worker_movement = dict(movement)
            worker_movement["workers"] = [worker]
            worker_movements.append(worker_movement)

    return _aggregate_movements(
        movements=worker_movements,
        entities_field="workers",
        key_by_entities=True,
    )


def _infer_movements(
    process: Any,
    source_field: str,
    target_field: str,
    entities_field: str,
    require_shared_entities: bool,
) -> list[dict[str, Any]]:
    nodes_by_id = _extract_node_attrs_by_id(process)
    edges = _extract_edges(process)
    locations = extract_location_spatial_index(process)

    movements: list[dict[str, Any]] = []
    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if not source or not target:
            continue

        source_attrs = nodes_by_id.get(source, {})
        target_attrs = nodes_by_id.get(target, {})
        source_location = _as_text(source_attrs.get("location"))
        target_location = _as_text(target_attrs.get("location"))
        if not source_location or not target_location or source_location == target_location:
            continue

        source_entities = _as_text_list(source_attrs.get(source_field))
        target_entities = _as_text_list(target_attrs.get(target_field))
        entities = _shared_text_values(source_entities, target_entities)
        if require_shared_entities and not entities:
            continue

        movement = _new_movement_record(
            source=source,
            target=target,
            source_location=source_location,
            target_location=target_location,
            entities_field=entities_field,
            entities=entities,
            location_index=locations,
        )
        movements.append(movement)

    return movements


def _new_movement_record(
    source: str,
    target: str,
    source_location: str,
    target_location: str,
    entities_field: str,
    entities: list[str],
    location_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    distance_value, distance_unit = _distance_between_locations(
        source_location=source_location,
        target_location=target_location,
        location_index=location_index,
    )

    movement: dict[str, Any] = {
        "source_node": source,
        "target_node": target,
        "from_location": source_location,
        "to_location": target_location,
        entities_field: entities,
    }

    if distance_value is not None and distance_unit is not None:
        movement["distance"] = {
            "value": distance_value,
            "unit": distance_unit,
        }
    return movement


def _aggregate_movements(
    movements: list[dict[str, Any]],
    entities_field: str,
    key_by_entities: bool,
) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str, tuple[str, ...]], dict[str, Any]] = {}

    for movement in movements:
        key = _movement_bucket_key(
            movement,
            entities_field=entities_field,
            key_by_entities=key_by_entities,
        )
        if key is None:
            continue
        source, target, entities = key

        bucket = buckets.get(key)
        if bucket is None:
            bucket = _new_movement_bucket(
                source=source,
                target=target,
                entities=entities,
                entities_field=entities_field,
                movement=movement,
            )
            buckets[key] = bucket

        bucket["count"] += 1
        if not key_by_entities:
            _merge_bucket_entities(bucket, movement=movement, entities_field=entities_field)

    return sorted(buckets.values(), key=_movement_bucket_sort_key)


def _movement_bucket_key(
    movement: dict[str, Any],
    entities_field: str,
    key_by_entities: bool,
) -> tuple[str, str, tuple[str, ...]] | None:
    source = str(movement.get("from_location") or "")
    target = str(movement.get("to_location") or "")
    if not source or not target:
        return None
    entities = _sorted_text_values(movement.get(entities_field) if key_by_entities else [])
    return source, target, entities


def _new_movement_bucket(
    source: str,
    target: str,
    entities: tuple[str, ...],
    entities_field: str,
    movement: dict[str, Any],
) -> dict[str, Any]:
    bucket: dict[str, Any] = {
        "from_location": source,
        "to_location": target,
        entities_field: list(entities),
        "count": 0,
    }
    distance = movement.get("distance")
    if isinstance(distance, dict):
        bucket["distance"] = distance
    return bucket


def _movement_bucket_sort_key(item: dict[str, Any]) -> tuple[int, str, str]:
    return (
        -int(item.get("count") or 0),
        str(item.get("from_location") or ""),
        str(item.get("to_location") or ""),
    )


def _merge_bucket_entities(bucket: dict[str, Any], movement: dict[str, Any], entities_field: str) -> None:
    merged_values = _sorted_text_values(
        list(bucket.get(entities_field) or []) + list(movement.get(entities_field) or [])
    )
    bucket[entities_field] = list(merged_values)


def _shared_text_values(source_values: list[str], target_values: list[str]) -> list[str]:
    target_set = set(target_values)
    shared: list[str] = []
    for value in source_values:
        if value in target_set and value not in shared:
            shared.append(value)
    return shared


def _sorted_text_values(values: Any) -> tuple[str, ...]:
    return tuple(sorted({str(item) for item in values or [] if str(item)}))


def extract_location_spatial_index(process: Any) -> dict[str, dict[str, Any]]:
    """Return location_id -> {name, kind, x, y, unit} from process metadata locations."""
    process_metadata = _extract_process_metadata(process)
    collection = process_metadata.get("locations") if isinstance(process_metadata, dict) else None

    index: dict[str, dict[str, Any]] = {}
    for item in _iter_resource_items(collection):
        if not isinstance(item, dict):
            continue
        location_id = _as_text(item.get("id"))
        if not location_id:
            continue

        spatial = _extract_spatial(item)
        entry: dict[str, Any] = {"name": _as_text(item.get("name")) or location_id}
        kind = _extract_location_kind(item)
        if kind is not None:
            entry["kind"] = kind
        if isinstance(spatial, dict):
            x = spatial.get("x")
            y = spatial.get("y")
            unit = _as_text(spatial.get("unit")) or "m"
            if _is_number(x) and _is_number(y):
                entry["x"] = float(x)
                entry["y"] = float(y)
                entry["unit"] = unit
        index[location_id] = entry

    return index


def _extract_node_attrs_by_id(process: Any) -> dict[str, dict[str, Any]]:
    nodes = _extract_nodes(process)
    out: dict[str, dict[str, Any]] = {}
    for node in nodes:
        node_id = _as_text(node.get("id"))
        if not node_id:
            continue
        raw_attrs = node.get("attrs")
        if isinstance(raw_attrs, dict):
            attrs: dict[str, Any] = raw_attrs
        else:
            attrs = {
                key: value
                for key, value in node.items()
                if key not in {"id", "type", "kind"}
            }
        out[node_id] = attrs
    return out


def _extract_nodes(process: Any) -> list[dict[str, Any]]:
    if hasattr(process, "nodes"):
        nodes: list[dict[str, Any]] = []
        for node in getattr(process, "nodes", []) or []:
            attrs = getattr(node, "attrs", None)
            node_entry = {
                "id": getattr(node, "id", ""),
                "type": getattr(node, "type", "task"),
                "attrs": attrs if isinstance(attrs, dict) else {},
            }
            nodes.append(node_entry)
        return nodes

    if isinstance(process, dict):
        nodes_raw = process.get("nodes")
        if isinstance(nodes_raw, list):
            return [node for node in nodes_raw if isinstance(node, dict)]
    return []


def _extract_edges(process: Any) -> list[dict[str, Any]]:
    if hasattr(process, "edges"):
        edges: list[dict[str, Any]] = []
        for edge in getattr(process, "edges", []) or []:
            edges.append(
                {
                    "source": getattr(edge, "source", None),
                    "target": getattr(edge, "target", None),
                    "outcome": getattr(edge, "outcome", None),
                    "label": getattr(edge, "label", None),
                }
            )
        return edges

    if isinstance(process, dict):
        edges_raw = process.get("edges") or process.get("transitions")
        if isinstance(edges_raw, list):
            return [edge for edge in edges_raw if isinstance(edge, dict)]
    return []


def _extract_process_metadata(process: Any) -> dict[str, Any]:
    if hasattr(process, "process_metadata"):
        metadata = getattr(process, "process_metadata", None)
        return metadata if isinstance(metadata, dict) else {}

    if isinstance(process, dict):
        proc = process.get("process")
        if isinstance(proc, dict):
            metadata = proc.get("metadata")
            return metadata if isinstance(metadata, dict) else {}
    return {}


def _iter_resource_items(collection: Any):
    if isinstance(collection, list):
        for item in collection:
            yield item
        return

    if not isinstance(collection, dict):
        return

    for key, value in collection.items():
        if key == "name":
            continue
        if key in {"items", "entries"} and isinstance(value, list):
            for item in value:
                yield item
            continue
        if isinstance(value, (dict, list)):
            yield from _iter_resource_items(value)


def _extract_spatial(resource: dict[str, Any]) -> dict[str, Any] | None:
    metadata = resource.get("metadata")
    if isinstance(metadata, dict) and isinstance(metadata.get("spatial"), dict):
        return metadata.get("spatial")

    if "x" in resource or "y" in resource:
        return {
            "x": resource.get("x"),
            "y": resource.get("y"),
            "unit": resource.get("unit"),
        }

    return None


def _extract_location_kind(resource: dict[str, Any]) -> str | None:
    direct_kind = _as_text(resource.get("kind"))
    if direct_kind is not None:
        return direct_kind

    metadata = resource.get("metadata")
    if not isinstance(metadata, dict):
        return None

    for key in ("kind", "location_kind", "type"):
        kind = _as_text(metadata.get(key))
        if kind is not None:
            return kind
    return None


def _distance_between_locations(
    source_location: str,
    target_location: str,
    location_index: dict[str, dict[str, Any]],
) -> tuple[float | None, str | None]:
    source = location_index.get(source_location)
    target = location_index.get(target_location)
    if not isinstance(source, dict) or not isinstance(target, dict):
        return None, None

    sx = source.get("x")
    sy = source.get("y")
    tx = target.get("x")
    ty = target.get("y")
    su = _as_text(source.get("unit"))
    tu = _as_text(target.get("unit"))

    if not (_is_number(sx) and _is_number(sy) and _is_number(tx) and _is_number(ty)):
        return None, None
    if not su or not tu or su != tu:
        return None, None

    return sqrt((float(tx) - float(sx)) ** 2 + (float(ty) - float(sy)) ** 2), su


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = _as_text(item)
        if text:
            out.append(text)
    return out


def _is_number(value: Any) -> TypeGuard[int | float]:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
