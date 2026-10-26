"""Routed geometry is inspectable before SVG and authoritative for its consumers."""

import xml.etree.ElementTree as ET
from dataclasses import FrozenInstanceError, asdict, replace
from unittest.mock import Mock

import pytest

from flo.render import RenderOptions, render_execution
from flo.render.layout_core.models import (
    LayoutBounds,
    LayoutPoint,
    LayoutResult,
    RoutedEdgePath,
)
from flo.render.sppm import renderer
from flo.render.sppm.geometry import finalize_sppm_geometry
from flo.render.sppm.layout import build_sppm_elk_layout_request
from flo.render.sppm.scene import finalize_sppm_scene
from flo.render.sppm.svg import emit_sppm_svg_artifact


def _layout():
    return LayoutResult(
        orientation="lr",
        canvas_bounds=LayoutBounds(0, 0, 400, 200),
        node_bounds={
            "a": LayoutBounds(0, 0, 100, 80),
            "b": LayoutBounds(250, 0, 100, 80),
        },
        edge_paths={
            ("a", "b"): RoutedEdgePath(
                edge=("a", "b"),
                points=(LayoutPoint(100, 40), LayoutPoint(250, 40)),
            )
        },
    )


def _process():
    return {
        "nodes": [{"id": "a", "kind": "task"}, {"id": "b", "kind": "task"}],
        "edges": [{"source": "a", "target": "b"}],
    }


def test_finalization_is_repeatable_and_does_not_modify_engine_geometry():
    layout = _layout()
    before = asdict(layout)
    first = finalize_sppm_geometry(layout)
    assert first == finalize_sppm_geometry(layout)
    assert asdict(layout) == before
    assert first.node_groups == {
        "mainline": frozenset({"a", "b"}),
        "correction": frozenset(),
    }
    assert first.edge_groups == {"correction": frozenset()}
    layout.node_bounds.clear()
    assert set(first.node_bounds) == {"a", "b"}
    with pytest.raises(TypeError):
        first.node_bounds["a"] = LayoutBounds(100, 0, 100, 80)
    with pytest.raises(TypeError):
        first.edge_groups["correction"] = frozenset({("a", "b")})
    with pytest.raises(FrozenInstanceError):
        first.canvas_bounds = LayoutBounds(0, 0, 1, 1)


def test_svg_consumes_supplied_positions_routes_canvas_and_correction_membership(
    monkeypatch,
):
    process = _process()
    options = RenderOptions(diagram="sppm")
    request = build_sppm_elk_layout_request(process, options)
    initial = finalize_sppm_geometry(_layout())
    supplied = replace(
        initial,
        node_bounds={
            key: replace(box, x_px=box.x_px + 100)
            for key, box in initial.node_bounds.items()
        },
        edge_paths={
            ("a", "b"): RoutedEdgePath(
                edge=("a", "b"),
                points=(
                    LayoutPoint(200, 40),
                    LayoutPoint(225, 40),
                    LayoutPoint(225, 140),
                    LayoutPoint(300, 140),
                    LayoutPoint(300, 40),
                    LayoutPoint(350, 40),
                ),
            )
        },
        canvas_bounds=LayoutBounds(0, 0, 700, 300),
        edge_groups={"correction": frozenset({("a", "b")})},
    )
    monkeypatch.setattr(
        renderer,
        "finalize_sppm_geometry",
        Mock(side_effect=AssertionError("emitter re-entered layout")),
    )
    scene = finalize_sppm_scene(
        process=process, options=options, request=request, geometry=supplied
    )
    artifact, _ = emit_sppm_svg_artifact(
        process=process, options=options, request=request, scene=scene
    )
    root = ET.fromstring(artifact.content)  # noqa: S314 - Renderer-produced SVG.
    assert root.attrib["viewBox"] == "0 0 756 356"
    ns = {"s": "http://www.w3.org/2000/svg"}
    for name, x in (("a", 100), ("b", 350)):
        rect = root.find(f'.//s:g[@data-node-id="{name}"]/s:rect', ns)
        assert float(rect.attrib["x"]) == x
    line = root.find('.//s:g[@data-edge-source="a"]/s:polyline', ns)
    points = tuple(
        tuple(map(float, point.split(","))) for point in line.attrib["points"].split()
    )
    assert points == tuple(
        (point.x_px, point.y_px) for point in supplied.edge_paths[("a", "b")].points
    )
    assert "stroke-dasharray" in line.attrib


def test_execution_captures_geometry_before_svg_emission(monkeypatch):
    order = []
    finalize = renderer.finalize_sppm_geometry
    emit = renderer.emit_sppm_svg_artifact

    def finalized(result):
        order.append("finalize")
        return finalize(result)

    def emitted(**kwargs):
        order.append("emit")
        assert kwargs["scene"].routed.diagram == "sppm"
        return emit(**kwargs)

    monkeypatch.setattr(renderer, "finalize_sppm_geometry", finalized)
    monkeypatch.setattr(renderer, "emit_sppm_svg_artifact", emitted)
    execution = render_execution(_process(), {"diagram": "sppm"}, capture_layout=True)
    assert order == ["finalize", "emit"]
    assert len(execution.layout_stages) == len(execution.geometry_stages) == 1
    assert execution.geometry_stages[0].node_bounds


def test_visible_lanes_canvas_and_correction_connectors_are_finalized_together():
    from flo.render.layout_core.models import LayoutLaneFrame

    layout = _layout()
    visible = LayoutLaneFrame(
        "owner", "Owner", LayoutBounds(0, 0, 400, 100), ("a", "b")
    )
    hidden = LayoutLaneFrame(
        "__sppm_row_wrap_rework_0", "", LayoutBounds(0, 150, 400, 100), ("c", "d")
    )
    nodes = {
        **layout.node_bounds,
        "c": LayoutBounds(0, 160, 100, 80),
        "d": LayoutBounds(250, 160, 100, 80),
    }
    paths = dict(layout.edge_paths)
    for a, b, variant in (("a", "c", "branch"), ("c", "d", None), ("d", "b", "return")):
        paths[(a, b)] = RoutedEdgePath(
            edge=(a, b),
            points=(LayoutPoint(50, 80), LayoutPoint(50, 160)),
            is_rework=variant is not None,
            rework_variant=variant,
        )
    geometry = finalize_sppm_geometry(
        replace(layout, node_bounds=nodes, edge_paths=paths, lanes=(visible, hidden))
    )
    assert geometry.lanes == (visible,)
    assert geometry.node_groups["mainline"] == {"a", "b"}
    assert geometry.node_groups["correction"] == {"c", "d"}
    assert geometry.edge_groups["correction"] == {("c", "d")}
    assert geometry.canvas_bounds.height_px >= 240
