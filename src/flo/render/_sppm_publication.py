"""SPPM-first publication plan builder backed by the shared publication model."""

from __future__ import annotations

from typing import Any

from flo.compiler.ir.subprocess_refs import resolve_subprocess_detail_map_reference

from ._process_header import build_process_header_rows, extract_process_header_context
from ._publication import (
    PublicationArtifactSlot,
    PublicationBandContent,
    PublicationBounds,
    PublicationMargins,
    PublicationPage,
    PublicationPlan,
    PublicationSeries,
    build_publication_canvas,
)
from ._sppm_text import normalize_space
from .options import RenderOptions

_DEFAULT_SPPM_PUBLICATION_WIDTH_PX = 1200
_DEFAULT_SPPM_PUBLICATION_MARGINS = PublicationMargins(top_px=48, right_px=48, bottom_px=48, left_px=48)
_SPPM_HEADER_BAND_HEIGHT_PX = 96


def build_sppm_publication_plan(
    *,
    process: Any,
    options: RenderOptions,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> PublicationPlan:
    """Build a renderer-independent single-page publication plan for SPPM output."""
    context = extract_process_header_context(process)
    title = normalize_space(context.title)
    header_rows = _build_sppm_header_rows(context=context, options=options, nodes=nodes, edges=edges)
    canvas = build_publication_canvas(
        bounds=PublicationBounds(width_px=options.layout_max_width_px or _DEFAULT_SPPM_PUBLICATION_WIDTH_PX),
        margins=_DEFAULT_SPPM_PUBLICATION_MARGINS,
        header_height_px=_SPPM_HEADER_BAND_HEIGHT_PX if title else 0,
        footer_height_px=0,
    )
    page = PublicationPage(
        page_id="main-p1",
        page_number=1,
        series_id="main",
        canvas=canvas,
        header_content=PublicationBandContent(title=title, rows=tuple(header_rows)) if title else None,
        metadata={
            "diagram": "sppm",
            "projection_mode": options.subprocess_view,
        },
    )
    series = PublicationSeries(
        series_id="main",
        title=title or "SPPM Publication",
        kind="map",
        pages=(page,),
        metadata={
            "diagram": "sppm",
            "projection_mode": options.subprocess_view,
            "page_count": 1,
        },
    )
    return PublicationPlan(
        title=title,
        primary_series_id=series.series_id,
        series=(series,),
        artifact_slots=tuple(_build_sppm_child_slots(nodes=nodes, parent_series_id=series.series_id)),
        metadata={
            "diagram": "sppm",
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
    )


def _build_sppm_header_rows(
    *,
    context: Any,
    options: RenderOptions,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    extra_rows: list[tuple[str, str]] = []
    if options.sppm_output_profile != "default":
        extra_rows.append(("Profile", options.sppm_output_profile))
    if options.subprocess_view != "expanded":
        extra_rows.append(("Subprocess View", options.subprocess_view.replace("_", "-")))
    extra_rows.append(("Nodes", str(len(nodes))))
    extra_rows.append(("Edges", str(len(edges))))
    return build_process_header_rows(context=context, extra_rows=extra_rows)


def _build_sppm_child_slots(*, nodes: list[dict[str, Any]], parent_series_id: str) -> list[PublicationArtifactSlot]:
    slots: list[PublicationArtifactSlot] = []
    for node in nodes:
        node_id = str(node.get("id") or "").strip()
        if not node_id:
            continue
        kind = str(node.get("kind") or node.get("type") or "").strip().lower()
        if kind != "subprocess":
            continue
        metadata = node.get("metadata")
        metadata_dict = metadata if isinstance(metadata, dict) else {}
        detail_map_ref = resolve_subprocess_detail_map_reference(node_id=node_id, metadata=metadata_dict)
        slots.append(
            PublicationArtifactSlot(
                slot_id=f"child:{node_id}",
                title=normalize_space(str(node.get("name") or node_id)),
                kind="child_map",
                parent_series_id=parent_series_id,
                source_node_id=node_id,
                metadata={"detail_map_ref": detail_map_ref},
            )
        )
    return slots