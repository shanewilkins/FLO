"""Renderer-neutral geometry resolution for direct SVG artifacts."""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Any

from flo.errors import RenderError

from ._artifact import RenderArtifact
from .options import RenderOptions

_SVG_DIMENSION_RE = re.compile(r'\b{attribute}="(?P<value>\d+(?:\.\d+)?)"')


def resolve_svg_geometry(
    artifact: RenderArtifact, options: RenderOptions
) -> RenderArtifact:
    """Validate a requested SVG canvas against natural artifact geometry."""
    if artifact.kind != "svg" or (
        options.layout_width_px is None and options.layout_height_px is None
    ):
        return artifact

    natural_width, natural_height = _natural_svg_dimensions(artifact.content)
    requested_width = options.layout_width_px
    requested_height = options.layout_height_px
    overflows = (requested_width is not None and natural_width > requested_width) or (
        requested_height is not None and natural_height > requested_height
    )
    geometry: dict[str, Any] = {
        "natural_width_px": natural_width,
        "natural_height_px": natural_height,
        "requested_width_px": requested_width,
        "requested_height_px": requested_height,
        "overflow_policy": options.layout_overflow,
        "overflows_requested_bounds": overflows,
    }
    if overflows:
        if options.layout_overflow == "expand":
            return _expand_svg_canvas(
                artifact=artifact,
                geometry=geometry,
                requested_width=requested_width,
                requested_height=requested_height,
            )
        if options.layout_overflow == "scale":
            return _scale_svg_to_fit(
                artifact=artifact,
                geometry=geometry,
                requested_width=requested_width,
                requested_height=requested_height,
            )
        _raise_for_overflow(geometry=geometry, policy=options.layout_overflow)
    geometry["final_width_px"] = requested_width or natural_width
    geometry["final_height_px"] = requested_height or natural_height
    geometry["expanded"] = False
    geometry["scale"] = 1.0
    return replace(artifact, metadata={**artifact.metadata, "geometry": geometry})


def _natural_svg_dimensions(content: str) -> tuple[int, int]:
    root = content.split(">", maxsplit=1)[0]
    width_match = re.search(_SVG_DIMENSION_RE.pattern.format(attribute="width"), root)
    height_match = re.search(_SVG_DIMENSION_RE.pattern.format(attribute="height"), root)
    if width_match is None or height_match is None:
        raise RenderError("SVG artifact is missing numeric root width or height.")
    return (
        round(float(width_match.group("value"))),
        round(float(height_match.group("value"))),
    )


def _raise_for_overflow(*, geometry: dict[str, Any], policy: str) -> None:
    requested = (
        f"{geometry['requested_width_px'] or 'natural'}x"
        f"{geometry['requested_height_px'] or 'natural'}px"
    )
    natural = f"{geometry['natural_width_px']}x{geometry['natural_height_px']}px"
    if policy == "error":
        raise RenderError(
            f"Natural SVG geometry {natural} exceeds requested bounds {requested}; "
            "select --layout-overflow expand, scale, or paginate explicitly."
        )
    raise RenderError(
        f"Requested --layout-overflow {policy} for natural SVG geometry {natural} "
        f"and bounds {requested}, but that policy is not implemented yet."
    )


def _expand_svg_canvas(
    *,
    artifact: RenderArtifact,
    geometry: dict[str, Any],
    requested_width: int | None,
    requested_height: int | None,
) -> RenderArtifact:
    natural_width = geometry["natural_width_px"]
    natural_height = geometry["natural_height_px"]
    final_width = max(natural_width, requested_width or natural_width)
    final_height = max(natural_height, requested_height or natural_height)
    geometry["final_width_px"] = final_width
    geometry["final_height_px"] = final_height
    geometry["expanded"] = (
        final_width != natural_width or final_height != natural_height
    )
    geometry["scale"] = 1.0
    return replace(
        artifact,
        content=_replace_svg_root_geometry(
            artifact.content, width=final_width, height=final_height
        ),
        metadata={**artifact.metadata, "geometry": geometry},
    )


def _scale_svg_to_fit(
    *,
    artifact: RenderArtifact,
    geometry: dict[str, Any],
    requested_width: int | None,
    requested_height: int | None,
) -> RenderArtifact:
    natural_width = geometry["natural_width_px"]
    natural_height = geometry["natural_height_px"]
    final_width, final_height = _requested_canvas_bounds(
        natural_width=natural_width,
        natural_height=natural_height,
        requested_width=requested_width,
        requested_height=requested_height,
    )
    scale = min(1.0, final_width / natural_width, final_height / natural_height)
    geometry["final_width_px"] = final_width
    geometry["final_height_px"] = final_height
    geometry["expanded"] = False
    geometry["scale"] = scale
    return replace(
        artifact,
        content=_replace_svg_root_geometry(
            artifact.content,
            width=final_width,
            height=final_height,
            view_box_width=natural_width,
            view_box_height=natural_height,
            preserve_aspect_ratio="xMidYMid meet",
        ),
        metadata={**artifact.metadata, "geometry": geometry},
    )


def _requested_canvas_bounds(
    *,
    natural_width: int,
    natural_height: int,
    requested_width: int | None,
    requested_height: int | None,
) -> tuple[int, int]:
    if requested_width is None:
        assert requested_height is not None
        return round(
            requested_height * natural_width / natural_height
        ), requested_height
    if requested_height is None:
        return requested_width, round(requested_width * natural_height / natural_width)
    return requested_width, requested_height


def _replace_svg_root_geometry(
    content: str,
    *,
    width: int,
    height: int,
    view_box_width: int | None = None,
    view_box_height: int | None = None,
    preserve_aspect_ratio: str | None = None,
) -> str:
    root, separator, remainder = content.partition(">")
    if not separator:
        raise RenderError("SVG artifact is missing a root element.")
    root = re.sub(
        _SVG_DIMENSION_RE.pattern.format(attribute="width"),
        f'width="{width}"',
        root,
        count=1,
    )
    root = re.sub(
        _SVG_DIMENSION_RE.pattern.format(attribute="height"),
        f'height="{height}"',
        root,
        count=1,
    )
    root = re.sub(
        r'\bviewBox="[^"]*"',
        f'viewBox="0 0 {view_box_width or width} {view_box_height or height}"',
        root,
        count=1,
    )
    if preserve_aspect_ratio is not None:
        root = re.sub(
            r'\bpreserveAspectRatio="[^"]*"',
            f'preserveAspectRatio="{preserve_aspect_ratio}"',
            root,
            count=1,
        )
        if "preserveAspectRatio=" not in root:
            root = root.replace(
                "<svg", f'<svg preserveAspectRatio="{preserve_aspect_ratio}"', 1
            )
    return f"{root}{separator}{remainder}"
