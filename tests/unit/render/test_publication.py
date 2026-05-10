from typing import Any

from flo.render._publication import (
    PublicationBandContent,
    PublicationBounds,
    build_publication_band_context,
    PublicationDiagnostic,
    PublicationMargins,
    build_publication_canvas_for_format,
    build_publication_bands,
    build_publication_canvas,
    evaluate_publication_fallback,
    materialize_publication_series,
    PublicationPageSpec,
    resolve_publication_page_format,
)
from flo.render._sppm_projection import project_sppm_subprocess_view
from flo.render._sppm_publication import build_sppm_publication_plan
from flo.render.options import RenderOptions
from flo.services.errors import RenderError


def test_build_publication_canvas_keeps_margins_outside_content_regions():
    canvas = build_publication_canvas(
        bounds=PublicationBounds(width_px=1200, height_px=900),
        margins=PublicationMargins(top_px=40, right_px=30, bottom_px=20, left_px=10),
        header_height_px=100,
        footer_height_px=80,
    )

    assert canvas.usable_region.x_px == 10
    assert canvas.usable_region.y_px == 40
    assert canvas.usable_region.width_px == 1160
    assert canvas.usable_region.height_px == 840
    assert canvas.region("header").height_px == 100
    assert canvas.region("body").y_px == 140
    assert canvas.region("body").height_px == 660
    assert canvas.region("footer").y_px == 800


def test_resolve_publication_page_format_supports_named_presets():
    preset = resolve_publication_page_format("a4")

    assert preset.name == "a4"
    assert preset.width_px == 794
    assert preset.height_px == 1123
    assert preset.margins.left_px == 48


def test_build_publication_canvas_for_format_uses_named_preset_geometry():
    canvas = build_publication_canvas_for_format(page_format="letter", header_height_px=96, footer_height_px=72)

    assert canvas.bounds.width_px == 816
    assert canvas.bounds.height_px == 1056
    assert canvas.usable_region.width_px == 720
    assert canvas.region("body").height_px == 792


def test_resolve_publication_page_format_rejects_unknown_names():
    import pytest

    with pytest.raises(ValueError, match="publication_page_format"):
        resolve_publication_page_format("broadsheet")


def test_evaluate_publication_fallback_warns_in_non_strict_mode():
    diagnostics = evaluate_publication_fallback(
        requested_mode="inline",
        effective_mode="child_map",
        fallback_reason="inline-budget-exceeded",
        strict=False,
    )

    assert diagnostics == (
        PublicationDiagnostic(
            code="publication-fallback",
            severity="warning",
            message="Requested publication mode 'inline' fell back to 'child_map' because inline budget exceeded.",
            metadata={
                "requested_mode": "inline",
                "effective_mode": "child_map",
                "fallback_reason": "inline-budget-exceeded",
                "strict": False,
            },
        ),
    )


def test_build_publication_band_context_supports_page_parent_child_and_continuation_refs():
    context_rows = build_publication_band_context(
        {
            "series_id": "child-series",
            "page_number": 2,
            "page_count": 3,
            "parent_series_id": "main",
            "source_node_id": "prep",
            "continuation_from": "main-p1",
            "continuation_to": "child-series-p3",
        }
    )

    assert context_rows == (
        ("Page", "2/3"),
        ("Series", "child-series"),
        ("Parent Map", "main"),
        ("Child Map", "prep"),
        ("Continues From", "main-p1"),
        ("Continues To", "child-series-p3"),
    )


def test_build_sppm_publication_plan_uses_print_page_format_and_header_rows():
    plan = _build_print_publication_plan()

    primary_series = plan.primary_series()
    primary_page = primary_series.pages[0]

    assert plan.title == "Wash n' Fold"
    assert primary_series.kind == "map"
    assert primary_page.canvas.bounds.width_px == 1000
    assert primary_page.canvas.bounds.height_px == 1123
    assert primary_page.canvas.usable_region.width_px == 904
    header_band = primary_page.band("header")
    assert header_band is not None
    assert header_band.region.name == "header"
    assert ("Process", "wash_n_fold") in header_band.content.rows
    assert ("Profile", "print") in header_band.content.rows
    assert ("Subprocess View", "parent-only") in header_band.content.rows
    assert ("Nodes", "3") in header_band.content.rows


def test_build_sppm_publication_plan_emits_child_slots_for_subprocesses():
    plan = _build_print_publication_plan()

    assert len(plan.artifact_slots) == 1
    assert plan.artifact_slots[0].slot_id == "child:prep"
    assert plan.artifact_slots[0].kind == "child_map"
    assert plan.artifact_slots[0].metadata["detail_map_ref"] == "SP-01"


def _build_print_publication_plan():
    return build_sppm_publication_plan(
        process={
            "process": {
                "id": "wash_n_fold",
                "name": "Wash n' Fold",
                "metadata": {"owner": "Laundry Ops", "revision": "R2"},
            }
        },
        options=RenderOptions.from_mapping(
            {"diagram": "sppm", "sppm_output_profile": "print", "subprocess_view": "parent_only"}
        ),
        nodes=[
            {"id": "start", "kind": "start", "name": "Start"},
            {
                "id": "prep",
                "kind": "subprocess",
                "name": "Prep",
                "metadata": {"detail_map_ref": "SP-01"},
            },
            {"id": "end", "kind": "end", "name": "End"},
        ],
        edges=[{"source": "start", "target": "prep"}, {"source": "prep", "target": "end"}],
    )


def _inline_budget_process() -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    process = {"process": {"id": "demo", "name": "Demo Process"}}
    nodes = [
        {"id": "start", "kind": "start", "name": "Start"},
        {"id": "prep", "kind": "subprocess", "name": "Prep"},
        {"id": "a", "kind": "task", "name": "A", "subprocess_parent": "prep"},
        {"id": "b", "kind": "task", "name": "B", "subprocess_parent": "prep"},
        {"id": "c", "kind": "task", "name": "C", "subprocess_parent": "prep"},
        {"id": "d", "kind": "task", "name": "D", "subprocess_parent": "prep"},
        {"id": "e", "kind": "task", "name": "E", "subprocess_parent": "prep"},
        {"id": "end", "kind": "end", "name": "End"},
    ]
    edges = [
        {"source": "start", "target": "prep"},
        {"source": "prep", "target": "a"},
        {"source": "a", "target": "b"},
        {"source": "b", "target": "c"},
        {"source": "c", "target": "d"},
        {"source": "d", "target": "e"},
        {"source": "e", "target": "end"},
    ]
    return process, nodes, edges


def test_materialize_publication_series_builds_stable_multi_page_ids_and_metadata():
    first_canvas = build_publication_canvas(
        bounds=PublicationBounds(width_px=1200, height_px=900),
        margins=PublicationMargins(),
        header_height_px=100,
        footer_height_px=80,
    )
    second_canvas = build_publication_canvas(
        bounds=PublicationBounds(width_px=1200, height_px=900),
        margins=PublicationMargins(),
        header_height_px=100,
        footer_height_px=80,
    )

    series = materialize_publication_series(
        series_id="main",
        title="Publication Demo",
        kind="map",
        page_specs=(
            PublicationPageSpec(
                page_key="p1",
                canvas=first_canvas,
                header_content=PublicationBandContent(title="Page 1"),
                metadata={"section": "alpha"},
            ),
            PublicationPageSpec(
                page_key="p2",
                canvas=second_canvas,
                footer_content=PublicationBandContent(notes=("Page 2 footer",)),
                metadata={"section": "beta"},
            ),
        ),
        metadata={"diagram": "sppm"},
    )

    assert series.metadata["page_count"] == 2
    assert series.pages[0].page_id == "main-p1"
    assert series.pages[0].page_number == 1
    assert series.pages[0].metadata["page_count"] == 2
    assert series.pages[0].metadata["section"] == "alpha"
    assert series.pages[0].band("header").content.context_rows == (("Page", "1/2"), ("Series", "main"))
    assert series.pages[1].page_id == "main-p2"
    assert series.pages[1].page_number == 2
    assert series.pages[1].metadata["page_id"] == "main-p2"
    assert series.pages[1].metadata["section"] == "beta"
    footer_band = series.pages[1].band("footer")
    assert footer_band is not None
    assert footer_band.content.context_rows == (("Page", "2/2"), ("Series", "main"))


def test_build_sppm_publication_plan_uses_shared_series_materialization_metadata():
    process = {
        "process": {
            "id": "wash_n_fold",
            "name": "Wash n' Fold",
        }
    }

    plan = build_sppm_publication_plan(
        process=process,
        options=RenderOptions(diagram="sppm"),
        nodes=[{"id": "start", "kind": "start", "name": "Start"}],
        edges=[],
    )

    page = plan.primary_series().pages[0]
    assert plan.primary_series().metadata["page_count"] == 1
    assert page.page_id == "main-p1"
    assert page.metadata["page_number"] == 1
    assert page.metadata["page_count"] == 1
    assert page.metadata["page_format"] is None


def test_build_sppm_publication_plan_records_page_format_metadata():
    process = {"process": {"id": "wash_n_fold", "name": "Wash n' Fold"}}

    plan = build_sppm_publication_plan(
        process=process,
        options=RenderOptions.from_mapping({"diagram": "sppm", "publication_page_format": "letter"}),
        nodes=[{"id": "start", "kind": "start", "name": "Start"}],
        edges=[],
    )

    page = plan.primary_series().pages[0]
    assert page.canvas.bounds.width_px == 816
    assert page.canvas.bounds.height_px == 1056
    assert page.metadata["page_format"] == "letter"


def test_build_sppm_publication_plan_records_non_strict_readability_warning():
    process, nodes, edges = _inline_budget_process()
    options = RenderOptions.from_mapping(
        {
            "diagram": "sppm",
            "sppm_projection": "inline",
            "sppm_focus_subprocess": "prep",
            "layout_fit": "fit-preferred",
            "layout_target_columns": 3,
        }
    )
    projected_nodes, projected_edges, projection = project_sppm_subprocess_view(nodes, edges, options=options)

    plan = build_sppm_publication_plan(
        process=process,
        options=options,
        nodes=projected_nodes,
        edges=projected_edges,
        projection=projection,
    )

    diagnostics = plan.metadata["publication_diagnostics"]
    assert diagnostics[0]["severity"] == "warning"
    assert diagnostics[0]["fallback_reason"] == "inline-budget-exceeded"
    header_rows = plan.primary_series().pages[0].band("header").content.rows
    assert any(label == "Readability Warning" and "inline budget exceeded" in value for label, value in header_rows)


def test_build_sppm_publication_plan_raises_on_strict_publication_fallback():
    import pytest

    process, nodes, edges = _inline_budget_process()
    options = RenderOptions.from_mapping(
        {
            "diagram": "sppm",
            "sppm_projection": "inline",
            "sppm_focus_subprocess": "prep",
            "layout_fit": "fit-strict",
            "layout_target_columns": 3,
        }
    )
    projected_nodes, projected_edges, projection = project_sppm_subprocess_view(nodes, edges, options=options)

    with pytest.raises(RenderError, match="fell back to 'child_map'"):
        build_sppm_publication_plan(
            process=process,
            options=options,
            nodes=projected_nodes,
            edges=projected_edges,
            projection=projection,
        )


def test_build_publication_bands_omits_unpopulated_regions():
    canvas = build_publication_canvas(
        bounds=PublicationBounds(width_px=1200, height_px=900),
        margins=PublicationMargins(),
        header_height_px=100,
        footer_height_px=80,
    )

    bands = build_publication_bands(
        canvas=canvas,
        header_content=PublicationBandContent(title="Header"),
    )

    assert len(bands) == 1
    assert bands[0].name == "header"
    assert bands[0].region.name == "header"


def test_build_sppm_publication_plan_populates_footer_band_from_process_metadata():
    process = {
        "process": {
            "id": "wash_n_fold",
            "name": "Wash n' Fold",
            "metadata": {
                "footer_notes": ["Draft for review", "Confidential"],
            },
        }
    }

    plan = build_sppm_publication_plan(
        process=process,
        options=RenderOptions(diagram="sppm"),
        nodes=[{"id": "start", "kind": "start", "name": "Start"}],
        edges=[],
    )

    footer_band = plan.primary_series().pages[0].band("footer")
    assert footer_band is not None
    assert footer_band.region.name == "footer"
    assert footer_band.content.notes == ("Draft for review", "Confidential")


def test_build_sppm_publication_plan_populates_footer_metrics_and_render_inputs():
    process = {
        "process": {
            "id": "ops_review",
            "name": "Ops Review",
            "metadata": {
                "footer_metrics": {
                    "Lead Time": "24 min",
                    "VA Ratio": "61%",
                },
            },
        }
    }

    plan = build_sppm_publication_plan(
        process=process,
        options=RenderOptions(
            diagram="sppm",
            sppm_footer_metrics=(("Queue", "7 min"),),
            sppm_footer_notes=("Handcrafted note",),
        ),
        nodes=[{"id": "start", "kind": "start", "name": "Start"}],
        edges=[],
    )

    footer_band = plan.primary_series().pages[0].band("footer")
    assert footer_band is not None
    assert ("Lead Time", "24 min") in footer_band.content.rows
    assert ("VA Ratio", "61%") in footer_band.content.rows
    assert ("Queue", "7 min") in footer_band.content.rows
    assert footer_band.content.notes == ("Handcrafted note",)


def test_build_sppm_publication_plan_supports_legend_and_caption_metadata_aliases():
    process = {
        "process": {
            "id": "ops_review",
            "name": "Ops Review",
            "metadata": {
                "legend_items": {"Queue": "7 min", "Rework": "8%"},
                "caption": "Draft for review",
            },
        }
    }

    plan = build_sppm_publication_plan(
        process=process,
        options=RenderOptions(diagram="sppm"),
        nodes=[{"id": "start", "kind": "start", "name": "Start"}],
        edges=[],
    )

    footer_band = plan.primary_series().pages[0].band("footer")
    assert footer_band is not None
    assert ("Queue", "7 min") in footer_band.content.rows
    assert ("Rework", "8%") in footer_band.content.rows
    assert footer_band.content.notes == ("Draft for review",)