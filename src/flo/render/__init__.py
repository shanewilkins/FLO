"""Renderers package: emit presentation artifacts from canonical IR."""

from __future__ import annotations

from typing import Any

from .graphviz_dot import render_flowchart_dot, render_swimlane_dot


def render_dot(ir: Any) -> str:
	"""Backward-compatible tiny DOT renderer used in tests.

	Delegates to `render_flowchart_dot` (preserving a simple signature).
	"""
	return render_flowchart_dot(ir)


__all__ = ["render_flowchart_dot", "render_swimlane_dot", "render_dot"]
