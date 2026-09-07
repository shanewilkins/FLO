"""SPPM Typst artifact assembly with page-local direct-SVG figures."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .._artifact import RenderArtifact
from .._publication import PublicationPlan
from ..layout_core.elk_support import extract_nodes_and_edges
from ..options import RenderOptions
from ..typst_publication import emit_typst_publication
from .projection import project_sppm_subprocess_view
from .publication import build_sppm_publication_plan
from .renderer import render_sppm_svg_artifact


def render_sppm_typst_publication_artifact(
    process: dict[str, Any] | Any, options: RenderOptions
) -> RenderArtifact:
    """Render Typst source and page-local SVG assets for an SPPM publication."""
    if options.diagram != "sppm":
        raise ValueError(
            "Typst publication output is currently supported only for SPPM."
        )
    publication_options = options
    if publication_options.publication_page_format is None:
        publication_options = replace(
            publication_options, publication_page_format="letter"
        )
    source_nodes, source_edges = extract_nodes_and_edges(process)
    nodes, edges, projection = project_sppm_subprocess_view(
        source_nodes, source_edges, options=publication_options
    )
    plan = build_sppm_publication_plan(
        process=process,
        options=publication_options,
        nodes=nodes,
        edges=edges,
        projection=projection,
    )
    return RenderArtifact(
        kind="typst",
        content=emit_typst_publication(plan),
        backend="typst",
        metadata={
            "publication": {
                "primary_series_id": plan.primary_series_id,
                "page_count": len(plan.primary_series().pages),
                "page_format": plan.metadata.get("page_format"),
            },
            "artifact_slots": tuple(slot.slot_id for slot in plan.artifact_slots),
            "page_svg_assets": _render_sppm_page_svg_assets(
                process=process,
                options=publication_options,
                plan=plan,
                nodes=nodes,
                edges=edges,
            ),
        },
    )


def _render_sppm_page_svg_assets(
    *,
    process: dict[str, Any] | Any,
    options: RenderOptions,
    plan: PublicationPlan,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> tuple[dict[str, str], ...]:
    nodes_by_id = {str(node.get("id") or ""): node for node in nodes}
    page_options = replace(
        options,
        layout_overflow="error",
        publication_page_format=None,
        sppm_show_header=False,
        sppm_show_footer=False,
    )
    assets: list[dict[str, str]] = []
    for page in plan.primary_series().pages:
        page_node_ids = tuple(page.metadata.get("node_ids", ()))
        visible_node_ids = set(page_node_ids)
        page_nodes = [
            nodes_by_id[node_id] for node_id in page_node_ids if node_id in nodes_by_id
        ]
        page_edges = [
            edge
            for edge in edges
            if str(edge.get("source") or "") in visible_node_ids
            and str(edge.get("target") or "") in visible_node_ids
        ]
        page_process = {
            "nodes": page_nodes,
            "edges": page_edges,
            "lanes": list(getattr(process, "lanes", []) or []),
        }
        artifact, _contract = render_sppm_svg_artifact(page_process, page_options)
        for figure in page.figures:
            assets.append(
                {
                    "asset_path": figure.asset_path,
                    "content": artifact.content,
                    "page_id": page.page_id,
                }
            )
    return tuple(assets)
