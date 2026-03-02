from flo.render.graphviz_dot import render_flowchart_dot, render_swimlane_dot
from flo.render import render_dot


def test_render_flowchart_dot():
    out = render_flowchart_dot({})
    assert "digraph" in out


def test_render_swimlane_dot():
    out = render_swimlane_dot({})
    assert "digraph" in out


def test_flowchart_does_not_emit_lane_clusters_for_laned_nodes():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start", "lane": "sales"},
            {"id": "task", "kind": "task", "name": "Task", "lane": "ops"},
        ],
        "edges": [{"source": "start", "target": "task"}],
    }
    out = render_dot(ir_like, options={"diagram": "flowchart"})
    assert "subgraph cluster_" not in out


def test_swimlane_emits_lane_clusters_for_laned_nodes():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start", "lane": "sales"},
            {"id": "task", "kind": "task", "name": "Task", "lane": "ops"},
        ],
        "edges": [{"source": "start", "target": "task"}],
    }
    out = render_dot(ir_like, options={"diagram": "swimlane"})
    assert "subgraph cluster_sales" in out
    assert "subgraph cluster_ops" in out


def test_summary_detail_omits_edge_labels():
    ir_like = {
        "nodes": [
            {"id": "d", "kind": "decision", "name": "Decision"},
            {"id": "a", "kind": "task", "name": "Approve"},
        ],
        "edges": [{"source": "d", "target": "a", "outcome": "yes"}],
    }
    out = render_dot(ir_like, options={"detail": "summary"})
    assert "label=\"yes\"" not in out


def test_verbose_analysis_detail_includes_kind_and_lane():
    ir_like = {
        "nodes": [
            {"id": "task_1", "kind": "task", "name": "Work", "lane": "ops"},
        ],
        "edges": [],
    }
    out = render_dot(ir_like, options={"detail": "verbose", "profile": "analysis"})
    assert "[task|lane:ops]" in out
