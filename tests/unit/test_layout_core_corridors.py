"""Unit tests for layout core corridor planning (Phase 3)."""

from flo.render.layout_core import (
    NodeMeasure,
    PlacementConstraints,
    build_corridor_plan,
    build_placement_plan,
)


def _node(nid: str, w: int = 100, h: int = 40) -> NodeMeasure:
    return NodeMeasure(id=nid, width_px=w, height_px=h, kind="task")


def test_corridor_lanes_are_deterministic_for_fixed_input():
    nodes = [_node("a"), _node("b"), _node("c"), _node("d"), _node("e")]
    constraints = PlacementConstraints(
        orientation="lr",
        max_width_px=250,
        gap_major=20,
        gap_minor=40,
        margin=10,
    )
    placement = build_placement_plan(nodes, [], constraints)

    plan1 = build_corridor_plan(placement=placement, lane_channels=2)
    plan2 = build_corridor_plan(placement=placement, lane_channels=2)

    assert plan1.lanes == plan2.lanes
    assert [lane.id for lane in plan1.lanes] == [
        "corridor_lane_0_0",
        "corridor_lane_0_1",
        "corridor_lane_1_0",
        "corridor_lane_1_1",
    ]


def test_corridor_occupancy_and_anchors_for_boundary_edges():
    nodes = [_node("a"), _node("b"), _node("c"), _node("d"), _node("e")]
    edges = [("a", "c"), ("b", "d"), ("a", "e"), ("e", "b")]
    constraints = PlacementConstraints(
        orientation="lr",
        max_width_px=250,
        gap_major=20,
        gap_minor=40,
        margin=10,
    )
    placement = build_placement_plan(nodes, edges, constraints)
    plan = build_corridor_plan(placement=placement, lane_channels=2)

    # Lane 0->1 sees four traversals; with 2 channels this deterministically
    # alternates channels by sorted edge order.
    assert plan.lane_occupancy["corridor_lane_0_0"] == (("a", "c"), ("b", "d"))
    assert plan.lane_occupancy["corridor_lane_0_1"] == (("a", "e"), ("e", "b"))

    # Lane 1->2 sees a->e and e->b.
    assert plan.lane_occupancy["corridor_lane_1_0"] == (("a", "e"),)
    assert plan.lane_occupancy["corridor_lane_1_1"] == (("e", "b"),)

    # Multi-line edges keep a deterministic hop sequence.
    assert plan.edge_lane_hops[("a", "e")] == ("corridor_lane_0_1", "corridor_lane_1_0")
    assert plan.edge_lane_hops[("e", "b")] == ("corridor_lane_1_1", "corridor_lane_0_1")

    # Anchors map each logical edge to first and last corridor hops.
    assert plan.entry_anchors[("a", "e")].lane_id == "corridor_lane_0_1"
    assert plan.exit_anchors[("a", "e")].lane_id == "corridor_lane_1_0"
    assert plan.entry_anchors[("e", "b")].line_index == 2
    assert plan.exit_anchors[("e", "b")].line_index == 0
