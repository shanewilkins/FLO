"""Compiler stub: adapter -> IR conversion.

The real compiler will convert adapter models into the canonical
FlowProcess IR (instances of `flo.ir.models.FlowProcess`). This stub
is a placeholder that will be implemented as part of v0.1.
"""
from typing import Any, Dict

from ..ir.models import IR, Node


def compile_adapter(adapter_model: Dict[str, Any]) -> IR:
    """Compile an adapter model into a minimal canonical `IR` instance.

    This is a tiny, pragmatic implementation used by the test harness
    to validate wiring; real compilation logic will replace this.
    """
    adapter = adapter_model or {}
    name = adapter.get("name") or "unnamed"

    # Create nodes from adapter content when present. Adapter shapes vary,
    # so keep mapping conservative for now.
    nodes: list[Node] = []

    # If adapter already has an explicit nodes list, map them.
    if isinstance(adapter.get("nodes"), list):
        for idx, a_node in enumerate(adapter.get("nodes", [])):
            nid = a_node.get("id") or f"n{idx}"
            ntype = a_node.get("kind") or a_node.get("type") or "task"
            attrs = a_node.get("attrs") or {}
            nodes.append(Node(id=str(nid), type=str(ntype), attrs=attrs))
    else:
        # Fallback: single node representing the adapter
        node = Node(id="n1", type="task", attrs={"name": name})
        nodes.append(node)

    ir = IR(name=name, nodes=nodes, schema_aligned=True)
    return ir
