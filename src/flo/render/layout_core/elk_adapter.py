"""Thin ELK adapter entrypoints for graph-family layout callers."""

from __future__ import annotations

from typing import Any, Callable, Protocol

from .elk import build_swimlane_elk_layout_request, execute_elk_layout
from .elk_runtime import run_elkjs_layout
from .models import LayoutResult
from flo.render.options import RenderOptions


class ElkEngine(Protocol):
    """Minimal engine boundary for ELK layout execution."""

    def __call__(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Run an ELK-shaped payload and return an ELK-shaped response."""
        ...


def layout_swimlane_with_elk(
    process: dict[str, Any] | Any,
    *,
    engine: ElkEngine | Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    options: RenderOptions | None = None,
) -> LayoutResult:
    """Build, execute, and normalize a swimlane ELK layout pass."""
    render_options = options or RenderOptions(diagram="swimlane")
    if render_options.diagram != "swimlane":
        raise ValueError("Swimlane ELK adapter requires diagram='swimlane'.")

    request = build_swimlane_elk_layout_request(process, options=render_options)
    return execute_elk_layout(request, engine=engine or run_elkjs_layout)
