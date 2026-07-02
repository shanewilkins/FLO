from types import SimpleNamespace

from flo.render._svg_swimlane import _edge_svg, _label_placement, _node_svg


def _p(x: float, y: float) -> SimpleNamespace:
    return SimpleNamespace(x_px=x, y_px=y)


def test_node_svg_renders_decision_and_endpoint_shapes():
    decision = _node_svg(
        node=SimpleNamespace(id="d", kind="decision", label="Decide"),
        x=0,
        y=0,
        width=100,
        height=60,
    )
    assert any("<polygon" in line for line in decision)

    endpoint = _node_svg(
        node=SimpleNamespace(id="e", kind="end", label="Done"),
        x=0,
        y=0,
        width=100,
        height=60,
    )
    assert any("<ellipse" in line for line in endpoint)


def test_edge_svg_without_label_emits_polyline_only():
    edge = SimpleNamespace(edge=("a", "b"), points=(_p(0, 0), _p(10, 10)), label=None)

    lines = _edge_svg(edge)

    assert any("<polyline" in line for line in lines)
    assert not any("<rect" in line for line in lines)


def test_label_placement_prefers_side_anchor_for_vertical_segment():
    points = (_p(0, 0), _p(0, 20), _p(0, 40))

    placement = _label_placement(points)

    assert placement.anchor in {"start", "end"}
