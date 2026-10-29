"""Strongly connected component projection over canonical IR edges."""

from dataclasses import replace

from flo.process.ir.models import IR, Node


def _tarjan_scc(adj: dict[str, list[str]]) -> list[list[str]]:
    index = 0
    index_map: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    stack: list[str] = []
    onstack: dict[str, bool] = {}
    sccs: list[list[str]] = []

    def strongconnect(v: str) -> None:
        nonlocal index
        index_map[v] = index
        lowlink[v] = index
        index += 1
        stack.append(v)
        onstack[v] = True

        for w in adj.get(v, []):
            if w not in index_map:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif onstack.get(w):
                lowlink[v] = min(lowlink[v], index_map[w])

        if lowlink[v] == index_map[v]:
            comp: list[str] = []
            while True:
                w = stack.pop()
                onstack[w] = False
                comp.append(w)
                if w == v:
                    break
            sccs.append(comp)

    for nid in adj:
        if nid not in index_map:
            strongconnect(nid)
    return sccs


def scc_condense(ir: IR) -> IR:
    """Collapse cycles while preserving canonical context and external edges."""
    if not isinstance(ir, IR):
        raise TypeError("SCC condensation requires an IR instance")
    if not ir.edges:
        return ir
    adjacency = {node.id: [] for node in ir.nodes}
    for edge in ir.edges:
        adjacency[edge.source].append(edge.target)
    components = _tarjan_scc(adjacency)
    if all(len(component) == 1 for component in components):
        return ir
    by_id = {node.id: node for node in ir.nodes}
    nodes = []
    representatives = {}
    for index, members in enumerate(components):
        if len(members) == 1:
            node = by_id[members[0]]
        else:
            node = Node(
                id=f"scc_{index}", type="scc", extensions={"flo:scc_members": members}
            )
        nodes.append(node)
        representatives.update(dict.fromkeys(members, node.id))
    edges = []
    for edge in ir.edges:
        source, target = representatives[edge.source], representatives[edge.target]
        if source != target:
            projected = replace(edge, source=source, target=target)
            if projected not in edges:
                edges.append(projected)
    return replace(ir, nodes=nodes, edges=edges)
