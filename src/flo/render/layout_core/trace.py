"""Detached observations of renderer-neutral engine execution."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .elk_contracts import ElkLayoutRequest
from .models import LayoutResult


@dataclass(frozen=True)
class ElkLayoutTrace:
    """Detached snapshots of one successful engine execution, before SVG emission."""

    request: ElkLayoutRequest
    request_payload: dict
    response_payload: dict
    result: LayoutResult


LayoutObserver = Callable[[ElkLayoutTrace], None]
