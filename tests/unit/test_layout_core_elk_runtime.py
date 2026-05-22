from flo.render.layout_core import (
    build_flowchart_elk_layout_request,
    build_sppm_elk_layout_request,
    build_swimlane_elk_layout_request,
    execute_elk_layout,
    layout_sppm_with_elk,
    layout_swimlane_with_elk,
    normalize_elk_layout_result,
    serialize_elk_layout_request,
    serialize_layout_result,
)
from flo.render.options import RenderOptions


def test_normalize_elk_layout_result_preserves_rework_edge_semantics():
    request = build_sppm_elk_layout_request(
        {
            "nodes": [
                {"id": "decision", "kind": "decision", "name": "Approved?"},
                {"id": "rework", "kind": "task", "name": "Rework"},
            ],
            "edges": [
                {
                    "source": "decision",
                    "target": "rework",
                    "outcome": "no",
                    "edge_type": "rework",
                    "rework": True,
                }
            ],
        },
        options=RenderOptions(diagram="sppm", orientation="lr"),
    )

    result = normalize_elk_layout_result(
        {
            "id": "root",
            "width": 320,
            "height": 180,
            "children": [
                {"id": "decision", "x": 20, "y": 40, "width": 120, "height": 52},
                {"id": "rework", "x": 200, "y": 40, "width": 140, "height": 52},
            ],
            "edges": [
                {
                    "id": "e0:decision->rework",
                    "sources": ["decision"],
                    "targets": ["rework"],
                    "sections": [
                        {
                            "startPoint": {"x": 140, "y": 66},
                            "bendPoints": [{"x": 170, "y": 66}],
                            "endPoint": {"x": 200, "y": 66},
                        }
                    ],
                }
            ],
        },
        request=request,
    )

    edge_path = result.path_for("decision", "rework")

    assert edge_path is not None
    assert edge_path.is_rework is True
    assert edge_path.rework_variant == "branch"


def test_build_sppm_elk_layout_request_distinguishes_rework_return_edges():
    request = build_sppm_elk_layout_request(
        {
            "nodes": [
                {"id": "decision", "kind": "decision", "name": "Approved?"},
                {"id": "rework", "kind": "task", "name": "Rework"},
                {"id": "done", "kind": "task", "name": "Done"},
            ],
            "edges": [
                {
                    "source": "decision",
                    "target": "rework",
                    "outcome": "no",
                    "edge_type": "rework",
                    "rework": True,
                },
                {
                    "source": "rework",
                    "target": "done",
                    "edge_type": "rework",
                    "rework": True,
                },
            ],
        },
        options=RenderOptions(diagram="sppm", orientation="lr"),
    )

    branch_edge = request.edges[0]
    return_edge = request.edges[1]

    assert branch_edge.rework_variant == "branch"
    assert return_edge.rework_variant == "return"


def test_serialize_elk_layout_request_builds_swimlane_payload_shape():
    request = build_swimlane_elk_layout_request(
        {
            "lanes": [
                {"id": "sales", "name": "Sales"},
                {"id": "ops", "name": "Operations"},
            ],
            "nodes": [
                {"id": "start", "kind": "start", "name": "Start", "lane": "sales"},
                {"id": "review", "kind": "task", "name": "Review", "lane": "ops"},
                {"id": "finish", "kind": "end", "name": "Finish"},
            ],
            "edges": [
                {"source": "start", "target": "review", "outcome": "handoff"},
                {"source": "review", "target": "finish"},
            ],
        },
        options=RenderOptions(diagram="swimlane", orientation="tb"),
    )

    payload = serialize_elk_layout_request(request)

    assert payload["id"] == "flo:swimlane"
    assert payload["layoutOptions"]["elk.algorithm"] == "layered"
    assert payload["layoutOptions"]["elk.direction"] == "DOWN"
    assert payload["layoutOptions"]["elk.hierarchyHandling"] == "INCLUDE_CHILDREN"
    assert [child["id"] for child in payload["children"]] == [
        "sales",
        "ops",
        "unassigned",
    ]
    assert payload["children"][0]["labels"][0]["text"] == "Sales"
    assert [child["id"] for child in payload["children"][0]["children"]] == ["start"]
    assert [child["id"] for child in payload["children"][1]["children"]] == ["review"]
    assert payload["children"][2]["labels"][0]["text"] == "unassigned"
    assert [child["id"] for child in payload["children"][2]["children"]] == ["finish"]
    assert payload["edges"][0]["labels"][0]["text"] == "handoff"
    assert payload["edges"][1]["targets"] == ["finish"]


def test_execute_elk_layout_round_trips_through_injected_engine():
    request = build_flowchart_elk_layout_request(
        {
            "nodes": [
                {"id": "start", "kind": "start", "name": "Start"},
                {"id": "finish", "kind": "end", "name": "Finish"},
            ],
            "edges": [{"source": "start", "target": "finish", "outcome": "done"}],
        },
        options=RenderOptions(diagram="flowchart", orientation="lr"),
    )

    captured: dict[str, object] = {}

    def fake_engine(payload: dict[str, object]) -> dict[str, object]:
        captured["payload"] = payload
        return {
            "id": payload["id"],
            "width": 360,
            "height": 160,
            "children": [
                {"id": "start", "x": 20, "y": 54, "width": 120, "height": 52},
                {"id": "finish", "x": 220, "y": 54, "width": 120, "height": 52},
            ],
            "edges": [
                {
                    "id": "e0:start->finish",
                    "sources": ["start"],
                    "targets": ["finish"],
                    "sections": [
                        {
                            "startPoint": {"x": 140, "y": 80},
                            "bendPoints": [{"x": 180, "y": 80}],
                            "endPoint": {"x": 220, "y": 80},
                        }
                    ],
                }
            ],
        }

    result = execute_elk_layout(request, engine=fake_engine)

    payload = captured.get("payload")
    assert isinstance(payload, dict)
    assert payload["id"] == "flo:flowchart"
    assert payload["layoutOptions"]["elk.direction"] == "RIGHT"
    assert [child["id"] for child in payload["children"]] == ["start", "finish"]
    assert payload["edges"][0]["labels"][0]["text"] == "done"
    assert serialize_layout_result(result) == "\n".join(
        [
            "canvas x=0 y=0 w=360 h=160",
            "orientation lr",
            "node finish x=220 y=54 w=120 h=52",
            "node start x=20 y=54 w=120 h=52",
            "edge start->finish label=done points=(140,80) -> (180,80) -> (220,80)",
        ]
    )


def test_layout_swimlane_with_elk_runs_full_adapter_slice():
    process = {
        "lanes": [
            {"id": "sales", "name": "Sales"},
            {"id": "ops", "name": "Operations"},
        ],
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start", "lane": "sales"},
            {"id": "review", "kind": "task", "name": "Review", "lane": "ops"},
        ],
        "edges": [{"source": "start", "target": "review", "outcome": "handoff"}],
    }
    captured: dict[str, object] = {}

    def fake_engine(payload: dict[str, object]) -> dict[str, object]:
        captured["payload"] = payload
        return {
            "id": payload["id"],
            "width": 320,
            "height": 280,
            "children": [
                {
                    "id": "sales",
                    "x": 20,
                    "y": 20,
                    "width": 280,
                    "height": 100,
                    "children": [
                        {"id": "start", "x": 16, "y": 24, "width": 120, "height": 52}
                    ],
                },
                {
                    "id": "ops",
                    "x": 20,
                    "y": 150,
                    "width": 280,
                    "height": 100,
                    "children": [
                        {"id": "review", "x": 16, "y": 24, "width": 140, "height": 52}
                    ],
                },
            ],
            "edges": [
                {
                    "sources": ["start"],
                    "targets": ["review"],
                    "labels": [{"text": "handoff"}],
                    "sections": [
                        {
                            "startPoint": {"x": 156, "y": 70},
                            "bendPoints": [{"x": 156, "y": 176}],
                            "endPoint": {"x": 176, "y": 176},
                        }
                    ],
                }
            ],
        }

    result = layout_swimlane_with_elk(
        process,
        engine=fake_engine,
        options=RenderOptions(diagram="swimlane", orientation="tb"),
    )

    payload = captured.get("payload")
    assert isinstance(payload, dict)
    assert payload["id"] == "flo:swimlane"
    assert payload["layoutOptions"]["elk.direction"] == "DOWN"
    assert [child["id"] for child in payload["children"]] == ["sales", "ops"]
    assert [lane.id for lane in result.lanes] == ["sales", "ops"]
    edge_path = result.path_for("start", "review")
    assert edge_path is not None
    assert edge_path.label == "handoff"


def test_layout_swimlane_with_elk_rejects_non_swimlane_options():
    try:
        layout_swimlane_with_elk(
            {"nodes": [], "edges": []},
            engine=lambda payload: payload,
            options=RenderOptions(diagram="flowchart"),
        )
    except ValueError as exc:
        assert str(exc) == "Swimlane ELK adapter requires diagram='swimlane'."
    else:
        raise AssertionError("Expected swimlane adapter to reject non-swimlane options")


def test_layout_sppm_with_elk_runs_full_adapter_slice_without_lane_groups():
    process = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "queue", "kind": "queue", "name": "Wait Queue"},
        ],
        "edges": [{"source": "start", "target": "queue", "outcome": "next"}],
    }
    captured: dict[str, object] = {}

    def fake_engine(payload: dict[str, object]) -> dict[str, object]:
        captured["payload"] = payload
        return {
            "id": payload["id"],
            "width": 320,
            "height": 160,
            "children": [
                {"id": "start", "x": 20, "y": 54, "width": 120, "height": 52},
                {"id": "queue", "x": 180, "y": 54, "width": 120, "height": 52},
            ],
            "edges": [
                {
                    "sources": ["start"],
                    "targets": ["queue"],
                    "labels": [{"text": "next"}],
                    "sections": [
                        {
                            "startPoint": {"x": 140, "y": 80},
                            "bendPoints": [{"x": 160, "y": 80}],
                            "endPoint": {"x": 180, "y": 80},
                        }
                    ],
                }
            ],
        }

    result = layout_sppm_with_elk(
        process,
        engine=fake_engine,
        options=RenderOptions(diagram="sppm", orientation="lr"),
    )

    payload = captured.get("payload")
    assert isinstance(payload, dict)
    assert payload["id"] == "flo:sppm"
    assert payload["layoutOptions"]["elk.direction"] == "RIGHT"
    assert [child["id"] for child in payload["children"]] == ["start", "queue"]
    assert result.lanes == ()
    edge_path = result.path_for("start", "queue")
    assert edge_path is not None
    assert edge_path.label == "next"


def test_layout_sppm_with_elk_rejects_non_sppm_options():
    try:
        layout_sppm_with_elk(
            {"nodes": [], "edges": []},
            engine=lambda payload: payload,
            options=RenderOptions(diagram="flowchart"),
        )
    except ValueError as exc:
        assert str(exc) == "SPPM ELK adapter requires diagram='sppm'."
    else:
        raise AssertionError("Expected SPPM adapter to reject non-SPPM options")


def test_layout_swimlane_with_elk_uses_real_runtime_when_available():
    process = {
        "lanes": [
            {"id": "sales", "name": "Sales"},
            {"id": "ops", "name": "Operations"},
        ],
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start", "lane": "sales"},
            {"id": "review", "kind": "task", "name": "Review", "lane": "ops"},
        ],
        "edges": [{"source": "start", "target": "review", "outcome": "handoff"}],
    }

    result = layout_swimlane_with_elk(
        process,
        options=RenderOptions(diagram="swimlane", orientation="tb"),
    )

    assert [lane.id for lane in result.lanes] == ["sales", "ops"]
    start_bounds = result.bounds_for("start")
    review_bounds = result.bounds_for("review")
    edge_path = result.path_for("start", "review")
    assert start_bounds is not None
    assert review_bounds is not None
    assert edge_path is not None
    assert len(edge_path.points) >= 2
    assert edge_path.label == "handoff"


def test_normalize_elk_layout_result_builds_flowchart_geometry():
    request = build_flowchart_elk_layout_request(
        {
            "nodes": [
                {"id": "start", "kind": "start", "name": "Start"},
                {"id": "finish", "kind": "end", "name": "Finish"},
            ],
            "edges": [
                {"source": "start", "target": "finish", "outcome": "done"},
            ],
        },
        options=RenderOptions(diagram="flowchart", orientation="lr"),
    )

    result = normalize_elk_layout_result(
        {
            "id": "root",
            "width": 360,
            "height": 160,
            "children": [
                {"id": "start", "x": 20, "y": 54, "width": 120, "height": 52},
                {"id": "finish", "x": 220, "y": 54, "width": 120, "height": 52},
            ],
            "edges": [
                {
                    "id": "e0:start->finish",
                    "sources": ["start"],
                    "targets": ["finish"],
                    "sections": [
                        {
                            "startPoint": {"x": 140, "y": 80},
                            "bendPoints": [{"x": 180, "y": 80}],
                            "endPoint": {"x": 220, "y": 80},
                        }
                    ],
                }
            ],
        },
        request=request,
    )

    start_bounds = result.bounds_for("start")
    finish_bounds = result.bounds_for("finish")
    edge_path = result.path_for("start", "finish")

    assert start_bounds is not None
    assert finish_bounds is not None
    assert edge_path is not None
    assert edge_path.label == "done"
    assert serialize_layout_result(result) == "\n".join(
        [
            "canvas x=0 y=0 w=360 h=160",
            "orientation lr",
            "node finish x=220 y=54 w=120 h=52",
            "node start x=20 y=54 w=120 h=52",
            "edge start->finish label=done points=(140,80) -> (180,80) -> (220,80)",
        ]
    )


def test_normalize_elk_layout_result_preserves_swimlane_frames_and_nested_offsets():
    request = build_swimlane_elk_layout_request(
        {
            "lanes": [
                {"id": "sales", "name": "Sales"},
                {"id": "ops", "name": "Operations"},
            ],
            "nodes": [
                {"id": "start", "kind": "start", "name": "Start", "lane": "sales"},
                {"id": "review", "kind": "task", "name": "Review", "lane": "ops"},
            ],
            "edges": [{"source": "start", "target": "review", "outcome": "handoff"}],
        },
        options=RenderOptions(diagram="swimlane", orientation="tb"),
    )

    result = normalize_elk_layout_result(
        {
            "id": "root",
            "width": 320,
            "height": 280,
            "children": [
                {
                    "id": "sales",
                    "x": 20,
                    "y": 20,
                    "width": 280,
                    "height": 100,
                    "children": [
                        {"id": "start", "x": 16, "y": 24, "width": 120, "height": 52}
                    ],
                },
                {
                    "id": "ops",
                    "x": 20,
                    "y": 150,
                    "width": 280,
                    "height": 100,
                    "children": [
                        {"id": "review", "x": 16, "y": 24, "width": 140, "height": 52}
                    ],
                },
            ],
            "edges": [
                {
                    "sources": ["start"],
                    "targets": ["review"],
                    "labels": [{"text": "handoff"}],
                    "sections": [
                        {
                            "startPoint": {"x": 156, "y": 70},
                            "bendPoints": [{"x": 156, "y": 176}],
                            "endPoint": {"x": 176, "y": 176},
                        }
                    ],
                }
            ],
        },
        request=request,
    )

    assert [lane.id for lane in result.lanes] == ["sales", "ops"]
    assert result.lanes[0].bounds.x_px == 20
    assert result.lanes[1].bounds.y_px == 150
    start_bounds = result.bounds_for("start")
    review_bounds = result.bounds_for("review")
    edge_path = result.path_for("start", "review")

    assert start_bounds is not None
    assert review_bounds is not None
    assert edge_path is not None
    assert start_bounds.x_px == 36
    assert review_bounds.y_px == 174
    assert edge_path.label == "handoff"
