from types import SimpleNamespace

from flo.render._svg_shared_primitives import standard_edge_svg, standard_node_svg
from flo.render._svg_sppm_edges import _label_placement
from flo.render.layout_core.models import LayoutBounds
from flo.render.options import RenderOptions


def _p(x: float, y: float) -> SimpleNamespace:
    return SimpleNamespace(x_px=x, y_px=y)


def test_node_svg_renders_decision_and_endpoint_shapes():
    decision = standard_node_svg(
        node=SimpleNamespace(id="d", kind="decision", label="Decide"),
        raw_node={},
        options=RenderOptions(diagram="swimlane"),
        x=0,
        y=0,
        width=100,
        height=60,
    )
    assert any("<polygon" in line for line in decision)

    endpoint = standard_node_svg(
        node=SimpleNamespace(id="e", kind="end", label="Done"),
        raw_node={},
        options=RenderOptions(diagram="swimlane"),
        x=0,
        y=0,
        width=100,
        height=60,
    )
    assert any("<rect" in line for line in endpoint)


def test_edge_svg_without_label_emits_polyline_only():
    edge = SimpleNamespace(
        edge=("a", "b"),
        points=(_p(0, 0), _p(10, 10)),
        label=None,
        label_point=None,
        source_port_side=None,
        target_port_side=None,
        is_rework=False,
        rework_variant=None,
        callout_lines=(),
        callout_near_source=False,
        outgoing_token=None,
        incoming_token=None,
    )

    lines, _bounds = standard_edge_svg(
        edge_path=edge,
        source_bounds=None,
        target_bounds=None,
        source_kind="task",
        target_kind="task",
        avoid_bounds=(),
        canvas_bounds=LayoutBounds(x_px=0.0, y_px=0.0, width_px=10.0, height_px=10.0),
        diagnostics=[],
    )

    assert any("<polyline" in line for line in lines)
    assert not any("<rect" in line for line in lines)


def test_label_placement_prefers_side_anchor_for_vertical_segment():
    points = (_p(0, 0), _p(0, 20), _p(0, 40))

    placement = _label_placement(points)

    assert placement.anchor in {"start", "end"}
