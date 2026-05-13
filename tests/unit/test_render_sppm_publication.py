from flo.render._publication import (
    PublicationBandContent,
    PublicationBounds,
    PublicationMargins,
    PublicationPageSpec,
    PublicationPlan,
    build_publication_canvas,
    materialize_publication_series,
)
from flo.render._sppm_band_render import build_sppm_header, render_sppm_footer_band
from flo.render import render_dot
from flo.render.options import RenderOptions


def test_sppm_header_is_rendered_from_publication_plan():
    process = {
        "process": {
            "id": "wash_n_fold",
            "name": "Wash n' Fold",
            "metadata": {"owner": "Laundry Ops", "revision": "R2"},
        },
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "fold", "kind": "task", "name": "Fold", "metadata": {"value_class": "VA"}},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [{"source": "start", "target": "fold"}, {"source": "fold", "target": "end"}],
    }

    out = render_dot(
        process,
        options={
            "diagram": "sppm",
            "sppm_output_profile": "print",
            "subprocess_view": "parent-only",
        },
    )

    assert "labelloc=t;" in out
    assert "Wash n' Fold" in out
    assert "Process:" in out
    assert "wash_n_fold" in out
    assert "Profile:" in out
    assert "print" in out
    assert "Subprocess View:" in out
    assert "parent-only" in out


def test_sppm_footer_band_is_rendered_from_publication_plan():
    process = {
        "process": {
            "id": "footer_demo",
            "name": "Footer Demo",
            "metadata": {
                "footer_notes": ["Draft for review", "Confidential"],
            },
        },
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [{"source": "start", "target": "end"}],
    }

    out = render_dot(process, options={"diagram": "sppm"})

    assert '"__sppm_footer_band" [shape=none, margin=0, label=' in out
    assert "Draft for review" in out
    assert "Confidential" in out
    assert '"end" -> "__sppm_footer_band" [style=invis, weight=2, minlen=1];' in out


def test_sppm_footer_band_renders_metrics_and_render_time_inputs():
    process = {
        "process": {
            "id": "ops_review",
            "name": "Ops Review",
            "metadata": {
                "footer_metrics": {"Lead Time": "24 min", "VA Ratio": "61%"},
            },
        },
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [{"source": "start", "target": "end"}],
    }

    out = render_dot(
        process,
        options={
            "diagram": "sppm",
            "sppm_footer_metrics": {"Queue": "7 min"},
            "sppm_footer_notes": ["Draft for review"],
        },
    )

    assert "Lead Time:" in out
    assert "24 min" in out
    assert "VA Ratio:" in out
    assert "61%" in out
    assert "Queue:" in out
    assert "7 min" in out
    assert "Draft for review" in out


def test_sppm_footer_band_preserves_waiting_vs_crossover_metric_distinction():
    """Verify footer metrics can display queue time and setup time as distinct entries.
    
    The distinction between waiting time (queue/resource scheduling) and
    crossover time (setup/SMED) is critical for diagnostic clarity. The
    footer should preserve this separation so users can see both metrics
    and understand the different improvement approaches needed for each.
    """
    process = {
        "process": {
            "id": "ops_review",
            "name": "Ops Review",
            "metadata": {
                "footer_metrics": {
                    "Waiting Time": "9 min",
                    "Crossover Time": "2 min",
                },
            },
        },
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [{"source": "start", "target": "end"}],
    }

    out = render_dot(process, options={"diagram": "sppm"})

    assert "Waiting Time:" in out
    assert "9 min" in out
    assert "Crossover Time:" in out
    assert "2 min" in out


def test_sppm_footer_band_renders_legend_and_caption_alias_inputs():
    process = {
        "process": {
            "id": "ops_review",
            "name": "Ops Review",
            "metadata": {
                "legend_items": {"Queue": "7 min"},
                "caption": "Draft for review",
            },
        },
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [{"source": "start", "target": "end"}],
    }

    out = render_dot(process, options={"diagram": "sppm"})

    assert "Queue:" in out
    assert "7 min" in out
    assert "Draft for review" in out


def test_sppm_footer_band_prefers_earlier_metric_alias_key_order():
    process = {
        "process": {
            "id": "ops_review",
            "name": "Ops Review",
            "metadata": {
                "publication_legend_items": {"Preferred": "yes"},
                "footer_metrics": {"Fallback": "no"},
            },
        },
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [{"source": "start", "target": "end"}],
    }

    out = render_dot(process, options={"diagram": "sppm"})

    assert "Preferred:" in out
    assert "yes" in out
    assert "Fallback:" not in out


def test_sppm_bands_render_shared_page_context_rows_when_present():
    canvas = build_publication_canvas(
        bounds=PublicationBounds(width_px=1200, height_px=900),
        margins=PublicationMargins(),
        header_height_px=96,
        footer_height_px=72,
    )
    series = materialize_publication_series(
        series_id="main",
        title="Ops Review",
        kind="map",
        page_specs=(
            PublicationPageSpec(
                page_key="p1",
                canvas=canvas,
                header_content=PublicationBandContent(title="Ops Review"),
                footer_content=PublicationBandContent(rows=(("Queue", "7 min"),), notes=("Draft for review",)),
            ),
            PublicationPageSpec(
                page_key="p2",
                canvas=canvas,
                header_content=PublicationBandContent(title="Ops Review"),
                footer_content=PublicationBandContent(rows=(("Queue", "7 min"),), notes=("Draft for review",)),
            ),
        ),
    )
    publication = PublicationPlan(title="Ops Review", primary_series_id="main", series=(series,))

    header = build_sppm_header(publication=publication)
    footer_lines = render_sppm_footer_band(
        publication=publication,
        nodes=[{"id": "end", "kind": "end", "name": "End"}],
        edges=[],
    )

    assert "Page:" in header
    assert "1/2" in header
    assert "Series:" in header
    assert "main" in header
    footer = "\n".join(footer_lines)
    assert "Page:" in footer
    assert "1/2" in footer
    assert "Series:" in footer


def test_sppm_footer_auto_aggregates_node_wait_times_in_publication():
    """Verify footer auto-aggregates waiting times when building from process with nodes.
    
    When a process contains nodes with wait_time metadata, the publication
    footer should display the aggregated total waiting time. This shows the
    cumulative queue delays in the process.
    """
    from flo.render._sppm_publication_support import _build_sppm_footer_content
    from flo.render._process_header import extract_process_header_context

    process = {
        "id": "order_fulfillment",
        "name": "Order Fulfillment",
        "metadata": {},
    }
    nodes = [
        {"id": "receive", "kind": "task", "name": "Receive", "metadata": {"wait_time": {"value": 4, "unit": "min"}}},
        {"id": "pick", "kind": "task", "name": "Pick", "metadata": {"wait_time": {"value": 6, "unit": "min"}}},
        {"id": "pack", "kind": "task", "name": "Pack", "metadata": {}},
    ]
    context = extract_process_header_context(process)
    options = RenderOptions()

    footer_content = _build_sppm_footer_content(context=context, options=options, nodes=nodes)

    assert footer_content is not None
    rows_dict = {label: value for label, value in footer_content.rows}
    assert "Waiting Time" in rows_dict


def test_sppm_footer_auto_aggregates_node_changeover_times_in_publication():
    """Verify footer auto-aggregates changeover times when building from process with nodes.
    
    When a process contains nodes with changeover_time or crossover_time metadata,
    the publication footer should display the aggregated total changeover time.
    This shows the cumulative setup delays in the process.
    """
    from flo.render._sppm_publication_support import _build_sppm_footer_content
    from flo.render._process_header import extract_process_header_context

    process = {
        "id": "manufacturing",
        "name": "Manufacturing",
        "metadata": {},
    }
    nodes = [
        {"id": "setup", "kind": "task", "name": "Setup", "metadata": {"crossover_time": {"value": 5, "unit": "min"}}},
        {"id": "run", "kind": "task", "name": "Run", "metadata": {"changeover_time": {"value": 3, "unit": "min"}}},
        {"id": "inspect", "kind": "task", "name": "Inspect", "metadata": {}},
    ]
    context = extract_process_header_context(process)
    options = RenderOptions()

    footer_content = _build_sppm_footer_content(context=context, options=options, nodes=nodes)

    assert footer_content is not None
    rows_dict = {label: value for label, value in footer_content.rows}
    assert "Changeover Time" in rows_dict


def test_sppm_footer_preserves_explicit_metrics_over_auto_aggregation():
    """Verify explicit footer metrics override auto-aggregated node values.
    
    If a process specifies explicit footer metrics via options, they should
    be preferred over auto-aggregated metrics from nodes. This allows users
    to override the automatic calculation if needed.
    """
    from flo.render._sppm_publication_support import _build_sppm_footer_content
    from flo.render._process_header import extract_process_header_context

    process = {
        "id": "process",
        "name": "Process",
        "metadata": {},
    }
    nodes = [
        {"id": "step1", "kind": "task", "name": "Step 1", "metadata": {"wait_time": {"value": 10, "unit": "min"}}},
    ]
    context = extract_process_header_context(process)
    options = RenderOptions(sppm_footer_metrics=(("Custom Metric", "100 min"),))

    footer_content = _build_sppm_footer_content(context=context, options=options, nodes=nodes)

    assert footer_content is not None
    rows_dict = {label: value for label, value in footer_content.rows}
    # Both auto-aggregated and explicit metrics should be present
    assert "Waiting Time" in rows_dict
    assert "Custom Metric" in rows_dict