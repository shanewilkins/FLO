"""Renderers package: emit presentation artifacts from canonical IR."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .graphviz_dot import render_flowchart_dot, render_swimlane_dot, render_spaghetti_dot, render_sppm_dot
from .options import RenderOptions

if TYPE_CHECKING:
    from ._sppm_postprocess_contract import SppmSvgPostprocessContract

_DOT_RENDERERS = {
	"flowchart": render_flowchart_dot,
	"swimlane": render_swimlane_dot,
	"spaghetti": render_spaghetti_dot,
	"sppm": render_sppm_dot,
}

# Cache for routing contract from most recent SPPM render
_LAST_SPPM_CONTRACT: SppmSvgPostprocessContract | None = None


def render_dot(ir: Any, options: dict | None = None) -> str:
	"""Render DOT from canonical IR using pluggable diagram strategies."""
	render_options = RenderOptions.from_mapping(options)
	renderer = _DOT_RENDERERS.get(render_options.diagram, render_flowchart_dot)
	return renderer(ir, options=render_options)


def get_last_sppm_contract() -> SppmSvgPostprocessContract | None:
	"""Return the routing contract from the most recent SPPM render."""
	return _LAST_SPPM_CONTRACT


def set_last_sppm_contract(contract: SppmSvgPostprocessContract | None) -> None:
	"""Store the routing contract from an SPPM render."""
	global _LAST_SPPM_CONTRACT
	_LAST_SPPM_CONTRACT = contract


__all__ = ["render_flowchart_dot", "render_swimlane_dot", "render_spaghetti_dot", "render_sppm_dot", "render_dot", "RenderOptions", "get_last_sppm_contract", "set_last_sppm_contract"]
