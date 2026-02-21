from typing import List, Dict, Tuple


def _build_node_index(nodes: List[Dict]) -> Dict[str, Dict]:
    return {n["id"]: n for n in nodes}


def validate_ir(ir: Dict) -> Tuple[bool, List[str]]:
    """Basic structural validation of the IR.

    Returns (is_valid, diagnostics).
    """
    diags = []
    nodes = ir.get("nodes", [])
    edges = ir.get("edges", [])

    node_idx = _build_node_index(nodes)

    # check unique ids
    ids = [n["id"] for n in nodes]
    dup_ids = set([x for x in ids if ids.count(x) > 1])
    if dup_ids:
        diags.append(f"duplicate node ids: {sorted(list(dup_ids))}")

    # check edge references
    for e in edges:
        s = e.get("source")
        t = e.get("target")
        if s not in node_idx:
            diags.append(f"edge source not found: {s}")
        if t not in node_idx:
            diags.append(f"edge target not found: {t}")

    # decision nodes should have outcome labels on outgoing edges
    decision_nodes = {n["id"] for n in nodes if n.get("kind") == "decision"}
    if decision_nodes:
        out_by_source = {}
        for e in edges:
            out_by_source.setdefault(e.get("source"), []).append(e)
        for d in decision_nodes:
            outs = out_by_source.get(d, [])
            if not outs:
                diags.append(f"decision node '{d}' has no outgoing edges")
            else:
                if any(e.get("outcome") is None for e in outs):
                    diags.append(f"decision node '{d}' has outgoing edge(s) missing 'outcome' labels")

    # recommended: at least one start node
    start_nodes = [n for n in nodes if n.get("kind") == "start"]
    if not start_nodes:
        diags.append("no start node found (recommended)")

    return (len(diags) == 0, diags)


def tarjan_scc(nodes: List[Dict], edges: List[Dict]):
    """Return list of SCCs (each is list of node ids) and a mapping node->scc_id.

    Simple Tarjan implementation operating on node ids and edge list.
    """
    index = 0
    stack = []
    indices = {}
    lowlink = {}
    onstack = set()
    sccs = []

    node_ids = [n["id"] for n in nodes]
    succ = {nid: [] for nid in node_ids}
    for e in edges:
        s = e.get("source")
        t = e.get("target")
        if s in succ:
            succ[s].append(t)

    def strongconnect(v):
        nonlocal index
        indices[v] = index
        lowlink[v] = index
        index += 1
        stack.append(v)
        onstack.add(v)

        for w in succ.get(v, []):
            if w not in indices:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in onstack:
                lowlink[v] = min(lowlink[v], indices[w])

        if lowlink[v] == indices[v]:
            # start a new SCC
            comp = []
            while True:
                w = stack.pop()
                onstack.remove(w)
                comp.append(w)
                if w == v:
                    break
            sccs.append(comp)

    for v in node_ids:
        if v not in indices:
            strongconnect(v)

    node_to_scc = {}
    for i, comp in enumerate(sccs):
        for n in comp:
            node_to_scc[n] = i

    return sccs, node_to_scc


def condense_graph(nodes: List[Dict], edges: List[Dict]):
    """Return condensed DAG nodes (list of comps) and condensed edges.

    Condensed edges include a list of original edges merged between two SCCs.
    """
    sccs, node_to_scc = tarjan_scc(nodes, edges)
    condensed_edges = {}
    for e in edges:
        su = node_to_scc.get(e.get("source"))
        tu = node_to_scc.get(e.get("target"))
        if su is None or tu is None:
            continue
        if su == tu:
            continue
        key = (su, tu)
        condensed_edges.setdefault(key, []).append(e)

    condensed = [ {"id": i, "members": comp} for i, comp in enumerate(sccs) ]
    cond_edges = []
    for (su, tu), origs in condensed_edges.items():
        cond_edges.append({"source_scc": su, "target_scc": tu, "orig_edges": origs})

    return condensed, cond_edges, node_to_scc
