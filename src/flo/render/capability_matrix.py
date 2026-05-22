"""Machine-readable render capability matrix.

Defines which diagram and backend combinations are currently supported.
"""

from __future__ import annotations

from typing import Final, TypedDict


class BackendCapability(TypedDict):
    """Capability metadata for one backend under a diagram entry."""

    supported: bool
    note: str


RenderCapabilityMatrix = dict[str, dict[str, BackendCapability]]


RENDER_CAPABILITY_MATRIX: Final[RenderCapabilityMatrix] = {
    "flowchart": {
        "graphviz": {
            "supported": True,
            "note": "Graphviz DOT renderer is supported.",
        },
        "svg": {
            "supported": True,
            "note": "Direct SVG renderer is supported.",
        },
    },
    "swimlane": {
        "graphviz": {
            "supported": True,
            "note": "Graphviz DOT renderer is supported.",
        },
        "svg": {
            "supported": False,
            "note": "Direct SVG swimlane renderer is not implemented yet.",
        },
    },
    "spaghetti": {
        "graphviz": {
            "supported": True,
            "note": "Graphviz DOT renderer is supported.",
        },
        "svg": {
            "supported": True,
            "note": "Direct SVG renderer is supported.",
        },
    },
    "sppm": {
        "graphviz": {
            "supported": True,
            "note": "Graphviz DOT renderer is supported.",
        },
        "svg": {
            "supported": True,
            "note": "Direct SVG renderer is supported.",
        },
    },
}


def supported_backends_for_diagram(diagram: str) -> tuple[str, ...]:
    """Return supported backends for a diagram from the capability matrix."""
    diagram_key = str(diagram or "").strip().lower()
    backends = RENDER_CAPABILITY_MATRIX.get(diagram_key, {})
    return tuple(
        backend
        for backend, capability in backends.items()
        if bool(capability.get("supported"))
    )
