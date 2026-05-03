"""Renderers package: emit presentation artifacts from canonical IR."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .graphviz_dot import render_flowchart_dot, render_swimlane_dot, render_spaghetti_dot, render_sppm_dot
from ._graphviz_dot_sppm import _render_sppm_graph
from .options import RenderOptions

if TYPE_CHECKING:
    from ._sppm_postprocess_contract import SppmSvgPostprocessContract

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


def render_dot_and_contract(ir: Any, options: dict | None = None) -> tuple[str, SppmSvgPostprocessContract | None]:
	"""Render DOT and return the SPPM postprocess contract alongside it.

	For non-SPPM diagrams the contract is ``None``.  Use this instead of
	``render_dot`` when the caller needs to pass the contract to the SVG
	postprocessor (e.g. ``render_dot_to_file``).
	"""
	render_options = RenderOptions.from_mapping(options)
	if render_options.diagram == "sppm":
		dot, contract = _render_sppm_graph(ir, render_options)
		return dot, contract
	renderer = _DOT_RENDERERS.get(render_options.diagram, render_flowchart_dot)
	return renderer(ir, options=render_options), None


__all__ = ["render_flowchart_dot", "render_swimlane_dot", "render_spaghetti_dot", "render_sppm_dot", "render_dot", "render_dot_and_contract", "RenderOptions"]
