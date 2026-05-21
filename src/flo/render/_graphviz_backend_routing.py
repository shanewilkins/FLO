"""Backend-oriented aliases for shared Graphviz routing helpers.

This module provides a backend-named import surface for shared Graphviz edge
and routing utilities that are still implemented in the older
``_graphviz_dot_edge_routing`` module.
"""

from __future__ import annotations

from . import _graphviz_dot_edge_routing as _legacy

_append_edges = _legacy._append_edges
_escape = _legacy._escape
_is_cross_lane_edge = _legacy._is_cross_lane_edge

__all__ = ["_append_edges", "_escape", "_is_cross_lane_edge"]
