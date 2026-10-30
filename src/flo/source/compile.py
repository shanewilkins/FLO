"""Strict source boundary to canonical dataclass IR assembly."""

from typing import Any

from flo.process.ir.models import IR

from ._adapter_normalization import flatten_source_nodes, validate_adapter_contract
from ._ir_assembly import build_edges, build_nodes_from_flat_source
from .composition import pop_source_composition


def compile_adapter(adapter_model: dict[str, Any]) -> IR:
    """Validate authored shapes once and assemble only canonical fields."""
    adapter = dict(adapter_model)
    pop_source_composition(adapter, source_path=None)
    validate_adapter_contract(adapter)
    process = adapter["process"]
    flat_steps = flatten_source_nodes(adapter["steps"])
    return IR(
        name=process["id"],
        nodes=build_nodes_from_flat_source(flat_steps),
        edges=build_edges(adapter=adapter, nodes=flat_steps),
        process_version=process.get("version"),
        process_metadata={"process_id": process["id"], "process_name": process["name"]},
        process_owner=process.get("owner"),
        business_units=process.get("business_units") or [],
        lanes=adapter.get("lanes"),
        items=process.get("items"),
        resources=process.get("resources"),
        locations=process.get("locations"),
        render_intent=process.get("render"),
        lead_time=process.get("lead_time"),
        extensions=process.get("extensions"),
    )
