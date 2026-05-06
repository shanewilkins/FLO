from flo.render import render_dot


def test_sppm_parent_only_hides_subprocess_children_and_collapses_path():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "prep", "kind": "subprocess", "name": "Prep"},
            {"id": "gather", "kind": "task", "name": "Gather", "subprocess_parent": "prep"},
            {"id": "mix", "kind": "task", "name": "Mix", "subprocess_parent": "prep"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "prep"},
            {"source": "prep", "target": "gather"},
            {"source": "gather", "target": "mix"},
            {"source": "mix", "target": "end"},
        ],
    }
    out = render_dot(ir_like, options={"diagram": "sppm", "subprocess_view": "parent-only"})
    assert '"gather"' not in out
    assert '"mix"' not in out
    assert '"prep"' in out
    assert '"start" -> "prep"' in out
    assert '"prep" -> "end"' in out


def test_sppm_subprocess_nodes_include_marker_and_detail_map_reference():
    ir_like = {
        "nodes": [
            {
                "id": "prep",
                "kind": "subprocess",
                "name": "Prep",
                "metadata": {"detail_map_ref": "SP-01", "value_class": "RNVA"},
            }
        ],
        "edges": [],
    }
    out = render_dot(ir_like, options={"diagram": "sppm"})
    assert "[Subprocess] Prep" in out
    assert "Subprocess" in out
    assert "Detail map: SP-01" in out