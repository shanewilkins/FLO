"""Legacy compatibility facade for Graphviz DOT renderer imports.

Prefer importing from ``flo.render.graphviz_backend`` for backend-oriented
package structure. This module remains to avoid breaking older callers.
"""

from __future__ import annotations

from .graphviz_backend import (
    render_flowchart_dot,
    render_spaghetti_dot,
    render_sppm_dot,
    render_swimlane_dot,
)

__all__ = [
    "render_flowchart_dot",
    "render_swimlane_dot",
    "render_spaghetti_dot",
    "render_sppm_dot",
]
