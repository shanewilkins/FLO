"""Private helpers for IR internal-shape serialization."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import IR, Edge, Node


def ir_to_internal_dict(ir: IR) -> dict[str, Any]:
    """Return internal-shape dict for in-memory canonical IR."""
    output = asdict(ir)
    output["nodes"] = [_node_to_dict(node) for node in ir.nodes]
    output["edges"] = [_edge_to_dict(edge) for edge in ir.edges]
    return output


def ir_from_internal_dict(data: dict[str, Any]) -> IR:
    """Build canonical IR from internal-shape dictionary payload."""
    payload = dict(data)
    payload["nodes"] = [Node(**entry) for entry in payload.get("nodes", [])]
    payload["edges"] = [Edge(**entry) for entry in payload.get("edges", [])]
    return IR(**payload)


def ir_to_internal_json(ir: IR, path: Path | str | None = None) -> str:
    """Serialize internal IR shape to JSON and optionally write to path."""
    payload = ir_to_internal_dict(ir)
    output = json.dumps(payload, indent=2)
    if path:
        Path(path).write_text(output, encoding="utf-8")
    return output


def _node_to_dict(node: Node) -> dict[str, Any]:
    return {
        key: value
        for key, value in asdict(node).items()
        if value is not None or key in {"consumes", "produces", "performed_by", "uses"}
    }


def _edge_to_dict(edge: Edge) -> dict[str, Any]:
    return {key: value for key, value in asdict(edge).items() if value is not None}
