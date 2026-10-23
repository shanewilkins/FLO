"""Neutral engine behavior depends on supplied data, never diagram tags or toggles."""

from dataclasses import replace
from unittest.mock import Mock

from flo.render.layout_core.elk import (
    execute_elk_layout,
    normalize_elk_layout_result,
    serialize_elk_layout_request,
)
from flo.render.layout_core.elk_contracts import (
    ElkLayoutNode,
    ElkLayoutRequest,
    ElkSerialization,
)
from flo.render.layout_core.models import LayoutBounds
from flo.render.sppm.layout import build_sppm_elk_layout_request
from flo.render.swimlane.layout import build_swimlane_elk_layout_request


def _request(diagram="example"):
    return ElkLayoutRequest(
        diagram=diagram,
        direction="RIGHT",
        lanes=(),
        edges=(),
        nodes=(ElkLayoutNode("task", "Task", "task", 140, 52),),
    )


def _response():
    return {
        "id": "root",
        "width": 200,
        "height": 100,
        "children": [
            {"id": "task", "x": 10, "y": 20, "width": 140, "height": 52},
        ],
    }


def test_neutral_engine_does_not_dispatch_on_diagram_names_or_strategy_environment(
    monkeypatch,
):
    request = _request()
    expected_payload = serialize_elk_layout_request(request)
    expected_result = normalize_elk_layout_result(_response(), request=request)
    for name, value in (
        ("FLO_SPPM_HELPER_ANCHORS", "always"),
        ("FLO_SPPM_SPACING_PROFILE", "roomy"),
        ("FLO_SPPM_PARTITION_MODE", "chain_progressive"),
        ("FLO_SPPM_PORT_CONSTRAINTS", "fixed_side"),
    ):
        monkeypatch.setenv(name, value)
    for diagram in ("sppm", "swimlane", "another_diagram"):
        other = replace(request, diagram=diagram)
        payload = serialize_elk_layout_request(other)
        assert {**payload, "id": expected_payload["id"]} == expected_payload
        assert (
            normalize_elk_layout_result(_response(), request=other) == expected_result
        )


def test_core_runs_only_the_explicit_transform_and_observes_its_result():
    transformed = LayoutBounds(0, 0, 777, 999)
    transform = Mock(
        side_effect=lambda request, result: replace(result, canvas_bounds=transformed)
    )
    request = replace(_request(), result_transform=transform)
    observer = Mock()
    result = execute_elk_layout(
        request, engine=lambda payload: _response(), observer=observer
    )
    assert transform.call_count == 1
    assert transform.call_args.args[0] is request
    assert result.canvas_bounds == transformed
    assert observer.call_args.args[0].result == result


def test_serialized_settings_are_detached_from_the_request():
    settings = ElkSerialization(
        root_options={"elk.direction": "DOWN"},
        node_overrides={"task": {"ports": [{"id": "task.p"}]}},
        auxiliary_nodes=({"id": "helper", "width": 1},),
    )
    request = replace(_request(), serialization=settings)
    payload = serialize_elk_layout_request(request)
    payload["layoutOptions"].clear()
    payload["children"][0]["ports"].clear()
    payload["children"][1]["width"] = 100
    assert settings.root_options == {"elk.direction": "DOWN"}
    assert settings.node_overrides["task"]["ports"] == [{"id": "task.p"}]
    assert settings.auxiliary_nodes[0]["width"] == 1


def test_diagram_builders_supply_independent_policy(monkeypatch):
    process = {"nodes": [{"id": "task", "kind": "task"}], "edges": []}
    swimlane = build_swimlane_elk_layout_request(process)
    before = serialize_elk_layout_request(swimlane)
    monkeypatch.setenv("FLO_SPPM_SPACING_PROFILE", "roomy")
    sppm = build_sppm_elk_layout_request(process)
    assert sppm.result_transform.__module__ == "flo.render.sppm.layout_spacing"
    assert sppm.serialization.root_options["elk.spacing.nodeNode"] == "200"
    assert swimlane.result_transform is None
    assert (
        serialize_elk_layout_request(build_swimlane_elk_layout_request(process))
        == before
    )


def test_auxiliary_edges_are_excluded_by_supplied_identity_not_reserved_prefix():
    request = replace(
        _request(),
        serialization=ElkSerialization(
            auxiliary_edges=({"id": "auxiliary.route"},),
        ),
    )
    response = _response()
    response["edges"] = [{"id": "auxiliary.route"}]
    result = normalize_elk_layout_result(response, request=request)
    assert not result.diagnostics
    response["edges"] = [
        {
            "id": "__sppm_helper_forged",
            "sources": ["task"],
            "targets": ["task"],
            "sections": [
                {"startPoint": {"x": 10, "y": 20}, "endPoint": {"x": 30, "y": 20}}
            ],
        }
    ]
    result = normalize_elk_layout_result(response, request=request)
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "elk-edge-unexpected"
    ]
