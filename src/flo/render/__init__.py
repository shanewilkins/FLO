"""Renderers package: emit presentation artifacts from canonical IR."""

from __future__ import annotations

from typing import Any

from .graphviz_dot import render_flowchart_dot, render_swimlane_dot, render_spaghetti_dot, render_sppm_dot
from .options import RenderOptions

_DOT_RENDERERS = {
	"flowchart": render_flowchart_dot,
	"swimlane": render_swimlane_dot,
	"spaghetti": render_spaghetti_dot,
	"sppm": render_sppm_dot,
}


def render_dot(ir: Any, options: dict | None = None) -> str:
	"""Render DOT from canonical IR using pluggable diagram strategies."""
	render_options = RenderOptions.from_mapping(options)
	renderer = _DOT_RENDERERS.get(render_options.diagram, render_flowchart_dot)
	return renderer(ir, options=render_options)


__all__ = ["render_flowchart_dot", "render_swimlane_dot", "render_spaghetti_dot", "render_sppm_dot", "render_dot", "RenderOptions"]
