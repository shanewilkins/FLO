"""Flow and swimlane renderer compatibility facade.

Use dedicated modules for implementation details.
"""

from __future__ import annotations

from ._graphviz_dot_flowchart import render_flowchart_dot
from ._graphviz_dot_swimlane import render_swimlane_dot

__all__ = ["render_flowchart_dot", "render_swimlane_dot"]
