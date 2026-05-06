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


def test_sppm_renders_process_title_and_header_metadata():
    ir_like = {
        "process": {
            "id": "wash_n_fold",
            "name": "Wash n' Fold",
            "metadata": {"owner": "Laundry Ops", "revision": "R2"},
        },
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [{"source": "start", "target": "end"}],
    }
    out = render_dot(ir_like, options={"diagram": "sppm", "sppm_output_profile": "print"})
    assert "Wash n' Fold" in out
    assert "Process:" in out
    assert "wash_n_fold" in out
    assert "Owner:" in out
    assert "Laundry Ops" in out
    assert "Revision:" in out
    assert "R2" in out
    assert "Profile:" in out
    assert "print" in out


def test_sppm_header_coexists_with_queue_rework_and_notes_in_default_output():
    ir_like = {
        "process": {
            "id": "header_demo",
            "name": "Header Demo",
            "metadata": {"owner": "Ops", "revision": "R1"},
        },
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {
                "id": "queue",
                "kind": "queue",
                "name": "Inbox",
                "metadata": {"wait_time": {"value": 7, "unit": "min"}},
            },
            {"id": "check", "kind": "decision", "name": "Ready?"},
            {
                "id": "work",
                "kind": "task",
                "name": "Do Work",
                "note": "Requires manager signoff",
                "metadata": {"value_class": "VA", "cycle_time": {"value": 4, "unit": "min"}},
            },
            {
                "id": "rework",
                "kind": "task",
                "name": "Fix Input",
                "metadata": {"value_class": "RNVA", "cycle_time": {"value": 3, "unit": "min"}},
            },
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "queue"},
            {"source": "queue", "target": "check"},
            {"source": "check", "target": "work", "outcome": "yes"},
            {
                "source": "check",
                "target": "rework",
                "outcome": "no",
                "edge_type": "rework",
                "rework": True,
                "metadata": {"rate": 0.12, "reason": "Missing details"},
            },
            {"source": "rework", "target": "queue", "edge_type": "rework", "rework": True},
            {"source": "work", "target": "end"},
        ],
    }

    out = render_dot(ir_like, options={"diagram": "sppm", "show_notes": True})

    assert "Header Demo" in out
    assert "Process:" in out
    assert "header_demo" in out
    assert "Owner:" in out
    assert "Ops" in out
    assert "Inbox" in out
    assert "Note: Requires manager signoff" in out
    assert "Rate: 12%" in out
    assert "Reason: Missing details" in out