"""Strongly connected component projection over canonical IR edges."""

from dataclasses import replace

from flo.process.graph import GraphFacts
from flo.process.ir.models import IR, Node


def scc_condense(ir: IR) -> IR:
    """Collapse cycles while preserving canonical context and external edges."""
    if not isinstance(ir, IR):
        raise TypeError("SCC condensation requires an IR instance")
    if not ir.edges:
        return ir
    graph = GraphFacts.build((node.id for node in ir.nodes), ir.edges)
    components = graph.components()
    if all(len(component) == 1 for component in components):
        return ir
    by_id = {node.id: node for node in ir.nodes}
    nodes = []
    representatives = {}
    reserved_ids = set(by_id)
    for index, members in enumerate(components):
        if len(members) == 1:
            node = by_id[members[0]]
        else:
            synthetic_id = f"scc_{index}"
            while synthetic_id in reserved_ids:
                synthetic_id += "_"
            reserved_ids.add(synthetic_id)
            node = Node(
                id=synthetic_id,
                type="scc",
                extensions={"flo:scc_members": list(members)},
            )
        nodes.append(node)
        representatives.update(dict.fromkeys(members, node.id))
    component_sizes = {
        member: len(members) for members in components for member in members
    }
    edges = []
    for edge in ir.edges:
        source, target = representatives[edge.source], representatives[edge.target]
        if source != target or component_sizes[edge.source] == 1:
            projected = replace(edge, source=source, target=target)
            edges.append(projected)
    return replace(ir, nodes=nodes, edges=edges)
