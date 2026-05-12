from flo.render import render_dot


def test_sppm_rework_edges_render_metadata_as_data_box():
    ir_like = {
        "nodes": [
            {"id": "decision", "kind": "decision", "name": "Approved?"},
            {"id": "rework", "kind": "task", "name": "Rework", "metadata": {"value_class": "NVA"}},
        ],
        "edges": [
            {
                "source": "decision",
                "target": "rework",
                "outcome": "no",
                "edge_type": "rework",
                "rework": True,
                "metadata": {"rate": 0.08, "reason": "Missing approvals"},
            },
        ],
    }

    out = render_dot(ir_like, options={"diagram": "sppm"})

    assert 'xlabel="no"' in out
    assert 'taillabel=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0"' in out
    assert 'Rate: 8%' in out
    assert 'Reason: Missing' in out
    assert 'approvals' in out


def test_sppm_rework_return_edges_render_frequency_and_count_metadata():
    ir_like = {
        "nodes": [
            {"id": "decision", "kind": "decision", "name": "Approved?"},
            {"id": "rework", "kind": "task", "name": "Rework", "metadata": {"value_class": "NVA"}},
            {"id": "review", "kind": "task", "name": "Review", "metadata": {"value_class": "RNVA"}},
        ],
        "edges": [
            {
                "source": "decision",
                "target": "rework",
                "outcome": "no",
                "edge_type": "rework",
                "rework": True,
            },
            {
                "source": "rework",
                "target": "review",
                "edge_type": "rework",
                "rework": True,
                "metadata": {"frequency": "3/day", "count": "12 per week"},
            },
        ],
    }

    out = render_dot(ir_like, options={"diagram": "sppm"})

    assert 'Frequency: 3/day' in out
    assert 'Count: 12 per week' in out


def test_sppm_rework_return_databox_moves_near_source_when_branch_label_present():
    ir_like = {
        "nodes": [
            {"id": "decision", "kind": "decision", "name": "Approved?"},
            {"id": "rework", "kind": "task", "name": "Rework", "metadata": {"value_class": "NVA"}},
            {"id": "review", "kind": "task", "name": "Review", "metadata": {"value_class": "RNVA"}},
        ],
        "edges": [
            {
                "source": "decision",
                "target": "rework",
                "outcome": "no",
                "edge_type": "rework",
                "rework": True,
            },
            {
                "source": "rework",
                "target": "review",
                "label": "retry",
                "edge_type": "rework",
                "rework": True,
                "metadata": {"frequency": "3/day"},
            },
        ],
    }

    out = render_dot(ir_like, options={"diagram": "sppm"})

    assert '"__sppm_rework_corridor_rework_review" -> "review"' in out
    assert 'xlabel="retry"' in out
    assert 'taillabel=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#666666" BGCOLOR="#FFFFFF"><TR><TD ALIGN="LEFT" BALIGN="LEFT"><FONT POINT-SIZE="10" COLOR="#000000">Frequency: 3/day</FONT></TD></TR></TABLE>>' in out


def test_sppm_queue_connector_to_rework_target_is_not_rendered_as_rework():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "decision", "kind": "decision", "name": "Approved?"},
            {"id": "process_queue", "kind": "queue", "name": "Process Queue", "metadata": {"wait_time": {"value": 11, "unit": "min"}}},
            {
                "id": "process",
                "kind": "task",
                "name": "Process",
                "metadata": {"value_class": "VA", "wait_time": {"value": 11, "unit": "min"}},
            },
            {"id": "rework", "kind": "task", "name": "Rework", "metadata": {"value_class": "NVA"}},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "decision"},
            {"source": "decision", "target": "process_queue", "outcome": "yes"},
            {"source": "process_queue", "target": "process"},
            {"source": "decision", "target": "rework", "outcome": "no", "edge_type": "rework", "rework": True},
            {"source": "rework", "target": "process_queue", "edge_type": "rework", "rework": True},
            {"source": "process", "target": "end"},
        ],
    }

    out = render_dot(ir_like, options={"diagram": "sppm"})

    assert '"rework":w -> "__sppm_rework_corridor_rework_process_queue"' in out
    assert '"process_queue":e -> "process":w' in out
    assert '"process_queue":w -> "__sppm_rework_corridor__queue_process_process"' not in out


def test_sppm_queue_triangles_render_with_wait_metadata_box():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "process_queue", "kind": "queue", "name": "Process Queue", "metadata": {"wait_time": {"value": 11, "unit": "min"}}},
            {
                "id": "process",
                "kind": "task",
                "name": "Process",
                "metadata": {"value_class": "VA", "wait_time": {"value": 11, "unit": "min"}},
            },
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "process_queue"},
            {"source": "process_queue", "target": "process"},
            {"source": "process", "target": "end"},
        ],
    }

    out = render_dot(ir_like, options={"diagram": "sppm"})

    assert '"process_queue" [label=<<TABLE' in out
    assert 'BGCOLOR="#FFB74D"' in out
    assert 'WT: 11 min' in out
    assert 'shape=triangle' in out
    assert 'Process Queue\nprocess_queue' not in out
    assert 'shape=triangle, orientation=0, width=2.1, height=3.0' in out
    assert 'style="solid"' in out
    assert 'fontcolor="#000000"' in out


def test_sppm_queue_triangle_labels_wrap_and_truncate_long_names():
    ir_like = {
        "nodes": [
            {
                "id": "dispatch_queue",
                "kind": "queue",
                "name": "Extremely Long Dispatch Review Queue",
                "metadata": {"wait_time": {"value": 14, "unit": "min"}},
            }
        ],
        "edges": [],
    }

    out = render_dot(ir_like, options={"diagram": "sppm"})

    assert '"dispatch_queue" [label=<<TABLE' in out
    assert 'shape=triangle' in out
    assert 'WT: 14 min' in out
    assert '[dispatch_queue]' not in out