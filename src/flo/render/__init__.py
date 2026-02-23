from __future__ import annotations

from flo.ir import IR


def render_dot(ir: IR) -> str:
    """Return a tiny DOT representation of the IR.

    This is intentionally minimal and only intended to validate wiring.
    """
    # Very small, always-valid DOT for the single-node IR produced by
    # the compiler stub.
    return "digraph G { n1; }"
"""Renderers package: emit presentation artifacts from canonical IR."""
from .graphviz_dot import render_flowchart_dot, render_swimlane_dot

__all__ = ["render_flowchart_dot", "render_swimlane_dot"]
