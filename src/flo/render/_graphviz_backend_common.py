"""Backend-oriented aliases for shared Graphviz renderer helpers.

This module provides the backend-named import surface for shared helper
functions implemented in ``_graphviz_backend_common_impl``.
"""

from __future__ import annotations

from . import _graphviz_backend_common_impl as _impl

_add_collapsed_edge = _impl._add_collapsed_edge
_append_clustered_node_pass = _impl._append_clustered_node_pass
_append_clustered_node_passes = _impl._append_clustered_node_passes
_append_node_or_subprocess_cluster = _impl._append_node_or_subprocess_cluster
_build_nodes_by_id = _impl._build_nodes_by_id
_edge_branch_label = _impl._edge_branch_label
_escape = _impl._escape
_extract_from_dict = _impl._extract_from_dict
_extract_nodes_and_edges = _impl._extract_nodes_and_edges
_is_cross_lane_edge = _impl._is_cross_lane_edge
_node_label = _impl._node_label
_node_lane_map = _impl._node_lane_map
_project_parent_only_subprocess_view = _impl._project_parent_only_subprocess_view
_project_subprocess_visible_ids = _impl._project_subprocess_visible_ids
_render_node_line = _impl._render_node_line
_safe_cluster_id = _impl._safe_cluster_id
_shape_for_kind = _impl._shape_for_kind
_subprocess_children_map = _impl._subprocess_children_map
_visible_targets_through_hidden = _impl._visible_targets_through_hidden

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
