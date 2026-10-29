"""Graph topology, branching and reachability validation."""

from flo.errors import ValidationError

from ._boundary_validation import validate_branch_config
from ._graph_utils import build_adjacency_maps, traverse
from .models import IR


def _validate_start_nodes(obj: IR) -> None:
    start_nodes = [n for n in obj.nodes if (n.type or "").lower() == "start"]
    if len(start_nodes) != 1:
        raise ValidationError("E1003: IR must contain exactly one start node")


def _validate_edge_resolution(obj: IR, ids: list[str]) -> None:
    known_ids = set(ids)
    for edge in obj.edges:
        if edge.source not in known_ids or edge.target not in known_ids:
            raise ValidationError(
                f"E1004: edge endpoint unresolved: {edge.source} -> {edge.target}"
            )


def _build_edge_degree_maps(
    obj: IR, ids: list[str]
) -> tuple[dict[str, int], dict[str, int]]:
    known_ids = set(ids)
    incoming_counts: dict[str, int] = dict.fromkeys(known_ids, 0)
    outgoing_counts: dict[str, int] = dict.fromkeys(known_ids, 0)
    for edge in obj.edges:
        if edge.target in incoming_counts:
            incoming_counts[edge.target] += 1
        if edge.source in outgoing_counts:
            outgoing_counts[edge.source] += 1
    return incoming_counts, outgoing_counts


def _validate_branch_points(obj: IR, outgoing_counts: dict[str, int]) -> None:
    node_types = {node.id: (node.type or "").lower() for node in obj.nodes}
    for node in obj.nodes:
        node_type = node_types[node.id]
        outgoing_count = outgoing_counts.get(node.id, 0)
        if node_type == "decision" and outgoing_count < 2:
            raise ValidationError(
                f"E1005: decision node '{node.id}' must have at least two outgoing edges"
            )
        if node_type == "decision":
            _validate_decision_edges(obj=obj, node_id=node.id)

        if node_type == "branch":
            if outgoing_count < 2:
                raise ValidationError(
                    f"E1026: branch node '{node.id}' must have at least two outgoing edges"
                )
            validate_branch_config(node.id, node.branch)
            _validate_branch_edges(obj=obj, node_id=node.id)

    for edge in obj.edges:
        outcome = (edge.outcome or "").strip()
        if outcome and node_types.get(edge.source) != "decision":
            raise ValidationError(
                f"E1022: edge '{edge.source}' -> '{edge.target}' declares outcome "
                f"'{outcome}', but source '{edge.source}' is not a decision. "
                "Remove the outcome or change the source to a decision."
            )
        route = (edge.route or "").strip()
        if route and node_types.get(edge.source) != "branch":
            raise ValidationError(
                f"E1027: edge '{edge.source}' -> '{edge.target}' declares route "
                f"'{route}', but source '{edge.source}' is not a branch. "
                "Remove the route or change the source to a branch."
            )


def _validate_decision_edges(*, obj: IR, node_id: str) -> None:
    seen_outcomes: set[str] = set()
    for edge in (edge for edge in obj.edges if edge.source == node_id):
        outcome = (edge.outcome or "").strip()
        if not outcome:
            raise ValidationError(
                f"E1020: decision '{node_id}' has outgoing edge "
                f"'{edge.source}' -> '{edge.target}' without an outcome. "
                "Add a non-empty outcome to that transition or declare it "
                "in the decision's outcomes."
            )
        normalized_outcome = outcome.casefold()
        if normalized_outcome in seen_outcomes:
            raise ValidationError(
                f"E1021: decision '{node_id}' uses outcome '{outcome}' more than "
                "once. Give each outgoing branch a unique outcome."
            )
        seen_outcomes.add(normalized_outcome)
        if edge.route:
            raise ValidationError(
                f"E1028: decision edge '{edge.source}' -> '{edge.target}' declares "
                "a route. Decision edges use outcome, not route."
            )


def _validate_branch_edges(*, obj: IR, node_id: str) -> None:
    seen_routes: set[str] = set()
    for edge in (edge for edge in obj.edges if edge.source == node_id):
        if edge.outcome:
            raise ValidationError(
                f"E1031: branch edge '{edge.source}' -> '{edge.target}' declares "
                "an outcome. Generic branch edges use route, not outcome."
            )
        route = (edge.route or "").strip()
        if not route:
            continue
        normalized_route = route.casefold()
        if normalized_route in seen_routes:
            raise ValidationError(
                f"E1032: branch '{node_id}' uses route '{route}' more than once. "
                "Give each named route a unique name."
            )
        seen_routes.add(normalized_route)


def _validate_ambiguous_fan_out(obj: IR, outgoing_counts: dict[str, int]) -> None:
    branch_point_types = {"decision", "branch", "parallel_split"}
    for node in obj.nodes:
        node_type = (node.type or "").lower()
        outgoing_count = outgoing_counts.get(node.id, 0)
        if outgoing_count > 1 and node_type not in branch_point_types:
            raise ValidationError(
                f"E1025: node '{node.id}' has {outgoing_count} outgoing edges but "
                f"kind '{node_type}' is not a branch point. Change it to decision, "
                "branch, or parallel_split to declare how paths are selected."
            )


def _validate_queue_nodes(
    obj: IR, incoming_counts: dict[str, int], outgoing_counts: dict[str, int]
) -> None:
    for node in obj.nodes:
        if (node.type or "").lower() != "queue":
            continue

        if incoming_counts.get(node.id, 0) < 1:
            raise ValidationError(
                f"E1103: queue node '{node.id}' must have at least one incoming edge"
            )
        if outgoing_counts.get(node.id, 0) < 1:
            raise ValidationError(
                f"E1104: queue node '{node.id}' must have at least one outgoing edge"
            )


def _validate_node_connectivity(
    obj: IR,
    incoming_counts: dict[str, int],
    outgoing_counts: dict[str, int],
) -> None:
    for node in obj.nodes:
        node_type = (node.type or "").lower()

        if node_type != "start" and incoming_counts.get(node.id, 0) < 1:
            raise ValidationError(
                f"E1006: node '{node.id}' must have at least one predecessor"
            )

        if node_type != "end" and outgoing_counts.get(node.id, 0) < 1:
            raise ValidationError(
                f"E1007: node '{node.id}' must have at least one successor"
            )


def _validate_global_reachability(obj: IR) -> None:
    node_ids = [node.id for node in obj.nodes]
    adjacency, reverse_adjacency = build_adjacency_maps(
        node_ids=node_ids, edges=obj.edges
    )
    start_nodes = _collect_node_ids_by_type(obj=obj, node_type="start")
    end_nodes = _collect_node_ids_by_type(obj=obj, node_type="end")

    _ensure_end_nodes_present(end_nodes=end_nodes)
    _ensure_all_nodes_reachable_from_start(
        obj=obj, start_nodes=start_nodes, adjacency=adjacency
    )
    _ensure_all_nodes_can_reach_end(
        obj=obj, end_nodes=end_nodes, reverse_adjacency=reverse_adjacency
    )


def _validate_boundary_edges(obj: IR) -> None:
    node_types = {node.id: (node.type or "").lower() for node in obj.nodes}
    for edge in obj.edges:
        if node_types.get(edge.target) == "start":
            raise ValidationError(
                f"E1023: edge '{edge.source}' -> '{edge.target}' enters start node "
                f"'{edge.target}'. Start is the process entry boundary; target a "
                "process step instead."
            )
        if node_types.get(edge.source) == "end":
            raise ValidationError(
                f"E1024: edge '{edge.source}' -> '{edge.target}' leaves end node "
                f"'{edge.source}'. End is a process termination boundary; remove "
                "the transition or change its source."
            )


def _collect_node_ids_by_type(obj: IR, node_type: str) -> list[str]:
    return [node.id for node in obj.nodes if (node.type or "").lower() == node_type]


def _ensure_end_nodes_present(end_nodes: list[str]) -> None:
    if not end_nodes:
        raise ValidationError("E1010: IR must contain at least one end node")


def _ensure_all_nodes_reachable_from_start(
    obj: IR,
    start_nodes: list[str],
    adjacency: dict[str, set[str]],
) -> None:
    reachable_from_start = traverse(start_nodes, adjacency)
    for node in obj.nodes:
        if node.id not in reachable_from_start:
            raise ValidationError(f"E1008: node '{node.id}' is unreachable from start")


def _ensure_all_nodes_can_reach_end(
    obj: IR,
    end_nodes: list[str],
    reverse_adjacency: dict[str, set[str]],
) -> None:
    can_reach_end = traverse(end_nodes, reverse_adjacency)
    for node in obj.nodes:
        if node.id not in can_reach_end:
            raise ValidationError(f"E1009: node '{node.id}' cannot reach any end node")
