"""Unit tests for the SPPM routing-plan helper module."""

from flo.render import render_dot
from flo.render._autoformat_wrap import build_wrap_plan
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
    wrap_plan = build_wrap_plan(nodes, options, planner="chunked")

    routing_plan = build_sppm_routing_plan(
        nodes=nodes,
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
    assert route.anchors == ()
    assert route.segments[0].target_id == "__wrap_exit_lr_0"
    assert route.segments[0].attrs == ('tailport="out_0:e"', "arrowhead=none", "constraint=false", "weight=0")
    assert route.segments[1].source_id == "__wrap_exit_lr_0"
    assert route.segments[1].attrs == ('headport="boundary_in:s"', "minlen=2", "penwidth=1.2")
    assert set(routing_plan.route_plan.routes.keys()) == {("start", "a"), ("a", "b"), ("b", "c"), ("c", "end")}


def test_sppm_routing_plan_splits_rework_edges_into_anchor_segments():
    edges = [
        {"source": "decision", "target": "rework", "outcome": "no", "edge_type": "rework", "rework": True},
    ]
    options = RenderOptions(diagram="sppm")

    routing_plan = build_sppm_routing_plan(
        nodes=[],
        edges=edges,
        options=options,
        step_numbering={"review": 1, "decision": 2, "rework": 1},
        wrap_plan=build_wrap_plan([], options, planner="chunked"),
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
    assert routing_plan.route_plan.routes == {}


def test_sppm_routing_plan_uses_tb_ports_for_wrapped_tb_layout():
    nodes = [
        {"id": "start", "kind": "start", "name": "Start"},
        {"id": "a", "kind": "task", "name": "A", "metadata": {}},
        {"id": "b", "kind": "task", "name": "B", "metadata": {}},
        {"id": "c", "kind": "task", "name": "C", "metadata": {}},
    ]
    edges = [{"source": "a", "target": "b"}, {"source": "b", "target": "c"}]
    options = RenderOptions(diagram="sppm", orientation="tb", layout_wrap="auto", layout_target_columns=2)
    wrap_plan = build_wrap_plan(nodes, options, planner="chunked")

    routing_plan = build_sppm_routing_plan(
        nodes=nodes,
        edges=edges,
        options=options,
        step_numbering={"a": 1, "b": 2, "c": 3},
        wrap_plan=wrap_plan,
    )

    route = routing_plan.route_for("a", "b")
    assert route is not None
    assert route.kind == "corridor"
    assert route.anchors[0].anchor_id == "__sppm_boundary_corridor_a_b"
    assert route.segments[0].attrs == ("tailport=s", "arrowhead=none", "constraint=false", "weight=0")
    assert route.segments[1].attrs == ("headport=n", "minlen=2", "penwidth=1.2")


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
    wrap_plan = build_wrap_plan(nodes, options, planner="chunked")

    routing_plan = build_sppm_routing_plan(
        nodes=nodes,
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
            "  segment a->__wrap_exit_lr_0 [tailport=\"out_0:e\", arrowhead=none, constraint=false, weight=0]",
            "  segment __wrap_exit_lr_0->b [headport=\"boundary_in:s\", minlen=2, penwidth=1.2]",
            "edge b->c kind=direct boundary=False rework=False",
            "  segment b->c [tailport=e, headport=w]",
            "edge c->end kind=corridor boundary=True rework=False",
            "  lane wrap_lane_1",
            "  segment c->__wrap_exit_lr_1 [tailport=\"out_0:e\", arrowhead=none, constraint=false, weight=0]",
            "  segment __wrap_exit_lr_1->end [headport=n, minlen=2, penwidth=1.2]",
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
        nodes=[],
        edges=edges,
        options=options,
        step_numbering={"decision": 3, "rework": 2, "done": 4},
        wrap_plan=build_wrap_plan([], options, planner="chunked"),
    )

    snapshot = serialize_sppm_routing_plan(routing_plan)
    expected = "\n".join(
        [
            "edge decision->rework kind=rework boundary=False rework=True",
            "  anchor __sppm_rework_corridor_decision_rework [shape=point, width=0.01, height=0.01, label=\"\", style=invis]",
            "  segment decision->__sppm_rework_corridor_decision_rework [tailport=e, constraint=false, style=dashed, weight=0, arrowhead=none]",
            "  segment __sppm_rework_corridor_decision_rework->rework [headport=w, constraint=false, minlen=3, weight=0, style=dashed, label=\"no\"]",
            "edge rework->done kind=direct boundary=False rework=False",
            "  segment rework->done [tailport=e, headport=w]",
        ]
    )
    assert snapshot == expected


def test_sppm_routing_plan_includes_corridor_plan_for_placement_wrap():
    nodes = [
        {"id": "start", "kind": "start", "name": "Start"},
        {"id": "a", "kind": "task", "name": "A", "metadata": {}},
        {"id": "b", "kind": "task", "name": "B", "metadata": {}},
        {"id": "c", "kind": "task", "name": "C", "metadata": {}},
        {"id": "d", "kind": "task", "name": "D", "metadata": {}},
        {"id": "end", "kind": "end", "name": "End"},
    ]
    edges = [
        {"source": "start", "target": "a"},
        {"source": "a", "target": "b"},
        {"source": "b", "target": "c"},
        {"source": "c", "target": "d"},
        {"source": "d", "target": "end"},
    ]
    options = RenderOptions(diagram="sppm", orientation="lr", layout_wrap="auto", layout_target_columns=2)
    wrap_plan = build_wrap_plan(nodes, options, planner="placement")

    routing_plan = build_sppm_routing_plan(
        nodes=nodes,
        edges=edges,
        options=options,
        step_numbering={"a": 1, "b": 2, "c": 3, "d": 4},
        wrap_plan=wrap_plan,
    )

    assert wrap_plan.placement_plan is not None
    assert len(routing_plan.corridor_plan.lanes) == 2
    assert routing_plan.route_plan.route_for("start", "a") is not None
    line_index = wrap_plan.placement_plan.node_line_index
    expected_cross_line = {
        (str(edge["source"]), str(edge["target"]))
        for edge in edges
        if line_index.get(str(edge["source"])) != line_index.get(str(edge["target"]))
    }
    assert set(routing_plan.corridor_plan.edge_lane_hops.keys()) == expected_cross_line
    assert set(routing_plan.route_plan.routes.keys()) == {(
        str(edge["source"]),
        str(edge["target"]),
    ) for edge in edges}
    for lane_hops in routing_plan.corridor_plan.edge_lane_hops.values():
        assert lane_hops
        for lane_id in lane_hops:
            assert lane_id.startswith("corridor_lane_")
    assert routing_plan.route_plan.route_for("start", "a").source_port.side == "e"
    assert routing_plan.route_plan.route_for("start", "a").target_port.side == "w"


def test_sppm_routing_plan_corridor_plan_empty_without_placement_wrap():
    edges = [{"source": "a", "target": "b"}]
    options = RenderOptions(diagram="sppm")

    routing_plan = build_sppm_routing_plan(
        nodes=[],
        edges=edges,
        options=options,
        step_numbering={"a": 1, "b": 2},
        wrap_plan=build_wrap_plan([], options, planner="chunked"),
    )

    assert routing_plan.corridor_plan.lanes == ()
    assert routing_plan.corridor_plan.edge_lane_hops == {}
    assert routing_plan.route_plan.routes == {}


def test_sppm_task_nodes_emit_named_slot_ports_when_route_plan_has_slots():
    ir_like = {
        "nodes": [
            {"id": "a", "kind": "task", "name": "A", "metadata": {}},
            {"id": "b", "kind": "task", "name": "B", "metadata": {}},
            {"id": "c", "kind": "task", "name": "C", "metadata": {}},
        ],
        "edges": [
            {"source": "a", "target": "c"},
            {"source": "b", "target": "c"},
        ],
    }

    out = render_dot(ir_like, options={"diagram": "sppm"})
    assert 'PORT="in_0"' in out
    assert 'PORT="in_1"' in out
    assert 'PORT="out_0"' in out
    assert "headport=w" in out