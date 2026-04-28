"""Unit tests for the SPPM routing-plan helper module."""

from flo.render import render_dot
from flo.render._autoformat_wrap import build_autoformat_wrap_plan
from flo.render._sppm_routing import build_sppm_routing_plan, serialize_sppm_routing_plan
from flo.render.options import RenderOptions


def test_sppm_rework_edge_uses_corridor_anchor_and_lr_ports():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "review", "kind": "task", "name": "Review", "metadata": {}},
            {"id": "decision", "kind": "decision", "name": "Valid?", "metadata": {}},
            {"id": "rework", "kind": "task", "name": "Rework", "metadata": {}},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "review"},
            {"source": "review", "target": "decision"},
            {"source": "decision", "target": "rework", "outcome": "no", "edge_type": "rework", "rework": True},
            {"source": "rework", "target": "end"},
        ],
    }

    out = render_dot(ir_like, options={"diagram": "sppm"})
    assert '"__sppm_rework_corridor_decision_rework" [shape=point, width=0.01, height=0.01, label="", style=invis];' in out
    assert '"decision" -> "__sppm_rework_corridor_decision_rework" [tailport=e, constraint=false, style=dashed, weight=0, arrowhead=none];' in out
    assert '"__sppm_rework_corridor_decision_rework" -> "rework" [headport=w, constraint=false, minlen=3, weight=0, style=dashed, label="no"];' in out


def test_sppm_rework_edge_uses_tb_ports_when_rankdir_tb():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "review", "kind": "task", "name": "Review", "metadata": {}},
            {"id": "decision", "kind": "decision", "name": "Valid?", "metadata": {}},
            {"id": "rework", "kind": "task", "name": "Rework", "metadata": {}},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "review"},
            {"source": "review", "target": "decision"},
            {"source": "decision", "target": "rework", "outcome": "no", "edge_type": "rework", "rework": True},
            {"source": "rework", "target": "end"},
        ],
    }

    out = render_dot(ir_like, options={"diagram": "sppm", "orientation": "tb"})
    assert '"decision" -> "__sppm_rework_corridor_decision_rework" [tailport=s, constraint=false, style=dashed, weight=0, arrowhead=none];' in out
    assert '"__sppm_rework_corridor_decision_rework" -> "rework" [headport=n, constraint=false, minlen=3, weight=0, style=dashed, label="no"];' in out


def test_sppm_routing_plan_marks_wrap_boundary_edges_with_ports_and_boundary_attrs():
    nodes = [
        {"id": "start", "kind": "start", "name": "Start"},
        {"id": "a", "kind": "task", "name": "A", "metadata": {}},
        {"id": "b", "kind": "task", "name": "B", "metadata": {}},
        {"id": "c", "kind": "task", "name": "C", "metadata": {}},
        {"id": "end", "kind": "end", "name": "End"},
    ]
    edges = [
        {"source": "start", "target": "a"},
        {"source": "a", "target": "b"},
        {"source": "b", "target": "c"},
        {"source": "c", "target": "end"},
    ]
    options = RenderOptions(diagram="sppm", orientation="lr", layout_wrap="auto", layout_target_columns=2)
    wrap_plan = build_autoformat_wrap_plan(nodes, options)

    routing_plan = build_sppm_routing_plan(
        edges=edges,
        options=options,
        step_numbering={"a": 1, "b": 2, "c": 3},
        wrap_plan=wrap_plan,
    )

    route = routing_plan.route_for("a", "b")
    assert route is not None
    assert route.kind == "corridor"
    assert route.is_boundary is True
    assert route.lane_id == "wrap_lane_0"
    assert route.corridor_nodes == ()
    assert route.segments[0].attrs == ("tailport=e", "headport=w", "minlen=2", "penwidth=1.2")


def test_sppm_routing_plan_splits_rework_edges_into_anchor_segments():
    edges = [
        {"source": "decision", "target": "rework", "outcome": "no", "edge_type": "rework", "rework": True},
    ]
    options = RenderOptions(diagram="sppm")

    routing_plan = build_sppm_routing_plan(
        edges=edges,
        options=options,
        step_numbering={"review": 1, "decision": 2, "rework": 1},
        wrap_plan=build_autoformat_wrap_plan([], options),
    )

    route = routing_plan.route_for("decision", "rework")
    assert route is not None
    assert route.kind == "rework"
    assert route.anchors[0].anchor_id == "__sppm_rework_corridor_decision_rework"
    assert route.segments[0].attrs == (
        "tailport=e",
        "constraint=false",
        "style=dashed",
        "weight=0",
        "arrowhead=none",
    )
    assert route.segments[1].attrs == (
        "headport=w",
        "constraint=false",
        "minlen=3",
        "weight=0",
        "style=dashed",
        'label="no"',
    )


def test_sppm_routing_plan_uses_tb_ports_for_wrapped_tb_layout():
    nodes = [
        {"id": "start", "kind": "start", "name": "Start"},
        {"id": "a", "kind": "task", "name": "A", "metadata": {}},
        {"id": "b", "kind": "task", "name": "B", "metadata": {}},
        {"id": "c", "kind": "task", "name": "C", "metadata": {}},
    ]
    edges = [{"source": "a", "target": "b"}, {"source": "b", "target": "c"}]
    options = RenderOptions(diagram="sppm", orientation="tb", layout_wrap="auto", layout_target_columns=2)
    wrap_plan = build_autoformat_wrap_plan(nodes, options)

    routing_plan = build_sppm_routing_plan(
        edges=edges,
        options=options,
        step_numbering={"a": 1, "b": 2, "c": 3},
        wrap_plan=wrap_plan,
    )

    route = routing_plan.route_for("a", "b")
    assert route is not None
    assert route.kind == "corridor"
    assert route.segments[0].attrs == ("tailport=s", "headport=n", "minlen=2", "penwidth=1.2")


def test_sppm_routing_plan_snapshot_wrap_boundary_and_direct_segments():
    nodes = [
        {"id": "start", "kind": "start", "name": "Start"},
        {"id": "a", "kind": "task", "name": "A", "metadata": {}},
        {"id": "b", "kind": "task", "name": "B", "metadata": {}},
        {"id": "c", "kind": "task", "name": "C", "metadata": {}},
        {"id": "end", "kind": "end", "name": "End"},
    ]
    edges = [
        {"source": "start", "target": "a"},
        {"source": "a", "target": "b"},
        {"source": "b", "target": "c"},
        {"source": "c", "target": "end"},
    ]
    options = RenderOptions(diagram="sppm", orientation="lr", layout_wrap="auto", layout_target_columns=2)
    wrap_plan = build_autoformat_wrap_plan(nodes, options)

    routing_plan = build_sppm_routing_plan(
        edges=edges,
        options=options,
        step_numbering={"a": 1, "b": 2, "c": 3},
        wrap_plan=wrap_plan,
    )

    snapshot = serialize_sppm_routing_plan(routing_plan)
    expected = "\n".join(
        [
            "edge a->b kind=corridor boundary=True rework=False",
            "  lane wrap_lane_0",
            "  segment a->b [tailport=e, headport=w, minlen=2, penwidth=1.2]",
            "edge b->c kind=direct boundary=False rework=False",
            "  segment b->c [tailport=e, headport=w]",
            "edge c->end kind=corridor boundary=True rework=False",
            "  lane wrap_lane_1",
            "  segment c->end [tailport=e, headport=w, minlen=2, penwidth=1.2]",
            "edge start->a kind=direct boundary=False rework=False",
            "  segment start->a [tailport=e, headport=w]",
        ]
    )
    assert snapshot == expected


def test_sppm_routing_plan_snapshot_rework_includes_anchor_segments():
    edges = [
        {"source": "decision", "target": "rework", "outcome": "no", "edge_type": "rework", "rework": True},
        {"source": "rework", "target": "done"},
    ]
    options = RenderOptions(diagram="sppm")

    routing_plan = build_sppm_routing_plan(
        edges=edges,
        options=options,
        step_numbering={"decision": 3, "rework": 2, "done": 4},
        wrap_plan=build_autoformat_wrap_plan([], options),
    )

    snapshot = serialize_sppm_routing_plan(routing_plan)
    expected = "\n".join(
        [
            "edge decision->rework kind=rework boundary=False rework=True",
            "  anchor __sppm_rework_corridor_decision_rework [shape=point, width=0.01, height=0.01, label=\"\", style=invis]",
            "  segment decision->__sppm_rework_corridor_decision_rework [tailport=e, constraint=false, style=dashed, weight=0, arrowhead=none]",
            "  segment __sppm_rework_corridor_decision_rework->rework [headport=w, constraint=false, minlen=3, weight=0, style=dashed, label=\"no\"]",
            "edge rework->done kind=direct boundary=False rework=False",
            "  segment rework->done []",
        ]
    )
    assert snapshot == expected