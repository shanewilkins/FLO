"""Unit tests for deterministic layout-core port assignment (Phase 4)."""

from flo.render.layout_core import (
    NodeMeasure,
    PlacementConstraints,
    build_placement_plan,
    build_port_assignments,
)


def _node(nid: str, w: int = 100, h: int = 40) -> NodeMeasure:
    return NodeMeasure(id=nid, width_px=w, height_px=h, kind="task")


def test_lr_ports_use_west_for_inputs_and_east_for_outputs_with_ordered_slots():
    nodes = [_node("a"), _node("b"), _node("c"), _node("d")]
    edges = [("a", "d"), ("b", "d"), ("d", "a"), ("d", "c")]
    placement = build_placement_plan(nodes, edges, PlacementConstraints())

    source_ports, target_ports = build_port_assignments(placement=placement, edges=edges)

    assert source_ports[("d", "a")].side == "e"
    assert source_ports[("d", "c")].side == "e"
    assert source_ports[("d", "a")].slot_index == 0
    assert source_ports[("d", "c")].slot_index == 1

    assert target_ports[("a", "d")].side == "w"
    assert target_ports[("b", "d")].side == "w"
    assert target_ports[("a", "d")].slot_index == 0
    assert target_ports[("b", "d")].slot_index == 1


def test_tb_ports_use_north_for_inputs_and_south_for_outputs():
    nodes = [_node("a"), _node("b"), _node("c")]
    edges = [("a", "c"), ("b", "c")]
    placement = build_placement_plan(nodes, edges, PlacementConstraints(orientation="tb"))

    source_ports, target_ports = build_port_assignments(placement=placement, edges=edges)

    assert source_ports[("a", "c")].side == "s"
    assert source_ports[("b", "c")].side == "s"
    assert target_ports[("a", "c")].side == "n"
    assert target_ports[("b", "c")].side == "n"


def test_port_assignment_is_deterministic_across_calls():
    nodes = [_node("a"), _node("b"), _node("c"), _node("d")]
    edges = [("a", "d"), ("b", "d"), ("c", "d"), ("d", "a")]
    placement = build_placement_plan(nodes, edges, PlacementConstraints())

    plan1 = build_port_assignments(placement=placement, edges=edges)
    plan2 = build_port_assignments(placement=placement, edges=edges)

    assert plan1 == plan2