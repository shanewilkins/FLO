"""Final-scene consumers must never repeat attachment or annotation policy."""

import xml.etree.ElementTree as ET
from dataclasses import asdict, replace
from unittest.mock import Mock

import pytest

from flo.errors import RenderError
from flo.render import RenderOptions, render_execution
from flo.render._diagnostics import RenderDiagnostic
from flo.render.layout_core.models import (
    LayoutBounds,
    LayoutPoint,
    LayoutResult,
    RoutedEdgePath,
)
from flo.render.sppm import attachments, edge_geometry, edge_layout, renderer
from flo.render.sppm.geometry import finalize_sppm_geometry
from flo.render.sppm.layout import build_sppm_elk_layout_request
from flo.render.sppm.scene import finalize_sppm_scene
from flo.render.sppm.svg import emit_sppm_svg_artifact


def _prepared():
    process = {
        "nodes": [{"id": "a", "kind": "decision"}, {"id": "b", "kind": "task"}],
        "edges": [{"source": "a", "target": "b"}],
    }
    options = RenderOptions(diagram="sppm")
    request = build_sppm_elk_layout_request(process, options)
    layout = LayoutResult(
        "lr",
        LayoutBounds(0, 0, 800, 400),
        {"a": LayoutBounds(0, 120, 100, 80), "b": LayoutBounds(600, 120, 100, 80)},
        {
            ("a", "b"): RoutedEdgePath(
                ("a", "b"),
                (LayoutPoint(90, 160), LayoutPoint(610, 160)),
                label="yes",
                callout_lines=("CT=3m",),
                outgoing_token="WIP",
                incoming_token="DONE",
            )
        },
    )
    geometry = finalize_sppm_geometry(layout)
    scene = finalize_sppm_scene(
        process=process, options=options, request=request, geometry=geometry
    )
    return process, options, request, geometry, scene


def test_scene_resolves_attachments_all_annotation_kinds_and_occupied_bounds():
    process, options, request, routed, scene = _prepared()
    edge = scene.edges[0]
    assert edge.points[0] == LayoutPoint(100, 160)
    assert edge.points[-1] == LayoutPoint(600, 160)
    assert [a.kind for a in edge.annotations] == ["label", "callout", "token", "token"]
    assert scene.occupied_bounds == tuple(a.bounds for a in edge.annotations)
    assert scene == finalize_sppm_scene(
        process=process, options=options, request=request, geometry=routed
    )
    assert routed.edge_paths[("a", "b")].points[0] == LayoutPoint(90, 160)


def test_emitter_consumes_supplied_scene_even_when_policy_is_disabled(monkeypatch):
    process, options, request, _routed, scene = _prepared()
    annotation = scene.edges[0].annotations[0]
    moved = replace(
        annotation,
        bounds=LayoutBounds(200, 50, 150, 18),
        texts=(replace(annotation.texts[0], x=275, y=63),),
    )
    edge = replace(
        scene.edges[0],
        points=(LayoutPoint(111, 165), LayoutPoint(589, 165)),
        annotations=(moved, *scene.edges[0].annotations[1:]),
    )
    supplied = replace(scene, edges=(edge,))
    for module, name in (
        (edge_geometry, "prepare_edge"),
        (attachments, "_clip_edge_points_to_node_bounds"),
        (edge_layout, "_avoid_bounds_overlap"),
        (renderer, "finalize_sppm_scene"),
    ):
        monkeypatch.setattr(
            module, name, Mock(side_effect=AssertionError("policy ran during emission"))
        )
    before = asdict(edge)
    artifact, _ = emit_sppm_svg_artifact(
        process=process, options=options, request=request, scene=supplied
    )
    root = ET.fromstring(artifact.content)
    ns = {"s": "http://www.w3.org/2000/svg"}
    line = root.find('.//s:g[@data-edge-source="a"]/s:polyline', ns)
    assert line.attrib["points"] == "111.0,165.0 589.0,165.0"
    text = root.find('.//s:g[@data-edge-source="a"]/s:text', ns)
    assert (text.attrib["x"], text.attrib["y"]) == ("275.0", "63.0")
    assert asdict(edge) == before


def test_strict_scene_diagnostics_fail_before_emission():
    process, options, request, routed, _ = _prepared()
    warning = RenderDiagnostic("sppm-annotation-overlap-fallback", "warning", "blocked")
    with pytest.raises(RenderError, match="Strict SPPM post-process"):
        finalize_sppm_scene(
            process=process,
            options=replace(options, layout_fit="fit-strict"),
            request=request,
            geometry=replace(routed, diagnostics=(warning,)),
        )


def test_public_execution_exposes_final_scene_and_viewport_metadata():
    process, _, _, _, _ = _prepared()
    execution = render_execution(
        process, {"diagram": "sppm", "layout_width": "800px"}, capture_layout=True
    )
    assert len(execution.scene_stages) == 1
    scene = execution.scene_stages[0]
    assert scene.width > 0 and scene.height > 0
    assert execution.artifact.metadata["geometry"]["requested_width_px"] == 800
