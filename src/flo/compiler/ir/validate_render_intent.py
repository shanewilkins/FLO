"""Validation helpers for render-intent metadata in FLO IR."""
from __future__ import annotations

from typing import Any
from flo.services.errors import ValidationError
from .models import IR


def validate_render_intent(ir: IR) -> None:
    """Validate render-intent structure in process metadata.
    
    Enforces:
    - Valid diagram types (sppm, spaghetti, topdown)
    - Valid page formats (letter, a4, legal, tabloid)
    - Valid diagram-specific configs (sppm, spaghetti)
    - View names are identifiers
    """
    if not ir.process_metadata:
        return
    
    render = ir.process_metadata.get("render")
    if not render:
        return
    
    if not isinstance(render, dict):
        raise ValidationError("process.metadata.render must be an object")
    
    # Validate defaults if present
    defaults = render.get("defaults")
    if defaults:
        _validate_render_view(defaults, "render.defaults")
    
    # Validate views if present
    views = render.get("views")
    if views:
        if not isinstance(views, dict):
            raise ValidationError("process.metadata.render.views must be an object")
        
        for view_id, view_config in views.items():
            if not isinstance(view_id, str) or not view_id:
                raise ValidationError(f"view id must be non-empty string, got: {view_id}")
            if not isinstance(view_config, dict):
                raise ValidationError(f"render.views.{view_id} must be an object")
            _validate_render_view(view_config, f"render.views.{view_id}")


def _validate_render_view(view: dict[str, Any], path: str) -> None:
    """Validate a single render view configuration.
    
    Args:
        view: render view dictionary
        path: JSONPath for error messages (e.g. "render.defaults" or "render.views.sppm_main")
    """
    _validate_render_diagram(view, path)
    _validate_render_publication(view, path)
    _validate_render_layout(view, path)
    _validate_render_sppm_config(view, path)
    _validate_render_spaghetti_config(view, path)


def _validate_render_diagram(view: dict[str, Any], path: str) -> None:
    """Validate diagram type in render view."""
    _VALID_DIAGRAMS = {"sppm", "spaghetti", "topdown"}
    diagram = view.get("diagram")
    if diagram is not None:
        if not isinstance(diagram, str):
            raise ValidationError(f"{path}.diagram must be string, got {type(diagram).__name__}")
        if diagram not in _VALID_DIAGRAMS:
            raise ValidationError(
                f"{path}.diagram='{diagram}' not supported; must be one of {sorted(_VALID_DIAGRAMS)}"
            )


def _validate_render_publication(view: dict[str, Any], path: str) -> None:
    """Validate publication config in render view."""
    _VALID_PAGE_FORMATS = {"letter", "a4", "legal", "tabloid"}
    pub = view.get("publication")
    if pub is None:
        return
    
    if not isinstance(pub, dict):
        raise ValidationError(f"{path}.publication must be object")
    
    # Validate page_format
    page_format = pub.get("page_format")
    if page_format is not None:
        if not isinstance(page_format, str):
            raise ValidationError(f"{path}.publication.page_format must be string")
        if page_format not in _VALID_PAGE_FORMATS:
            raise ValidationError(
                f"{path}.publication.page_format='{page_format}' not supported; must be one of {sorted(_VALID_PAGE_FORMATS)}"
            )
    
    # Validate margins
    margins = pub.get("margins")
    if margins is not None:
        if not isinstance(margins, dict):
            raise ValidationError(f"{path}.publication.margins must be object")
        for key in margins:
            if key not in {"top", "right", "bottom", "left"}:
                raise ValidationError(f"{path}.publication.margins: unknown key '{key}'")
            val = margins[key]
            if not isinstance(val, int) or val < 0:
                raise ValidationError(f"{path}.publication.margins.{key} must be non-negative integer")


def _validate_render_layout(view: dict[str, Any], path: str) -> None:
    """Validate layout config in render view."""
    layout = view.get("layout")
    if layout is None:
        return
    
    if not isinstance(layout, dict):
        raise ValidationError(f"{path}.layout must be object")
    
    # Validate wrap
    wrap = layout.get("wrap")
    if wrap is not None:
        _VALID_WRAPS = {"none", "auto", "manual"}
        if wrap not in _VALID_WRAPS:
            raise ValidationError(f"{path}.layout.wrap='{wrap}' not supported; must be one of {sorted(_VALID_WRAPS)}")
    
    # Validate numeric fields
    for key in {"max_width", "target_columns"}:
        val = layout.get(key)
        if val is not None and (not isinstance(val, int) or val < 1):
            raise ValidationError(f"{path}.layout.{key} must be positive integer")


def _validate_render_sppm_config(view: dict[str, Any], path: str) -> None:
    """Validate SPPM-specific config in render view."""
    sppm = view.get("sppm")
    if sppm is None:
        return
    
    if not isinstance(sppm, dict):
        raise ValidationError(f"{path}.sppm must be object")
    
    _VALID_DENSITIES = {"full", "compact", "teaching"}
    _VALID_NUMBERING = {"none", "visible", "hidden"}
    
    density = sppm.get("label_density")
    if density is not None and density not in _VALID_DENSITIES:
        raise ValidationError(f"{path}.sppm.label_density='{density}' not supported")
    
    for key in {"node_numbering", "edge_numbering"}:
        numbering = sppm.get(key)
        if numbering is not None and numbering not in _VALID_NUMBERING:
            raise ValidationError(f"{path}.sppm.{key}='{numbering}' not supported")


def _validate_render_spaghetti_config(view: dict[str, Any], path: str) -> None:
    """Validate spaghetti-specific config in render view."""
    spaghetti = view.get("spaghetti")
    if spaghetti is None:
        return
    
    if not isinstance(spaghetti, dict):
        raise ValidationError(f"{path}.spaghetti must be object")
    
    channel = spaghetti.get("channel")
    if channel is not None:
        _VALID_CHANNELS = {"material", "people", "equipment"}
        if channel not in _VALID_CHANNELS:
            raise ValidationError(f"{path}.spaghetti.channel='{channel}' not supported")
    
    mode = spaghetti.get("people_mode")
    if mode is not None:
        _VALID_MODES = {"aggregate", "individual"}
        if mode not in _VALID_MODES:
            raise ValidationError(f"{path}.spaghetti.people_mode='{mode}' not supported")
