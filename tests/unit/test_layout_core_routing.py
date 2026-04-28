"""Unit tests for deterministic layout-core route planning (Phase 4)."""

from flo.render.layout_core import (
    NodeMeasure,
    PlacementConstraints,
    build_corridor_plan,
    build_placement_plan,
    build_route_plan,
    serialize_route_plan,
)


def _node(nid: str, w: int = 100, h: int = 40) -> NodeMeasure:
    return NodeMeasure(id=nid, width_px=w, height_px=h, kind="task")


def test_route_plan_assigns_side_slots_and_lane_hops():
    nodes = [_node("a"), _node("b"), _node("c"), _node("d"), _node("e")]
    edges = [("a", "c"), ("b", "d"), ("a", "e"), ("e", "b")]
    constraints = PlacementConstraints(max_width_px=250, gap_major=20, gap_minor=40, margin=10)
    placement = build_placement_plan(nodes, edges, constraints)
    corridor = build_corridor_plan(placement=placement, lane_channels=2, edges=edges)

    plan = build_route_plan(placement=placement, corridor=corridor, edges=edges)

    assert plan.route_for("a", "e").lane_hops == ("corridor_lane_0_1", "corridor_lane_1_0")
    assert plan.route_for("a", "e").source_port.side == "e"
    assert plan.route_for("a", "e").target_port.side == "w"
    assert plan.route_for("a", "e").source_port.slot_index == 1
    assert plan.route_for("e", "b").target_port.slot_index == 0


def test_route_plan_reports_shared_lane_conflicts_deterministically():
    nodes = [_node("a"), _node("b"), _node("c"), _node("d"), _node("e")]
    edges = [("a", "c"), ("b", "d"), ("a", "e"), ("e", "b")]
    constraints = PlacementConstraints(max_width_px=250, gap_major=20, gap_minor=40, margin=10)
    placement = build_placement_plan(nodes, edges, constraints)
    corridor = build_corridor_plan(placement=placement, lane_channels=2, edges=edges)

    plan = build_route_plan(placement=placement, corridor=corridor, edges=edges)

    assert plan.conflicts == (
        # Both conflicts are reported in lane-id order.
        plan.conflicts[0],
        plan.conflicts[1],
    )
    assert plan.conflicts[0].lane_id == "corridor_lane_0_0"
    assert plan.conflicts[0].policy == "share-lane-stacked"
    assert plan.conflicts[0].edges == (("a", "c"), ("b", "d"))
    assert plan.conflicts[1].lane_id == "corridor_lane_0_1"
    assert plan.conflicts[1].edges == (("a", "e"), ("e", "b"))


def test_route_plan_snapshot_is_stable():
    nodes = [_node("a"), _node("b"), _node("c"), _node("d"), _node("e")]
    edges = [("a", "c"), ("b", "d"), ("a", "e"), ("e", "b")]
    constraints = PlacementConstraints(max_width_px=250, gap_major=20, gap_minor=40, margin=10)
    placement = build_placement_plan(nodes, edges, constraints)
    corridor = build_corridor_plan(placement=placement, lane_channels=2, edges=edges)

    snapshot = serialize_route_plan(build_route_plan(placement=placement, corridor=corridor, edges=edges))
    expected = "\n".join(
        [
            "edge a->c boundary=True",
            "  source a:e[0]",
            "  lanes corridor_lane_0_0",
            "  target c:w[0]",
            "edge a->e boundary=True",
            "  source a:e[1]",
            "  lanes corridor_lane_0_1, corridor_lane_1_0",
            "  target e:w[0]",
            "edge b->d boundary=True",
            "  source b:e[0]",
            "  lanes corridor_lane_0_0",
            "  target d:w[0]",
            "edge e->b boundary=True",
            "  source e:e[0]",
            "  lanes corridor_lane_1_1, corridor_lane_0_1",
            "  target b:w[0]",
            "conflict corridor_lane_0_0 policy=share-lane-stacked edges=a->c, b->d",
            "conflict corridor_lane_0_1 policy=share-lane-stacked edges=a->e, e->b",
        ]
    )
    assert snapshot == expected