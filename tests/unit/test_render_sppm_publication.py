from flo.render import render_dot


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