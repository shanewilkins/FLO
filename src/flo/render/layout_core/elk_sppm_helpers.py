"""SPPM-specific ELK request helpers extracted from the core layout module."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .elk_contracts import ElkLayoutEdge, ElkLayoutLane, ElkLayoutRequest
from .sppm_strategy import current_sppm_layout_strategy, sppm_spacing_values


def _sppm_spacing_layout_options() -> dict[str, str]:
    node_spacing, layer_spacing = sppm_spacing_values()
    return {
        "elk.spacing.nodeNode": node_spacing,
        "elk.layered.spacing.nodeNodeBetweenLayers": layer_spacing,
    }


def _sppm_port_id(node_id: str, side: str) -> str:
    return f"{node_id}__port_{side.lower()}"


def _root_layout_options(request: ElkLayoutRequest) -> dict[str, str]:
    options = {"elk.algorithm": "layered", "elk.direction": request.direction}
    if request.diagram == "sppm":
        options["elk.layered.considerModelOrder.strategy"] = "NODES_AND_EDGES"
        options["elk.layered.crossingMinimization.forceNodeModelOrder"] = "true"
        options["elk.layered.feedbackEdges"] = "true"
        options["elk.edgeRouting"] = "ORTHOGONAL"
        options.update(_sppm_spacing_layout_options())
        options["elk.layered.nodePlacement.strategy"] = "BRANDES_KOEPF"
        options["elk.layered.nodePlacement.bk.fixedAlignment"] = "TOP"
        options["elk.layered.nodePlacement.favorStraightEdges"] = "true"
        options["elk.partitioning.activate"] = "true"
    if request.lanes and not _synthetic_sppm_rows(request=request):
        options["elk.hierarchyHandling"] = "INCLUDE_CHILDREN"
    return options


def _sppm_branch_anchor_helpers(
    *, request: ElkLayoutRequest
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    node_by_id = {node.id: node for node in request.nodes}
    helper_nodes: list[dict[str, Any]] = []
    helper_edges: list[dict[str, Any]] = []

    branch_edges = [edge for edge in request.edges if edge.rework_variant == "branch"]
    for idx, branch_edge in enumerate(branch_edges):
        source_node = node_by_id.get(branch_edge.source_id)
        if source_node is None:
            continue
        anchor_id = f"__sppm_branch_anchor_{idx}_{branch_edge.source_id}_{branch_edge.target_id}"
        partition = (
            source_node.partition_index
            if source_node.partition_index is not None
            else 0
        )
        helper_nodes.append(
            {
                "id": anchor_id,
                "width": 2,
                "height": 2,
                "layoutOptions": {
                    "elk.partitioning.partition": str(partition),
                },
            }
        )
        helper_edges.append(
            {
                "id": f"__sppm_helper_a_{idx}",
                "sources": [_sppm_port_id(branch_edge.source_id, "SOUTH")],
                "targets": [anchor_id],
            }
        )
        helper_edges.append(
            {
                "id": f"__sppm_helper_b_{idx}",
                "sources": [anchor_id],
                "targets": [_sppm_port_id(branch_edge.target_id, "NORTH")],
            }
        )

    return helper_nodes, helper_edges


def _synthetic_sppm_rows(*, request: ElkLayoutRequest) -> bool:
    if request.diagram != "sppm":
        return False
    lane_ids = {lane.id for lane in request.lanes}
    return {
        "__sppm_row_mainline",
        "__sppm_row_rework",
    }.issubset(lane_ids)


def _preserves_lane_structure(
    process: dict[str, Any] | Any, nodes: list[dict[str, Any]]
) -> bool:
    if any(str(node.get("lane") or "").strip() for node in nodes):
        return True
    if not isinstance(process, dict):
        return False
    raw_lanes = process.get("lanes")
    if isinstance(raw_lanes, list) and raw_lanes:
        return True
    process_block = process.get("process")
    if not isinstance(process_block, dict):
        return False
    nested_lanes = process_block.get("lanes")
    return isinstance(nested_lanes, list) and bool(nested_lanes)


def _node_kind_map(nodes: list[dict[str, Any]]) -> dict[str, str]:
    return {
        str(node.get("id") or ""): str(
            node.get("kind") or node.get("type") or "task"
        ).lower()
        for node in nodes
        if str(node.get("id") or "")
    }


def _sppm_synthetic_row_lanes(
    *,
    nodes: list[dict[str, Any]],
    edges: tuple[ElkLayoutEdge, ...],
) -> tuple[ElkLayoutLane, ...]:
    node_ids = [
        str(node.get("id") or "") for node in nodes if str(node.get("id") or "")
    ]
    if not node_ids:
        return ()

    branch_targets, return_sources = _sppm_rework_endpoints(edges=edges)
    if not branch_targets:
        return ()

    adjacency = _sppm_non_rework_adjacency(node_ids=node_ids, edges=edges)
    terminal_ids = {
        node_id
        for node in nodes
        if (node_id := str(node.get("id") or ""))
        and str(node.get("kind") or node.get("type") or "").lower() == "end"
    }
    rework_node_ids = _sppm_rework_reachable_nodes(
        node_ids=node_ids,
        branch_targets=branch_targets,
        return_sources=return_sources,
        adjacency=adjacency,
        terminal_ids=terminal_ids,
    )

    if not rework_node_ids:
        return ()

    mainline_ids = tuple(
        node_id for node_id in node_ids if node_id not in rework_node_ids
    )
    rework_ids = _ordered_rework_row_node_ids(
        node_ids=node_ids,
        rework_node_ids=rework_node_ids,
        edges=edges,
    )
    if not mainline_ids or not rework_ids:
        return ()

    return _sppm_synthetic_lane_pair(mainline_ids=mainline_ids, rework_ids=rework_ids)


def _sppm_rework_endpoints(
    *, edges: tuple[ElkLayoutEdge, ...]
) -> tuple[set[str], set[str]]:
    branch_targets = {
        edge.target_id for edge in edges if edge.rework_variant == "branch"
    }
    return_sources = {
        edge.source_id for edge in edges if edge.rework_variant == "return"
    }
    return branch_targets, return_sources


def _sppm_non_rework_adjacency(
    *,
    node_ids: list[str],
    edges: tuple[ElkLayoutEdge, ...],
) -> dict[str, list[str]]:
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for edge in edges:
        if edge.is_rework or edge.source_id not in adjacency:
            continue
        adjacency[edge.source_id].append(edge.target_id)
    return adjacency


def _sppm_rework_reachable_nodes(
    *,
    node_ids: list[str],
    branch_targets: set[str],
    return_sources: set[str],
    adjacency: dict[str, list[str]],
    terminal_ids: set[str],
) -> set[str]:
    rework_node_ids: set[str] = set()
    frontier = [target_id for target_id in node_ids if target_id in branch_targets]
    while frontier:
        current = frontier.pop()
        if current in rework_node_ids:
            continue
        if current in terminal_ids and current not in branch_targets:
            continue
        rework_node_ids.add(current)
        if current in return_sources:
            continue
        for next_id in adjacency.get(current, []):
            if next_id not in rework_node_ids:
                frontier.append(next_id)
    return rework_node_ids


def _sppm_synthetic_lane_pair(
    *,
    mainline_ids: tuple[str, ...],
    rework_ids: tuple[str, ...],
) -> tuple[ElkLayoutLane, ...]:
    return (
        ElkLayoutLane(
            id="__sppm_row_mainline",
            label="Mainline",
            node_ids=mainline_ids,
        ),
        ElkLayoutLane(
            id="__sppm_row_rework",
            label="Rework",
            node_ids=rework_ids,
        ),
    )


def _ordered_rework_row_node_ids(
    *,
    node_ids: list[str],
    rework_node_ids: set[str],
    edges: tuple[ElkLayoutEdge, ...],
) -> tuple[str, ...]:
    chains_by_branch = _rework_chains_by_branch(
        node_ids=node_ids,
        rework_node_ids=rework_node_ids,
        edges=edges,
    )
    if not chains_by_branch:
        return tuple(node_id for node_id in node_ids if node_id in rework_node_ids)

    ordered: list[str] = []
    claimed: set[str] = set()
    for _branch_source_id, chain in chains_by_branch:
        for member in chain:
            if member in claimed:
                continue
            claimed.add(member)
            ordered.append(member)

    for node_id in node_ids:
        if node_id in rework_node_ids and node_id not in claimed:
            ordered.append(node_id)

    return tuple(ordered)


def _rework_chains_by_branch(
    *,
    node_ids: list[str],
    rework_node_ids: set[str],
    edges: tuple[ElkLayoutEdge, ...],
) -> list[tuple[str, tuple[str, ...]]]:
    branch_target_to_source = {
        edge.target_id: edge.source_id
        for edge in edges
        if edge.rework_variant == "branch"
    }
    if not branch_target_to_source:
        return []

    node_index = {node_id: idx for idx, node_id in enumerate(node_ids)}
    non_rework_adjacency = _sppm_non_rework_adjacency(node_ids=node_ids, edges=edges)
    return_sources = {
        edge.source_id for edge in edges if edge.rework_variant == "return"
    }

    chains: list[tuple[str, tuple[str, ...]]] = []
    branch_targets = sorted(
        (target for target in branch_target_to_source if target in rework_node_ids),
        key=lambda target: node_index.get(branch_target_to_source[target], -1),
        reverse=True,
    )
    for target_id in branch_targets:
        source_id = branch_target_to_source[target_id]
        chain = _walk_rework_chain(
            start_id=target_id,
            rework_node_ids=rework_node_ids,
            adjacency=non_rework_adjacency,
            return_sources=return_sources,
        )
        if chain:
            chains.append((source_id, chain))

    return chains


def _sppm_partition_indexes_for_synthetic_rows(
    *,
    node_ids: list[str],
    lanes: tuple[ElkLayoutLane, ...],
    edges: tuple[ElkLayoutEdge, ...],
) -> dict[str, int]:
    if len(lanes) < 2:
        return {}

    mainline_lane = next(
        (lane for lane in lanes if lane.id == "__sppm_row_mainline"),
        None,
    )
    rework_lane = next(
        (lane for lane in lanes if lane.id == "__sppm_row_rework"),
        None,
    )
    if mainline_lane is None or rework_lane is None:
        return {}

    main_index = {node_id: idx for idx, node_id in enumerate(mainline_lane.node_ids)}
    partition_map = dict(main_index)
    rework_set = set(rework_lane.node_ids)
    return_target_by_source = {
        edge.source_id: edge.target_id
        for edge in edges
        if edge.rework_variant == "return"
    }

    chains_by_branch = _rework_chains_by_branch(
        node_ids=node_ids,
        rework_node_ids=rework_set,
        edges=edges,
    )
    claimed: set[str] = set()
    for source_id, chain in chains_by_branch:
        start = main_index.get(source_id, 0)
        end_node_id = next(
            (
                node_id
                for node_id in reversed(chain)
                if node_id in return_target_by_source
            ),
            None,
        )
        end = (
            main_index.get(return_target_by_source[end_node_id], start)
            if end_node_id is not None
            else None
        )
        strategy = current_sppm_layout_strategy()
        for offset, node_id in enumerate(chain):
            if node_id in claimed:
                continue
            claimed.add(node_id)
            if strategy.partition_mode == "chain_progressive":
                if end is not None and len(chain) > 1:
                    ratio = offset / float(len(chain) - 1)
                    partition_map[node_id] = max(
                        0,
                        int(round((start * (1.0 - ratio)) + (end * ratio))),
                    )
                else:
                    partition_map[node_id] = max(0, start - offset)
                continue

            # branch_aligned keeps branch targets anchored under the branch source,
            # but still anchors the return source at its reintegration target.
            if end is not None and node_id == end_node_id:
                partition_map[node_id] = max(0, end)
            else:
                partition_map[node_id] = start

    for node_id in rework_lane.node_ids:
        if node_id not in partition_map:
            partition_map[node_id] = 0

    return partition_map


def _walk_rework_chain(
    *,
    start_id: str,
    rework_node_ids: set[str],
    adjacency: dict[str, list[str]],
    return_sources: set[str],
) -> tuple[str, ...]:
    chain: list[str] = []
    current = start_id
    visited: set[str] = set()

    while current in rework_node_ids and current not in visited:
        visited.add(current)
        chain.append(current)
        if current in return_sources:
            break
        next_candidates = [
            candidate
            for candidate in adjacency.get(current, [])
            if candidate in rework_node_ids and candidate not in visited
        ]
        if not next_candidates:
            break
        current = next_candidates[0]

    return tuple(chain)


def _sppm_lane_direction(*, lane_id: str, root_direction: str) -> str:
    # Rework rows should flow opposite the mainline to express return-to-previous
    # semantics when synthetic rows are represented as explicit lane containers.
    if lane_id == "__sppm_row_rework" and root_direction == "RIGHT":
        return "LEFT"
    return root_direction


def _sppm_apply_secondary_row_edge_ports(
    *,
    edges: tuple[ElkLayoutEdge, ...],
    synthetic_rows: tuple[ElkLayoutLane, ...],
    root_direction: str,
) -> tuple[ElkLayoutEdge, ...]:
    rework_lane = next(
        (lane for lane in synthetic_rows if lane.id == "__sppm_row_rework"),
        None,
    )
    if rework_lane is None:
        return edges

    rework_ids = set(rework_lane.node_ids)
    adjusted: list[ElkLayoutEdge] = []
    direct_source_port = "NORTH" if root_direction == "DOWN" else "WEST"
    direct_target_port = "SOUTH" if root_direction == "DOWN" else "EAST"
    for edge in edges:
        if (
            edge.source_id in rework_ids
            and edge.target_id in rework_ids
            and not edge.is_rework
        ):
            adjusted.append(
                replace(
                    edge,
                    source_port_side=direct_source_port,
                    target_port_side=direct_target_port,
                )
            )
            continue
        adjusted.append(edge)
    return tuple(adjusted)
