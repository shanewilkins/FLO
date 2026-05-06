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