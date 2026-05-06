"""Thin public entrypoint for SPPM DOT rendering.

The implementation is intentionally delegated to focused SPPM renderer modules so
graph assembly, node rendering, and publication-band rendering evolve
independently.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ._sppm_graph_builder import build_sppm_graph
from .options import RenderOptions

if TYPE_CHECKING:
    from flo.compiler.ir.models import IR
    from ._sppm_postprocess_contract import SppmSvgPostprocessContract

__all__ = ["render_sppm_dot", "_render_sppm_graph"]


def render_sppm_dot(process: IR | dict[str, Any], options: RenderOptions | None = None) -> str:
    """Render a Standard Process Performance Map (SPPM) as Graphviz DOT."""
    render_options = options or RenderOptions()
    dot, _contract = _render_sppm_graph(process, options=render_options)
    return dot


def _render_sppm_graph(process: IR | dict[str, Any], options: RenderOptions) -> tuple[str, SppmSvgPostprocessContract]:
    """Return SPPM DOT plus the SVG postprocess contract."""
    return build_sppm_graph(process, options=options)
