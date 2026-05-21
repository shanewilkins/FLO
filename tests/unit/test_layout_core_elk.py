from pathlib import Path

from flo.adapters import parse_adapter
from flo.render.layout_core import (
    build_flowchart_elk_layout_request,
    build_swimlane_elk_layout_request,
    execute_elk_layout,
    layout_swimlane_with_elk,
    normalize_elk_layout_result,
    serialize_elk_layout_request,
    serialize_layout_result,
)
from flo.render.options import RenderOptions


def test_build_swimlane_elk_layout_request_preserves_lane_order_and_edges():
    process = {
        "lanes": [
            {"id": "sales", "name": "Sales"},
            {"id": "ops", "name": "Operations"},
        ],
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start", "lane": "sales"},
            {"id": "review", "kind": "task", "name": "Review", "lane": "ops"},
            {"id": "finish", "kind": "end", "name": "Finish", "lane": "ops"},
        ],
        "edges": [
            {"source": "start", "target": "review"},
            {"source": "review", "target": "finish", "outcome": "approved"},
        ],
    }

    request = build_swimlane_elk_layout_request(
        process,
        options=RenderOptions(diagram="swimlane", orientation="lr"),
    )

    assert request.diagram == "swimlane"
    assert request.direction == "RIGHT"
    assert [lane.id for lane in request.lanes] == ["sales", "ops"]
    assert request.lanes[0].label == "Sales"
    assert request.lanes[1].label == "Operations"
    assert request.lanes[0].node_ids == ("start",)
    assert request.lanes[1].node_ids == ("review", "finish")
    assert [node.id for node in request.nodes] == ["start", "review", "finish"]
    assert request.nodes[1].lane_id == "ops"
    assert [edge.id for edge in request.edges] == [
        "e0:start->review",
        "e1:review->finish",
    ]
    assert request.edges[1].label == "approved"


def test_build_swimlane_elk_layout_request_accepts_reference_example():
    path = Path("examples/reference/swimlane.flo")
    adapter_model = parse_adapter(
        path.read_text(encoding="utf-8"), source_path=str(path)
    )

    request = build_swimlane_elk_layout_request(
        adapter_model,
        options=RenderOptions(diagram="swimlane", orientation="tb"),
    )

    assert request.direction == "DOWN"
    assert [lane.id for lane in request.lanes] == [
        "requester",
        "manager",
        "finance",
        "procurement",
        "vendor",
    ]
    assert any(
        node.id == "manager_review" and node.lane_id == "manager"
        for node in request.nodes
    )
    assert any(
        edge.source_id == "manager_review"
        and edge.target_id == "budget_check"
        and edge.label == "approved"
        for edge in request.edges
    )
    assert any(
        edge.source_id == "budget_check"
        and edge.target_id == "request_revision"
        and edge.label == "rejected"
        for edge in request.edges
    )


def test_build_flowchart_elk_layout_request_preserves_nodes_and_edges_without_lanes():
    process = {
        "lanes": [
            {"id": "sales", "name": "Sales"},
            {"id": "ops", "name": "Operations"},
        ],
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start", "lane": "sales"},
            {"id": "review", "kind": "task", "name": "Review", "lane": "ops"},
            {"id": "finish", "kind": "end", "name": "Finish", "lane": "ops"},
        ],
        "edges": [
            {"source": "start", "target": "review"},
            {"source": "review", "target": "finish", "outcome": "approved"},
        ],
    }

    request = build_flowchart_elk_layout_request(
        process,
        options=RenderOptions(diagram="flowchart", orientation="tb"),
    )

    assert request.diagram == "flowchart"
    assert request.direction == "DOWN"
    assert request.lanes == ()
    assert [node.id for node in request.nodes] == ["start", "review", "finish"]
    assert all(node.lane_id is None for node in request.nodes)
    assert [edge.id for edge in request.edges] == [
        "e0:start->review",
        "e1:review->finish",
    ]
    assert request.edges[1].label == "approved"


def test_build_flowchart_elk_layout_request_accepts_reference_example():
    path = Path("examples/reference/linear.flo")
    adapter_model = parse_adapter(
        path.read_text(encoding="utf-8"), source_path=str(path)
    )

    request = build_flowchart_elk_layout_request(
        adapter_model,
        options=RenderOptions(diagram="flowchart", orientation="lr"),
    )

    assert request.direction == "RIGHT"
    assert request.lanes == ()
    assert [node.id for node in request.nodes] == [
        "start",
        "collect_docs",
        "verify",
        "approved",
        "finish",
    ]
    assert all(node.lane_id is None for node in request.nodes)
    assert any(
        edge.source_id == "approved"
        and edge.target_id == "finish"
        and edge.label == "yes"
        for edge in request.edges
    )
    assert any(
        edge.source_id == "approved"
        and edge.target_id == "collect_docs"
        and edge.label == "no"
        for edge in request.edges
    )


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
