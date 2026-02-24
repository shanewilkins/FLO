"""SCC condensation utilities.

Implements a small Tarjan-based SCC detection and a conservative
condensation routine that collapses strongly connected components into
single nodes. The function is intentionally permissive: if the input IR
doesn't expose an adjacency structure (via `attrs['edges']`) it returns the
IR unchanged.
"""
from __future__ import annotations

from typing import List, Dict, Any
from flo.ir.models import IR, Node


def scc_condense(ir: IR) -> IR:
    """Condense strongly connected components in `ir`.

    Expects nodes to have an `attrs` mapping that MAY contain an
    `edges` list of target node ids. If no edges are present, the IR is
    returned unchanged.
    """
    # Build adjacency list if edges information is available
    id_to_node: Dict[str, Node] = {n.id: n for n in ir.nodes}
    adj: Dict[str, List[str]] = {}
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

    if not has_edges:
        return ir

    # Tarjan's algorithm
    index = 0
    index_map: Dict[str, int] = {}
    lowlink: Dict[str, int] = {}
    stack: List[str] = []
    onstack: Dict[str, bool] = {}
    sccs: List[List[str]] = []

    def strongconnect(v: str):
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
            # start a new SCC
            comp: List[str] = []
            while True:
                w = stack.pop()
                onstack[w] = False
                comp.append(w)
                if w == v:
                    break
            sccs.append(comp)

    for nid in id_to_node:
        if nid not in index_map:
            strongconnect(nid)

    # If all SCCs are singletons, nothing to condense
    if all(len(c) == 1 for c in sccs):
        return ir

    # Build condensed nodes: for each SCC create a representative node
    new_nodes: List[Node] = []
    scc_map: Dict[str, str] = {}
    for i, comp in enumerate(sccs):
        if len(comp) == 1:
            nid = comp[0]
            new_nodes.append(id_to_node[nid])
            scc_map[nid] = nid
        else:
            # create a new node id for the SCC
            rep_id = f"scc_{i}"
            # collect combined attrs for debug/traceability
            members = comp
            attrs = {"members": members}
            new_nodes.append(Node(id=rep_id, type="scc", attrs=attrs))
            for m in comp:
                scc_map[m] = rep_id

    # Recreate edges between condensed nodes
    for node in new_nodes:
        if node.attrs and node.attrs.get("members"):
            # aggregate outgoing targets
            outs: List[str] = []
            for member in node.attrs["members"]:
                for tgt in adj.get(member, []):
                    tgt_rep = scc_map.get(tgt, tgt)
                    if tgt_rep != node.id and tgt_rep not in outs:
                        outs.append(tgt_rep)
            node.attrs["edges"] = outs

    return IR(name=ir.name, nodes=new_nodes)


def condense_scc(process: Any) -> IR:
    """Backward-compatible wrapper for older callers.

    The historical API accepted a generic mapping and raised
    `NotImplementedError` for non-IR inputs. Preserve that behavior for
    compatibility while delegating to `scc_condense` for `IR` inputs.
    """
    if not isinstance(process, IR):
        raise NotImplementedError("SCC condensation not implemented for this input type")
    return scc_condense(process)

