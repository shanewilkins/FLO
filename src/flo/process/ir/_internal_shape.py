"""Private helpers for IR internal-shape serialization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import IR, Edge, Node


def ir_to_internal_dict(ir: IR) -> dict[str, Any]:
    """Return internal-shape dict for in-memory canonical IR."""
    return {
        "name": ir.name,
        "process_version": ir.process_version,
        "nodes": [_node_to_dict(node) for node in ir.nodes],
        "edges": [_edge_to_dict(edge) for edge in ir.edges],
        "process_metadata": ir.process_metadata or {},
        "process_owner": ir.process_owner,
        "business_units": ir.business_units,
        "lanes": ir.lanes,
        "items": ir.items,
        "resources": ir.resources,
        "locations": ir.locations,
        "render_intent": ir.render_intent,
        "lead_time": ir.lead_time,
        "extensions": ir.extensions,
    }


def ir_from_internal_dict(data: dict[str, Any]) -> IR:
    """Build canonical IR from internal-shape dictionary payload."""
    nodes: list[Node] = []
    for node_data in data.get("nodes", []):
        if not isinstance(node_data, dict):
            continue
        nodes.append(
            Node(
                id=node_data.get("id", ""),
                type=node_data.get("type", ""),
                attrs=node_data.get("attrs", {}),
                subprocess_parent=node_data.get("subprocess_parent"),
                name=node_data.get("name"),
                description=node_data.get("description"),
                lane=node_data.get("lane"),
                location=node_data.get("location"),
                consumes=node_data.get("consumes", []),
                produces=node_data.get("produces", []),
                performed_by=node_data.get("performed_by", []),
                uses=node_data.get("uses", []),
                value_class=node_data.get("value_class"),
                cycle_time=node_data.get("cycle_time"),
                wait_time=node_data.get("wait_time"),
                changeover_time=node_data.get("changeover_time"),
                extensions=node_data.get("extensions"),
            )
        )

    edges: list[Edge] = []
    for edge_data in data.get("edges", []):
        if not isinstance(edge_data, dict):
            continue
        edges.append(
            Edge(
                source=edge_data.get("source", ""),
                target=edge_data.get("target", ""),
                id=edge_data.get("id"),
                outcome=edge_data.get("outcome"),
                route=edge_data.get("route"),
                label=edge_data.get("label"),
                handoff=edge_data.get("handoff"),
                rework=edge_data.get("rework"),
                extensions=edge_data.get("extensions"),
            )
        )

    process_metadata = data.get("process_metadata")
    if not isinstance(process_metadata, dict):
        process_metadata = None

    return IR(
        name=data.get("name", ""),
        nodes=nodes,
        edges=edges,
        process_version=data.get("process_version"),
        process_metadata=process_metadata,
        process_owner=data.get("process_owner"),
        business_units=data.get("business_units", []),
        lanes=data.get("lanes", []),
        items=data.get("items"),
        resources=data.get("resources"),
        locations=data.get("locations"),
        render_intent=data.get("render_intent"),
        lead_time=data.get("lead_time"),
        extensions=data.get("extensions"),
    )


def ir_to_internal_json(ir: IR, path: Path | str | None = None) -> str:
    """Serialize internal IR shape to JSON and optionally write to path."""
    payload = ir_to_internal_dict(ir)
    output = json.dumps(payload, indent=2)
    if path:
        Path(path).write_text(output, encoding="utf-8")
    return output


def _node_to_dict(node: Node) -> dict[str, Any]:
    output: dict[str, Any] = {
        "id": node.id,
        "type": node.type,
        "attrs": node.attrs or {},
    }
    if node.subprocess_parent is not None:
        output["subprocess_parent"] = node.subprocess_parent
    for key in (
        "name",
        "description",
        "lane",
        "location",
        "value_class",
        "cycle_time",
        "wait_time",
        "changeover_time",
        "extensions",
    ):
        value = getattr(node, key)
        if value is not None:
            output[key] = value
    for key in ("consumes", "produces", "performed_by", "uses"):
        value = getattr(node, key)
        if value or not isinstance(value, list):
            output[key] = value
    return output


def _edge_to_dict(edge: Edge) -> dict[str, Any]:
    output: dict[str, Any] = {"source": edge.source, "target": edge.target}
    if edge.id is not None:
        output["id"] = edge.id
    if edge.outcome is not None:
        output["outcome"] = edge.outcome
    if edge.route is not None:
        output["route"] = edge.route
    if edge.label is not None:
        output["label"] = edge.label
    if edge.handoff is not None:
        output["handoff"] = edge.handoff
    if edge.rework is not None:
        output["rework"] = edge.rework
    if edge.extensions is not None:
        output["extensions"] = edge.extensions
    return output
