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
    assert 'label="sales";' in out
    assert 'label="ops";' in out
    assert '"start" -> "task" [constraint=false];' in out


def test_flowchart_emits_subprocess_clusters_for_parent_links():
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

    out = render_dot(ir_like, options={"diagram": "flowchart"})
    assert "subgraph cluster_subprocess_prep" in out
    assert 'label="Prep";' in out
    assert '"prep" [label="Prep", shape=component, style="rounded,filled", fillcolor="lightsteelblue1", color=steelblue4, penwidth=1.4];' in out


def test_flowchart_subprocess_view_expanded_keeps_children_visible():
    ir_like = {
        "nodes": [
            {"id": "prep", "kind": "subprocess", "name": "Prep"},
            {"id": "gather", "kind": "task", "name": "Gather", "subprocess_parent": "prep"},
            {"id": "mix", "kind": "task", "name": "Mix", "subprocess_parent": "prep"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "prep", "target": "gather"},
            {"source": "gather", "target": "mix"},
            {"source": "mix", "target": "end"},
        ],
    }

    out = render_dot(ir_like, options={"diagram": "flowchart", "subprocess_view": "expanded"})
    assert "subgraph cluster_subprocess_prep" in out
    assert '"gather" [label="Gather", shape=box];' in out
    assert '"mix" [label="Mix", shape=box];' in out


def test_flowchart_subprocess_view_parent_only_hides_children_and_collapses_path():
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

    out = render_dot(ir_like, options={"diagram": "flowchart", "subprocess_view": "parent-only"})
    assert "subgraph cluster_subprocess_prep" not in out
    assert '"gather" [label="Gather", shape=box];' not in out
    assert '"mix" [label="Mix", shape=box];' not in out
    assert '"prep" -> "end" [];' in out


def test_flowchart_parent_only_collapses_nested_subprocess_depth():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "outer", "kind": "subprocess", "name": "Outer"},
            {"id": "inner", "kind": "subprocess", "name": "Inner", "subprocess_parent": "outer"},
            {"id": "task", "kind": "task", "name": "Task", "subprocess_parent": "inner"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "outer"},
            {"source": "outer", "target": "inner"},
            {"source": "inner", "target": "task"},
            {"source": "task", "target": "end"},
        ],
    }

    out = render_dot(ir_like, options={"diagram": "flowchart", "subprocess_view": "parent-only"})
    assert '"inner" [label="Inner", shape=component' not in out
    assert '"task" [label="Task", shape=box];' not in out
    assert '"outer" -> "end" [];' in out


def test_flowchart_expanded_supports_nested_subprocess_depth():
    ir_like = {
        "nodes": [
            {"id": "outer", "kind": "subprocess", "name": "Outer"},
            {"id": "inner", "kind": "subprocess", "name": "Inner", "subprocess_parent": "outer"},
            {"id": "task", "kind": "task", "name": "Task", "subprocess_parent": "inner"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "outer", "target": "inner"},
            {"source": "inner", "target": "task"},
            {"source": "task", "target": "end"},
        ],
    }

    out = render_dot(ir_like, options={"diagram": "flowchart", "subprocess_view": "expanded"})
    assert "subgraph cluster_subprocess_outer" in out
    assert "subgraph cluster_subprocess_inner" in out
    assert '"inner" [label="Inner", shape=component' in out
    assert '"task" [label="Task", shape=box];' in out


def test_subprocess_parent_from_attrs_is_supported_for_flowchart_clusters():
    ir_like = {
        "nodes": [
            {"id": "prep", "kind": "subprocess", "name": "Prep"},
            {"id": "gather", "kind": "task", "name": "Gather", "attrs": {"subprocess_parent": "prep"}},
        ],
        "edges": [{"source": "prep", "target": "gather"}],
    }

    out = render_dot(ir_like, options={"diagram": "flowchart"})
    assert "subgraph cluster_subprocess_prep" in out
    assert '"gather" [label="Gather", shape=box];' in out


def test_swimlane_emits_lane_boundary_anchors():
    ir_like = {
        "nodes": [
            {"id": "a", "kind": "task", "name": "A", "lane": "sales"},
            {"id": "b", "kind": "task", "name": "B", "lane": "ops"},
        ],
        "edges": [{"source": "a", "target": "b"}],
    }
    out = render_dot(ir_like, options={"diagram": "swimlane"})
    assert "subgraph lane_left_boundary" in out
    assert "subgraph lane_right_boundary" in out
    assert "__lane_sales_left" in out
    assert "__lane_ops_right" in out
    assert '"__lane_sales_left" -> "__lane_ops_left" [style=invis, weight=200, minlen=1];' in out
    assert '"__lane_sales_right" -> "__lane_ops_right" [style=invis, weight=200, minlen=1];' in out


def test_swimlane_emits_lane_local_subprocess_cluster():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start", "lane": "ops"},
            {"id": "prep", "kind": "subprocess", "name": "Prep", "lane": "ops"},
            {"id": "gather", "kind": "task", "name": "Gather", "lane": "ops", "subprocess_parent": "prep"},
            {"id": "mix", "kind": "task", "name": "Mix", "lane": "ops", "subprocess_parent": "prep"},
            {"id": "end", "kind": "end", "name": "End", "lane": "ops"},
        ],
        "edges": [
            {"source": "start", "target": "prep"},
            {"source": "prep", "target": "gather"},
            {"source": "gather", "target": "mix"},
            {"source": "mix", "target": "end"},
        ],
    }

    out = render_dot(ir_like, options={"diagram": "swimlane"})
    assert "subgraph cluster_ops" in out
    assert "subgraph cluster_subprocess_prep" in out
    assert '"prep" [label="Prep", shape=component, style="rounded,filled", fillcolor="lightsteelblue1", color=steelblue4, penwidth=1.4];' in out


def test_swimlane_parent_only_hides_subprocess_children():
    ir_like = {
        "nodes": [
            {"id": "prep", "kind": "subprocess", "name": "Prep", "lane": "ops"},
            {"id": "gather", "kind": "task", "name": "Gather", "lane": "ops", "subprocess_parent": "prep"},
            {"id": "mix", "kind": "task", "name": "Mix", "lane": "ops", "subprocess_parent": "prep"},
            {"id": "end", "kind": "end", "name": "End", "lane": "ops"},
        ],
        "edges": [
            {"source": "prep", "target": "gather"},
            {"source": "gather", "target": "mix"},
            {"source": "mix", "target": "end"},
        ],
    }

    out = render_dot(ir_like, options={"diagram": "swimlane", "subprocess_view": "parent-only"})
    assert "subgraph cluster_ops" in out
    assert "subgraph cluster_subprocess_prep" not in out
    assert '"gather" [label="Gather", shape=box];' not in out
    assert '"mix" [label="Mix", shape=box];' not in out
    assert '"prep" -> "end" [];' in out


def test_swimlane_does_not_cross_lane_subprocess_cluster():
    ir_like = {
        "nodes": [
            {"id": "prep", "kind": "subprocess", "name": "Prep", "lane": "ops"},
            {"id": "gather", "kind": "task", "name": "Gather", "lane": "sales", "subprocess_parent": "prep"},
        ],
        "edges": [{"source": "prep", "target": "gather"}],
    }

    out = render_dot(ir_like, options={"diagram": "swimlane"})
    assert "subgraph cluster_ops" in out
    assert "subgraph cluster_sales" in out
    assert "subgraph cluster_subprocess_prep" not in out
    assert '"gather" [label="Gather", shape=box];' in out


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


def test_standard_detail_omits_parenthesized_node_ids():
    ir_like = {
        "nodes": [
            {"id": "collect_docs", "kind": "task", "name": "Collect Documents"},
        ],
        "edges": [],
    }
    out = render_dot(ir_like)
    assert "Collect Documents" in out
    assert "(collect_docs)" not in out


def test_edges_prefer_graphviz_routing_and_keep_splines_enabled():
    ir_like = {
        "nodes": [
            {"id": "d", "kind": "decision", "name": "Decision"},
            {"id": "a", "kind": "task", "name": "Approve"},
        ],
        "edges": [{"source": "d", "target": "a", "outcome": "yes"}],
    }
    out = render_dot(ir_like)
    assert "splines=true" in out
    assert "tailport=" not in out
    assert "headport=" not in out
    assert 'label="yes"' in out
    assert '"d" [label="Decision", shape=diamond, regular=true];' in out


def test_wait_nodes_use_distinct_wait_symbol():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "rest", "kind": "wait", "name": "Rest Dough"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "rest"},
            {"source": "rest", "target": "end"},
        ],
    }
    out = render_dot(ir_like)
    assert '"rest" [label="Rest Dough", shape=circle];' in out


def test_backward_edge_uses_graphviz_defaults():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "collect", "kind": "task", "name": "Collect"},
            {"id": "approve", "kind": "decision", "name": "Approve?"},
        ],
        "edges": [
            {"source": "collect", "target": "approve"},
            {"source": "approve", "target": "collect", "outcome": "no"},
        ],
    }
    out = render_dot(ir_like)
    assert '"approve" -> "collect" [label="no"];' in out


def test_backward_non_decision_edge_uses_graphviz_defaults():
    ir_like = {
        "nodes": [
            {"id": "a", "kind": "task", "name": "A"},
            {"id": "b", "kind": "task", "name": "B"},
        ],
        "edges": [
            {"source": "a", "target": "b"},
            {"source": "b", "target": "a", "label": "retry"},
        ],
    }
    out = render_dot(ir_like)
    assert '"b" -> "a" [label="retry"];' in out


def test_node_note_hidden_by_default():
    ir_like = {
        "nodes": [
            {"id": "task_1", "kind": "task", "name": "Work", "note": "Requires manager signoff"},
        ],
        "edges": [],
    }
    out = render_dot(ir_like)
    assert "Requires manager signoff" not in out


def test_node_note_shown_when_enabled():
    ir_like = {
        "nodes": [
            {"id": "task_1", "kind": "task", "name": "Work", "note": "Requires manager signoff"},
        ],
        "edges": [],
    }
    out = render_dot(ir_like, options={"show_notes": True})
    assert "Note: Requires manager signoff" in out


def test_orientation_tb_sets_rankdir_tb():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [{"source": "start", "target": "end"}],
    }
    out = render_dot(ir_like, options={"orientation": "tb"})
    assert "rankdir=TB;" in out
