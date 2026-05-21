"""Graphviz backend entrypoint for FLO renderers.

This module is the backend-oriented aggregation point for Graphviz-backed
diagram rendering. It supersedes the older ``graphviz_dot`` compatibility
facade, which remains available for legacy imports.
"""

from __future__ import annotations

from ._graphviz_dot_flow import render_flowchart_dot, render_swimlane_dot
from ._graphviz_dot_spaghetti import render_spaghetti_dot
from ._graphviz_dot_sppm import render_sppm_dot

__all__ = [
    "render_flowchart_dot",
    "render_swimlane_dot",
    "render_spaghetti_dot",
    "render_sppm_dot",
]
