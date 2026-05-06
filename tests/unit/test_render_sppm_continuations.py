from flo.render import render_dot


def test_sppm_wrap_boundary_edges_show_continuation_labels():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "a", "kind": "task", "name": "A", "metadata": {}},
            {"id": "b", "kind": "task", "name": "B", "metadata": {}},
            {"id": "c", "kind": "task", "name": "C", "metadata": {}},
            {"id": "d", "kind": "task", "name": "D", "metadata": {}},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "a"},
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "d"},
            {"source": "d", "target": "end"},
        ],
    }

    out = render_dot(
        ir_like,
        options={
            "diagram": "sppm",
            "orientation": "lr",
            "layout_wrap": "auto",
            "layout_target_columns": 3,
        },
    )

    assert 'Continue to p2 [c]' in out
    assert 'Continued from p1 [b]' in out


def test_sppm_wrap_rework_edges_show_lighter_continuation_labels():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "prep", "kind": "task", "name": "Prep", "metadata": {}},
            {"id": "decision", "kind": "decision", "name": "Approved?"},
            {"id": "rework", "kind": "task", "name": "Rework", "metadata": {"value_class": "NVA"}},
            {"id": "finish", "kind": "task", "name": "Finish", "metadata": {"value_class": "VA"}},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "prep"},
            {"source": "prep", "target": "decision"},
            {"source": "decision", "target": "finish", "outcome": "yes"},
            {"source": "decision", "target": "rework", "outcome": "no", "edge_type": "rework", "rework": True},
            {"source": "rework", "target": "finish", "edge_type": "rework", "rework": True},
            {"source": "finish", "target": "end"},
        ],
    }

    out = render_dot(
        ir_like,
        options={
            "diagram": "sppm",
            "orientation": "lr",
            "layout_wrap": "auto",
            "layout_target_columns": 3,
        },
    )

    assert 'Continue to p2 [rework]' in out
    assert 'Continued from p1 [decision]' in out
    assert 'style=dashed' in out