"""SCC condensation utilities moved under compiler.analysis."""

from __future__ import annotations

from typing import Any

from flo.process.ir.models import IR, Node


def _build_adjacency(ir: IR) -> tuple[dict[str, Node], dict[str, list[str]], bool]:
    id_to_node: dict[str, Node] = {n.id: n for n in ir.nodes}
    adj: dict[str, list[str]] = {}
    has_edges = False
    for n in ir.nodes:
        if n.attrs and isinstance(n.attrs, dict) and "edges" in n.attrs:
            targets = n.attrs.get("edges") or []
            if isinstance(targets, list):
                adj[n.id] = [str(t) for t in targets]
                has_edges = True
            else:
                adj[n.id] = []
        else:
            adj[n.id] = []
    return id_to_node, adj, has_edges


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


def _build_condensed_nodes(
    sccs: list[list[str]], id_to_node: dict[str, Node]
) -> tuple[list[Node], dict[str, str]]:
    new_nodes: list[Node] = []
    scc_map: dict[str, str] = {}
    for i, comp in enumerate(sccs):
        if len(comp) == 1:
            nid = comp[0]
            new_nodes.append(id_to_node[nid])
            scc_map[nid] = nid
        else:
            rep_id = f"scc_{i}"
            members = comp
            attrs = {"members": members}
            new_nodes.append(Node(id=rep_id, type="scc", attrs=attrs))
            for m in comp:
                scc_map[m] = rep_id
    return new_nodes, scc_map


def _rebuild_edges(
    new_nodes: list[Node], adj: dict[str, list[str]], scc_map: dict[str, str]
) -> None:
    for node in new_nodes:
        if node.attrs and node.attrs.get("members"):
            outs: list[str] = []
            for member in node.attrs["members"]:
                for tgt in adj.get(member, []):
                    tgt_rep = scc_map.get(tgt, tgt)
                    if tgt_rep != node.id and tgt_rep not in outs:
                        outs.append(tgt_rep)
            node.attrs["edges"] = outs


def scc_condense(ir: IR) -> IR:
    """Condense strongly-connected components in an IR into SCC nodes.

    Returns the original IR if there are no edges or no condensation is needed.
    """
    id_to_node, adj, has_edges = _build_adjacency(ir)
    if not has_edges:
        return ir

    sccs = _tarjan_scc(adj)

    if all(len(c) == 1 for c in sccs):
        return ir

    new_nodes, scc_map = _build_condensed_nodes(sccs, id_to_node)
    _rebuild_edges(new_nodes, adj, scc_map)

    return IR(
        name=ir.name,
        nodes=new_nodes,
        process_version=ir.process_version,
        process_metadata=ir.process_metadata,
        process_owner=ir.process_owner,
        business_units=ir.business_units,
        lanes=ir.lanes,
        items=ir.items,
        resources=ir.resources,
        locations=ir.locations,
        render_intent=ir.render_intent,
    )


def condense_scc(process: Any) -> IR:
    """Compatibility wrapper that accepts a generic process and condenses SCCs.

    Raises NotImplementedError for unsupported input types.
    """
    if not isinstance(process, IR):
        raise NotImplementedError(
            "SCC condensation not implemented for this input type"
        )
    return scc_condense(process)
