"""Unit tests for the renderer-agnostic placement core (Phase 1)."""

from flo.render.layout_core import (
    NodeMeasure,
    PlacementConstraints,
    build_placement_plan,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _node(nid: str, w: int = 100, h: int = 40, kind: str = "task") -> NodeMeasure:
    return NodeMeasure(id=nid, width_px=w, height_px=h, kind=kind)


def _edges(*pairs: tuple[str, str]) -> list[tuple[str, str]]:
    return list(pairs)


# ---------------------------------------------------------------------------
# Empty input
# ---------------------------------------------------------------------------


def test_empty_nodes_returns_empty_plan():
    plan = build_placement_plan([], [], PlacementConstraints())
    assert plan.lines == ()
    assert plan.node_line_index == {}
    assert plan.boundary_edges == frozenset()
    assert plan.total_major == 40  # margin * 2 = 20 * 2
    assert plan.total_cross == 40
    assert plan.orientation == "lr"


# ---------------------------------------------------------------------------
# Single line (no wrap limit)
# ---------------------------------------------------------------------------


def test_single_node_lr():
    node = _node("a", w=100, h=40)
    plan = build_placement_plan([node], [], PlacementConstraints(orientation="lr"))
    assert len(plan.lines) == 1
    line = plan.lines[0]
    assert line.node_ids == ("a",)
    assert line.node_major_offsets == (20,)   # margin=20
    assert line.node_cross_offsets == (20,)
    assert line.major_size == 100
    assert line.cross_size == 40
    assert plan.total_major == 140             # margin + 100 + margin
    assert plan.total_cross == 80             # margin + 40 + margin


def test_two_nodes_same_line_lr():
    nodes = [_node("a", w=100, h=40), _node("b", w=80, h=40)]
    plan = build_placement_plan(nodes, [], PlacementConstraints(gap_major=10))
    line = plan.lines[0]
    assert line.node_ids == ("a", "b")
    # a at margin=20, b at 20+100+10=130
    assert line.node_major_offsets == (20, 130)
    assert line.major_size == 190             # 100 + 10 + 80
    assert plan.total_major == 230            # 20 + 190 + 20


def test_three_nodes_no_wrap_share_one_line():
    nodes = [_node(str(i), w=60, h=30) for i in range(3)]
    plan = build_placement_plan(
        nodes, [], PlacementConstraints(gap_major=10, max_width_px=None)
    )
    assert len(plan.lines) == 1
    assert plan.lines[0].node_ids == ("0", "1", "2")


# ---------------------------------------------------------------------------
# Row packing (LR wrap)
# ---------------------------------------------------------------------------


def test_wrap_splits_into_two_rows():
    # 3 nodes of width 100 each, gap=20; max_width=250 → A+B fit (100+20+100=220),
    # adding C (220+20+100=340) > 250 → C wraps.
    nodes = [_node("a"), _node("b"), _node("c")]
    constraints = PlacementConstraints(
        orientation="lr", max_width_px=250, gap_major=20, gap_minor=40, margin=10
    )
    plan = build_placement_plan(nodes, [], constraints)
    assert len(plan.lines) == 2
    assert plan.lines[0].node_ids == ("a", "b")
    assert plan.lines[1].node_ids == ("c",)


def test_wrap_cross_offsets_accumulate_correctly():
    nodes = [_node("a", h=50), _node("b", h=50), _node("c", h=30)]
    constraints = PlacementConstraints(
        orientation="lr", max_width_px=250, gap_major=20, gap_minor=40, margin=10
    )
    plan = build_placement_plan(nodes, [], constraints)
    line0, line1 = plan.lines[0], plan.lines[1]
    # Line 0 cross starts at margin=10, cross_size=50
    assert line0.cross_offset == 10
    assert line0.cross_size == 50
    # Line 1 cross starts at 10 + 50 + 40 = 100
    assert line1.cross_offset == 100
    assert line1.cross_size == 30
    assert plan.total_cross == 100 + 30 + 10  # last.cross_offset + last.cross_size + margin


# ---------------------------------------------------------------------------
# Column packing (TB orientation)
# ---------------------------------------------------------------------------


def test_tb_single_line_no_limit():
    nodes = [_node("x", w=60, h=40), _node("y", w=80, h=60)]
    plan = build_placement_plan(nodes, [], PlacementConstraints(orientation="tb"))
    assert len(plan.lines) == 1
    line = plan.lines[0]
    # major = height; cross = width
    assert line.major_size == 40 + 20 + 60  # default gap_major=20
    assert line.cross_size == 80            # max width


def test_tb_wrap_splits_into_columns():
    # 3 nodes of height 80 each, gap=20; max_height=200 → A+B fit (80+20+80=180),
    # adding C (180+20+80=280) > 200 → C wraps.
    nodes = [_node("a", h=80), _node("b", h=80), _node("c", h=80)]
    constraints = PlacementConstraints(
        orientation="tb", max_height_px=200, gap_major=20, gap_minor=40, margin=10
    )
    plan = build_placement_plan(nodes, [], constraints)
    assert len(plan.lines) == 2
    assert plan.lines[0].node_ids == ("a", "b")
    assert plan.lines[1].node_ids == ("c",)


# ---------------------------------------------------------------------------
# Boundary edge derivation
# ---------------------------------------------------------------------------


def test_boundary_edges_across_rows():
    nodes = [_node("a"), _node("b"), _node("c")]
    constraints = PlacementConstraints(max_width_px=250, gap_major=20, margin=10)
    edges = _edges(("a", "b"), ("b", "c"), ("a", "c"))
    plan = build_placement_plan(nodes, edges, constraints)
    # a,b on line 0; c on line 1 → b→c and a→c are boundary
    assert ("b", "c") in plan.boundary_edges
    assert ("a", "c") in plan.boundary_edges
    assert ("a", "b") not in plan.boundary_edges


def test_edges_with_unknown_nodes_are_excluded():
    nodes = [_node("a"), _node("b")]
    edges = _edges(("a", "unknown"), ("unknown", "b"))
    plan = build_placement_plan(nodes, edges, PlacementConstraints())
    assert plan.boundary_edges == frozenset()


def test_intra_line_edges_are_not_boundary():
    nodes = [_node("a"), _node("b"), _node("c")]
    edges = _edges(("a", "b"), ("b", "c"))
    plan = build_placement_plan(nodes, edges, PlacementConstraints())
    assert len(plan.boundary_edges) == 0


# ---------------------------------------------------------------------------
# node_line_index
# ---------------------------------------------------------------------------


def test_node_line_index_correct_after_wrap():
    nodes = [_node("a"), _node("b"), _node("c")]
    constraints = PlacementConstraints(max_width_px=250, gap_major=20, margin=10)
    plan = build_placement_plan(nodes, [], constraints)
    assert plan.node_line_index["a"] == 0
    assert plan.node_line_index["b"] == 0
    assert plan.node_line_index["c"] == 1


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_plan_is_deterministic_across_calls():
    nodes = [_node(f"n{i}", w=60 + i * 10, h=30 + i * 5) for i in range(6)]
    edges = [(f"n{i}", f"n{i+1}") for i in range(5)]
    constraints = PlacementConstraints(max_width_px=300, gap_major=15, gap_minor=30)
    plan1 = build_placement_plan(nodes, edges, constraints)
    plan2 = build_placement_plan(nodes, edges, constraints)
    assert plan1.lines == plan2.lines
    assert plan1.boundary_edges == plan2.boundary_edges
    assert plan1.total_major == plan2.total_major
    assert plan1.total_cross == plan2.total_cross


# ---------------------------------------------------------------------------
# align_stack modes
# ---------------------------------------------------------------------------


def test_align_stack_start_shorter_line_keeps_margin():
    nodes = [_node("a"), _node("b"), _node("c")]
    constraints = PlacementConstraints(
        max_width_px=250, gap_major=20, margin=10, align_stack="start"
    )
    plan = build_placement_plan(nodes, [], constraints)
    # Line 1 has only "c"; its first major offset should remain at margin=10.
    assert plan.lines[1].node_major_offsets[0] == 10


def test_align_stack_center_shorter_line_shifts_right():
    nodes = [_node("a"), _node("b"), _node("c")]
    # Line 0: a+b = 100+20+100=220, Line 1: c = 100
    constraints = PlacementConstraints(
        max_width_px=250, gap_major=20, margin=10, align_stack="center"
    )
    plan = build_placement_plan(nodes, [], constraints)
    # shift = (220 - 100) // 2 = 60; first offset = 10 + 60 = 70
    assert plan.lines[1].node_major_offsets[0] == 70


def test_align_stack_end_shorter_line_right_aligns():
    nodes = [_node("a"), _node("b"), _node("c")]
    constraints = PlacementConstraints(
        max_width_px=250, gap_major=20, margin=10, align_stack="end"
    )
    plan = build_placement_plan(nodes, [], constraints)
    # shift = 220 - 100 = 120; first offset = 10 + 120 = 130
    assert plan.lines[1].node_major_offsets[0] == 130


# ---------------------------------------------------------------------------
# align_line modes
# ---------------------------------------------------------------------------


def test_align_line_start_all_nodes_at_line_cross_offset():
    nodes = [_node("tall", h=80), _node("short", h=40)]
    constraints = PlacementConstraints(align_line="start", margin=10)
    plan = build_placement_plan(nodes, [], constraints)
    line = plan.lines[0]
    # line cross_offset = margin = 10; both nodes start at top
    assert line.node_cross_offsets[0] == 10  # tall: no shift
    assert line.node_cross_offsets[1] == 10  # short: no shift (start-aligned)


def test_align_line_center_shorter_node_centered():
    nodes = [_node("tall", h=80), _node("short", h=40)]
    constraints = PlacementConstraints(align_line="center", margin=10)
    plan = build_placement_plan(nodes, [], constraints)
    line = plan.lines[0]
    # cross_size = 80; short has delta=40, shift = 40//2 = 20
    assert line.node_cross_offsets[0] == 10       # tall: no shift
    assert line.node_cross_offsets[1] == 10 + 20  # short: shifted by 20


def test_align_line_end_shorter_node_bottom_aligned():
    nodes = [_node("tall", h=80), _node("short", h=40)]
    constraints = PlacementConstraints(align_line="end", margin=10)
    plan = build_placement_plan(nodes, [], constraints)
    line = plan.lines[0]
    # shift for short = 80 - 40 = 40
    assert line.node_cross_offsets[0] == 10       # tall
    assert line.node_cross_offsets[1] == 10 + 40  # short
