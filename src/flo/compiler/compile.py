"""Compiler stub: adapter -> IR conversion.

The real compiler will convert adapter models into the canonical
FlowProcess IR (instances of `flo.ir.models.FlowProcess`). This stub
is a placeholder that will be implemented as part of v0.1.
"""
from typing import Any, Dict

from .ir.models import IR, Node, Edge


def compile_adapter(adapter_model: Dict[str, Any]) -> IR:
    """Compile an adapter model into a minimal canonical `IR` instance.

    This is a tiny, pragmatic implementation used by the test harness
    to validate wiring; real compilation logic will replace this.
    """
    adapter = adapter_model or {}

    process = adapter.get("process") if isinstance(adapter.get("process"), dict) else {}
    name = process.get("id") or process.get("name") or adapter.get("name") or "unnamed"

    # Create nodes from adapter content when present. Adapter shapes vary,
    # so keep mapping conservative for now.
    nodes: list[Node] = []
    edges: list[Edge] = []

    # Prefer FLO `steps` surface, then legacy `nodes` shape.
    source_nodes = adapter.get("steps") if isinstance(adapter.get("steps"), list) else adapter.get("nodes")

    if isinstance(source_nodes, list):
        for idx, a_node in enumerate(source_nodes):
            nid = a_node.get("id") or f"n{idx}"
            ntype = a_node.get("kind") or a_node.get("type") or "task"
            attrs = a_node.get("attrs") or {}

            # FLO surface fields map into attrs for now.
            if not attrs and isinstance(a_node, dict):
                attrs = {}
                for key in ("name", "lane", "metadata"):
                    if key in a_node:
                        attrs[key] = a_node[key]
                outcomes = a_node.get("outcomes")
                if isinstance(outcomes, dict):
                    attrs["outcomes"] = outcomes

            nodes.append(Node(id=str(nid), type=str(ntype), attrs=attrs))

        # Explicit edge list (preferred when present)
        if isinstance(adapter.get("edges"), list):
            for edge in adapter.get("edges", []):
                if not isinstance(edge, dict):
                    continue
                src = edge.get("source")
                tgt = edge.get("target")
                if src is None or tgt is None:
                    continue
                edges.append(
                    Edge(
                        source=str(src),
                        target=str(tgt),
                        id=str(edge.get("id")) if edge.get("id") is not None else None,
                        outcome=str(edge.get("outcome")) if edge.get("outcome") is not None else None,
                        label=str(edge.get("label")) if edge.get("label") is not None else None,
                        metadata=edge.get("metadata") if isinstance(edge.get("metadata"), dict) else None,
                    )
                )
        else:
            # Decision-outcome shorthand inference when explicit edges are absent.
            for node in nodes:
                attrs = node.attrs or {}
                outcomes = attrs.get("outcomes") if isinstance(attrs, dict) else None
                if not isinstance(outcomes, dict):
                    continue
                for outcome, target in outcomes.items():
                    edges.append(
                        Edge(
                            source=node.id,
                            target=str(target),
                            outcome=str(outcome),
                        )
                    )
    else:
        # Fallback: single node representing the adapter
        node = Node(id="n1", type="task", attrs={"name": name})
        nodes.append(node)

    ir = IR(name=name, nodes=nodes, edges=edges)
    return ir
