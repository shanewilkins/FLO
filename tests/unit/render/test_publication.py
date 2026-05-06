from flo.render._publication import PublicationBounds, PublicationMargins, build_publication_canvas
from flo.render._sppm_publication import build_sppm_publication_plan
from flo.render.options import RenderOptions


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


def test_build_sppm_publication_plan_includes_primary_series_and_child_slots():
    process = {
        "process": {
            "id": "wash_n_fold",
            "name": "Wash n' Fold",
            "metadata": {"owner": "Laundry Ops", "revision": "R2"},
        }
    }
    nodes = [
        {"id": "start", "kind": "start", "name": "Start"},
        {
            "id": "prep",
            "kind": "subprocess",
            "name": "Prep",
            "metadata": {"detail_map_ref": "SP-01"},
        },
        {"id": "end", "kind": "end", "name": "End"},
    ]
    edges = [{"source": "start", "target": "prep"}, {"source": "prep", "target": "end"}]

    plan = build_sppm_publication_plan(
        process=process,
        options=RenderOptions(diagram="sppm", sppm_output_profile="print", subprocess_view="parent_only"),
        nodes=nodes,
        edges=edges,
    )

    primary_series = plan.primary_series()
    primary_page = primary_series.pages[0]

    assert plan.title == "Wash n' Fold"
    assert primary_series.kind == "map"
    assert primary_page.canvas.usable_region.width_px == 1104
    assert primary_page.header_content is not None
    assert ("Process", "wash_n_fold") in primary_page.header_content.rows
    assert ("Profile", "print") in primary_page.header_content.rows
    assert ("Subprocess View", "parent-only") in primary_page.header_content.rows
    assert ("Nodes", "3") in primary_page.header_content.rows
    assert len(plan.artifact_slots) == 1
    assert plan.artifact_slots[0].slot_id == "child:prep"
    assert plan.artifact_slots[0].kind == "child_map"
    assert plan.artifact_slots[0].metadata["detail_map_ref"] == "SP-01"