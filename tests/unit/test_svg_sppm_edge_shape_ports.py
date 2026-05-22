from flo.render._svg_sppm_edges import _shape_edge_point
from flo.render.layout_core.models import LayoutBounds, LayoutPoint


def test_start_end_ports_snap_to_side_midpoints_not_rounded_corners():
    bounds = LayoutBounds(x_px=100.0, y_px=50.0, width_px=120.0, height_px=60.0)

    top = _shape_edge_point(
        bounds=bounds,
        kind="start",
        toward=LayoutPoint(x_px=156.0, y_px=0.0),
    )
    left = _shape_edge_point(
        bounds=bounds,
        kind="end",
        toward=LayoutPoint(x_px=0.0, y_px=90.0),
    )

    assert top.x_px == 160.0
    assert top.y_px == 50.0
    assert left.x_px == 100.0
    assert left.y_px == 80.0


def test_decision_ports_snap_to_diamond_points():
    bounds = LayoutBounds(x_px=200.0, y_px=120.0, width_px=100.0, height_px=80.0)

    top = _shape_edge_point(
        bounds=bounds,
        kind="decision",
        toward=LayoutPoint(x_px=270.0, y_px=0.0),
    )
    right = _shape_edge_point(
        bounds=bounds,
        kind="decision",
        toward=LayoutPoint(x_px=500.0, y_px=172.0),
    )

    assert top.x_px == 250.0
    assert top.y_px == 120.0
    assert right.x_px == 300.0
    assert right.y_px == 160.0


def test_queue_ports_snap_to_straight_cardinal_exits():
    bounds = LayoutBounds(x_px=320.0, y_px=100.0, width_px=120.0, height_px=120.0)

    right = _shape_edge_point(
        bounds=bounds,
        kind="queue",
        toward=LayoutPoint(x_px=700.0, y_px=150.0),
    )
    top = _shape_edge_point(
        bounds=bounds,
        kind="queue",
        toward=LayoutPoint(x_px=380.0, y_px=10.0),
    )

    assert right.y_px == 160.0
    assert right.x_px > 380.0
    assert top.x_px == 380.0
    assert top.y_px == 100.0


def test_task_box_ports_exit_from_true_side_midpoint():
    bounds = LayoutBounds(x_px=40.0, y_px=30.0, width_px=160.0, height_px=80.0)

    right = _shape_edge_point(
        bounds=bounds,
        kind="task",
        toward=LayoutPoint(x_px=400.0, y_px=92.0),
    )

    assert right.x_px == 200.0
    assert right.y_px == 70.0
