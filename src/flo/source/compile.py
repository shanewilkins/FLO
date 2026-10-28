"""Compiler entrypoint for strict adapter-model to canonical IR conversion."""

from typing import Any

from flo.process.ir.models import IR

from ._adapter_normalization import (
    flatten_source_nodes,
    resolve_business_units,
    resolve_items,
    resolve_lanes,
    resolve_locations,
    resolve_process_extensions,
    resolve_process_lead_time,
    resolve_process_metadata,
    resolve_process_name,
    resolve_process_owner,
    resolve_process_version,
    resolve_render_intent,
    resolve_resources,
    resolve_source_nodes,
    validate_adapter_contract,
)
from ._ir_assembly import build_edges, build_nodes_from_flat_source
from .composition import pop_source_composition


def compile_adapter(adapter_model: dict[str, Any]) -> IR:
    """Compile a strict v0.1 adapter payload into canonical `IR`."""
    adapter = dict(adapter_model or {})
    pop_source_composition(adapter, source_path=None)
    validate_adapter_contract(adapter)

    name = resolve_process_name(adapter)
    process_version = resolve_process_version(adapter)
    process_metadata = resolve_process_metadata(adapter)
    process_owner = resolve_process_owner(adapter)
    business_units = resolve_business_units(adapter)
    lanes = resolve_lanes(adapter)
    items = resolve_items(adapter)
    resources = resolve_resources(adapter)
    locations = resolve_locations(adapter)
    render_intent = resolve_render_intent(adapter)
    lead_time = resolve_process_lead_time(adapter)
    extensions = resolve_process_extensions(adapter)
    source_nodes = resolve_source_nodes(adapter)

    flat_source_nodes = flatten_source_nodes(source_nodes)
    nodes = build_nodes_from_flat_source(flat_source_nodes)
    edges = build_edges(adapter=adapter, nodes=nodes)
    return IR(
        name=name,
        nodes=nodes,
        edges=edges,
        process_version=process_version,
        process_metadata=process_metadata,
        process_owner=process_owner,
        business_units=business_units,
        lanes=lanes,
        items=items,
        resources=resources,
        locations=locations,
        render_intent=render_intent,
        lead_time=lead_time,
        extensions=extensions,
    )
