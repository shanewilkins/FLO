"""Compiler stub: adapter -> IR conversion.

The real compiler will convert adapter models into the canonical
FlowProcess IR (instances of `flo.ir.models.FlowProcess`). This stub
is a placeholder that will be implemented as part of v0.1.
"""

from typing import Any, Dict

from ._adapter_normalization import (
    coerce_adapter_model,
    flatten_source_nodes,
    resolve_process_metadata,
    resolve_process_name,
    resolve_source_nodes,
)
from ._ir_assembly import build_edges, build_nodes_from_flat_source
from .ir.models import IR, Node


def compile_adapter(adapter_model: Dict[str, Any]) -> IR:
    """Compile an adapter model into a minimal canonical `IR` instance.

    This is a tiny, pragmatic implementation used by the test harness
    to validate wiring; real compilation logic will replace this.
    """
    adapter = coerce_adapter_model(adapter_model)
    name = resolve_process_name(adapter)
    process_metadata = resolve_process_metadata(adapter)
    source_nodes = resolve_source_nodes(adapter)

    if not isinstance(source_nodes, list):
        fallback_node = Node(id="n1", type="task", attrs={"name": name})
        return IR(
            name=name,
            nodes=[fallback_node],
            edges=[],
            process_metadata=process_metadata,
        )

    flat_source_nodes = flatten_source_nodes(source_nodes)
    nodes = build_nodes_from_flat_source(flat_source_nodes)
    edges = build_edges(adapter=adapter, nodes=nodes)
    return IR(name=name, nodes=nodes, edges=edges, process_metadata=process_metadata)
