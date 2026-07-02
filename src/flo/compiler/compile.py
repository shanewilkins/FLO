"""Compiler entrypoint for strict adapter-model to canonical IR conversion."""

from typing import Any

from ._adapter_normalization import (
    coerce_adapter_model,
    flatten_source_nodes,
    resolve_process_metadata,
    resolve_process_name,
    resolve_source_nodes,
    validate_adapter_contract,
)
from ._ir_assembly import build_edges, build_nodes_from_flat_source
from .ir.models import IR


def compile_adapter(adapter_model: dict[str, Any]) -> IR:
    """Compile a strict v0.1 adapter payload into canonical `IR`."""
    adapter = coerce_adapter_model(adapter_model)
    validate_adapter_contract(adapter)

    name = resolve_process_name(adapter)
    process_metadata = resolve_process_metadata(adapter)
    source_nodes = resolve_source_nodes(adapter)

    if not isinstance(source_nodes, list):
        raise ValueError("steps must be a list")

    flat_source_nodes = flatten_source_nodes(source_nodes)
    nodes = build_nodes_from_flat_source(flat_source_nodes)
    edges = build_edges(adapter=adapter, nodes=nodes)
    return IR(name=name, nodes=nodes, edges=edges, process_metadata=process_metadata)
