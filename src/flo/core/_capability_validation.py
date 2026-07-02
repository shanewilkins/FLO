"""Projection capability validation.

Ensures requested diagram/backend combinations are supported before render.
"""

from __future__ import annotations

from flo.render.capability_matrix import (
    RENDER_CAPABILITY_MATRIX,
    supported_backends_for_diagram,
)
from flo.render.options import RenderOptions
from flo.services.errors import CLIError, EXIT_USAGE


def ensure_render_projection_supported(render_options: RenderOptions) -> None:
    """Raise CLIError when requested diagram/backend projection is unsupported."""
    diagram = str(render_options.diagram or "flowchart").strip().lower()
    backend = str(render_options.backend or "svg").strip().lower()

    diagram_capabilities = RENDER_CAPABILITY_MATRIX.get(diagram)
    if diagram_capabilities is None:
        raise CLIError(
            f"Unsupported diagram '{diagram}'.",
            code=EXIT_USAGE,
        )

    backend_capability = diagram_capabilities.get(backend)
    if backend_capability is None:
        supported = supported_backends_for_diagram(diagram)
        supported_text = ", ".join(supported) if supported else "none"
        raise CLIError(
            f"Unsupported render backend '{backend}' for diagram '{diagram}'. Supported backends: {supported_text}.",
            code=EXIT_USAGE,
        )

    if bool(backend_capability.get("supported")):
        return

    supported = supported_backends_for_diagram(diagram)
    supported_text = ", ".join(supported) if supported else "none"
    note = str(backend_capability.get("note") or "").strip()
    guidance = f" Unsupported projection: diagram '{diagram}' is not available on backend '{backend}'. Supported backends: {supported_text}."
    message = note + guidance if note else guidance.strip()
    raise CLIError(message, code=EXIT_USAGE)
