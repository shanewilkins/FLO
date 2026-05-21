"""Legacy compatibility shim for shared Graphviz common helpers.

Prefer importing from ``flo.render._graphviz_backend_common``. The underlying
implementation now lives in ``_graphviz_backend_common_impl``.
"""

from __future__ import annotations

from ._graphviz_backend_common import (
    _add_collapsed_edge,
    _append_clustered_node_pass,
    _append_clustered_node_passes,
    _append_node_or_subprocess_cluster,
    _build_nodes_by_id,
    _edge_branch_label,
    _escape,
    _extract_from_dict,
    _extract_nodes_and_edges,
    _is_cross_lane_edge,
    _node_label,
    _node_lane_map,
    _project_parent_only_subprocess_view,
    _project_subprocess_visible_ids,
    _render_node_line,
    _safe_cluster_id,
    _shape_for_kind,
    _subprocess_children_map,
    _visible_targets_through_hidden,
)

__all__ = [
    "_add_collapsed_edge",
    "_append_clustered_node_pass",
    "_append_clustered_node_passes",
    "_append_node_or_subprocess_cluster",
    "_build_nodes_by_id",
    "_edge_branch_label",
    "_escape",
    "_extract_from_dict",
    "_extract_nodes_and_edges",
    "_is_cross_lane_edge",
    "_node_label",
    "_node_lane_map",
    "_project_parent_only_subprocess_view",
    "_project_subprocess_visible_ids",
    "_render_node_line",
    "_safe_cluster_id",
    "_shape_for_kind",
    "_subprocess_children_map",
    "_visible_targets_through_hidden",
]
