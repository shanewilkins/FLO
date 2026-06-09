import logging

import pytest

import flo.render.layout_core.elk_adapter as elk_adapter
from flo.render._diagnostics import RenderDiagnostic
from flo.render.layout_core import (
    build_flowchart_elk_layout_request,
    build_sppm_elk_layout_request,
    build_swimlane_elk_layout_request,
    execute_elk_layout,
    LayoutBounds,
    LayoutPoint,
    LayoutResult,
    layout_sppm_with_elk,
    layout_swimlane_with_elk,
    normalize_elk_layout_result,
    RoutedEdgePath,
    serialize_elk_layout_request,
    serialize_layout_result,
)
from flo.render.options import RenderOptions
from flo.services.logging import configure_logging
from flo.services.errors import RenderError


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
    assert edge_path.source_port_side == "SOUTH"
    assert edge_path.target_port_side == "NORTH"


def test_normalize_elk_layout_result_balances_mainline_queue_to_task_gaps():
    request = build_sppm_elk_layout_request(
        {
            "nodes": [
                {"id": "start", "kind": "start", "name": "Start"},
                {"id": "process_queue", "kind": "queue", "name": "Process Queue"},
                {
                    "id": "assess_scope_wait_queue",
                    "kind": "queue",
                    "name": "Assess Scope Queue",
                },
                {
                    "id": "assess_scope",
                    "kind": "task",
                    "name": "Assess Service Scope",
                },
                {
                    "id": "rework_quality_wait_queue",
                    "kind": "queue",
                    "name": "Rework Quality Queue",
                },
                {"id": "rework_quality", "kind": "task", "name": "Rework Quality"},
                {"id": "finish", "kind": "end", "name": "Finish"},
            ],
            "edges": [
                {"source": "start", "target": "process_queue"},
                {"source": "process_queue", "target": "assess_scope_wait_queue"},
                {"source": "assess_scope_wait_queue", "target": "assess_scope"},
                {"source": "assess_scope", "target": "finish", "outcome": "pass"},
                {
                    "source": "assess_scope",
                    "target": "rework_quality_wait_queue",
                    "outcome": "fail",
                    "edge_type": "rework",
                },
                {"source": "rework_quality_wait_queue", "target": "rework_quality"},
                {
                    "source": "rework_quality",
                    "target": "assess_scope",
                    "edge_type": "rework",
                },
            ],
        },
        options=RenderOptions(diagram="sppm", orientation="lr"),
    )

    result = normalize_elk_layout_result(
        {
            "id": "root",
            "width": 5200,
            "height": 480,
            "children": [
                {"id": "start", "x": 40.0, "y": 40.0, "width": 80.0, "height": 80.0},
                {
                    "id": "process_queue",
                    "x": 1713.0,
                    "y": 12.0,
                    "width": 189.0,
                    "height": 150.0,
                },
                {
                    "id": "assess_scope_wait_queue",
                    "x": 1958.0,
                    "y": 12.0,
                    "width": 214.0,
                    "height": 150.0,
                },
                {
                    "id": "assess_scope",
                    "x": 2564.0,
                    "y": 12.0,
                    "width": 310.0,
                    "height": 150.0,
                },
                {
                    "id": "rework_quality_wait_queue",
                    "x": 3400.0,
                    "y": 220.0,
                    "width": 220.0,
                    "height": 150.0,
                },
                {
                    "id": "rework_quality",
                    "x": 2870.0,
                    "y": 220.0,
                    "width": 220.0,
                    "height": 150.0,
                },
                {"id": "finish", "x": 4700.0, "y": 40.0, "width": 90.0, "height": 80.0},
            ],
            "edges": [
                {
                    "id": "e0:start->process_queue",
                    "sources": ["start__port_east"],
                    "targets": ["process_queue__port_west"],
                    "sections": [
                        {
                            "startPoint": {"x": 120.0, "y": 80.0},
                            "endPoint": {"x": 1713.0, "y": 87.0},
                        }
                    ],
                },
                {
                    "id": "e1:process_queue->assess_scope_wait_queue",
                    "sources": ["process_queue__port_east"],
                    "targets": ["assess_scope_wait_queue__port_west"],
                    "sections": [
                        {
                            "startPoint": {"x": 1902.0, "y": 87.0},
                            "endPoint": {"x": 2011.5, "y": 87.0},
                        }
                    ],
                },
                {
                    "id": "e2:assess_scope_wait_queue->assess_scope",
                    "sources": ["assess_scope_wait_queue__port_east"],
                    "targets": ["assess_scope__port_west"],
                    "sections": [
                        {
                            "startPoint": {"x": 2118.5, "y": 87.0},
                            "endPoint": {"x": 2564.0, "y": 87.0},
                        }
                    ],
                },
                {
                    "id": "e3:assess_scope->finish",
                    "sources": ["assess_scope__port_east"],
                    "targets": ["finish__port_west"],
                    "sections": [
                        {
                            "startPoint": {"x": 2874.0, "y": 87.0},
                            "endPoint": {"x": 4700.0, "y": 80.0},
                        }
                    ],
                },
                {
                    "id": "e4:assess_scope->rework_quality_wait_queue",
                    "sources": ["assess_scope__port_south"],
                    "targets": ["rework_quality_wait_queue__port_north"],
                    "sections": [
                        {
                            "startPoint": {"x": 2719.0, "y": 162.0},
                            "endPoint": {"x": 3510.0, "y": 220.0},
                        }
                    ],
                },
                {
                    "id": "e5:rework_quality_wait_queue->rework_quality",
                    "sources": ["rework_quality_wait_queue__port_west"],
                    "targets": ["rework_quality__port_east"],
                    "sections": [
                        {
                            "startPoint": {"x": 3400.0, "y": 295.0},
                            "endPoint": {"x": 3090.0, "y": 295.0},
                        }
                    ],
                },
                {
                    "id": "e6:rework_quality->assess_scope",
                    "sources": ["rework_quality__port_north"],
                    "targets": ["assess_scope__port_south"],
                    "sections": [
                        {
                            "startPoint": {"x": 2980.0, "y": 220.0},
                            "endPoint": {"x": 2719.0, "y": 162.0},
                        }
                    ],
                },
            ],
        },
        request=request,
    )

    process_bounds = result.node_bounds["process_queue"]
    wait_queue_bounds = result.node_bounds["assess_scope_wait_queue"]
    task_bounds = result.node_bounds["assess_scope"]

    gap_left = wait_queue_bounds.x_px - (process_bounds.x_px + process_bounds.width_px)
    gap_right = task_bounds.x_px - (wait_queue_bounds.x_px + wait_queue_bounds.width_px)

    assert gap_left > 0.0
    assert gap_right > 0.0
    assert abs(gap_left - gap_right) <= 1.0


def test_normalize_elk_layout_result_equalizes_mainline_horizontal_gaps():
    request = build_sppm_elk_layout_request(
        {
            "nodes": [
                {"id": "start", "kind": "start", "name": "Start"},
                {"id": "q1", "kind": "queue", "name": "Queue 1"},
                {"id": "t1", "kind": "task", "name": "Task 1"},
                {"id": "q2", "kind": "queue", "name": "Queue 2"},
                {"id": "t2", "kind": "task", "name": "Task 2"},
                {"id": "rw_q", "kind": "queue", "name": "Rework Queue"},
                {"id": "rw_t", "kind": "task", "name": "Rework Task"},
                {"id": "finish", "kind": "end", "name": "Finish"},
            ],
            "edges": [
                {"source": "start", "target": "q1"},
                {"source": "q1", "target": "t1"},
                {"source": "t1", "target": "q2"},
                {"source": "q2", "target": "t2"},
                {"source": "t2", "target": "finish", "outcome": "pass"},
                {
                    "source": "t2",
                    "target": "rw_q",
                    "outcome": "fail",
                    "edge_type": "rework",
                },
                {"source": "rw_q", "target": "rw_t"},
                {
                    "source": "rw_t",
                    "target": "t2",
                    "edge_type": "rework",
                },
            ],
        },
        options=RenderOptions(diagram="sppm", orientation="lr"),
    )

    result = normalize_elk_layout_result(
        {
            "id": "root",
            "width": 5200,
            "height": 480,
            "children": [
                {"id": "start", "x": 40.0, "y": 40.0, "width": 80.0, "height": 80.0},
                {"id": "q1", "x": 500.0, "y": 12.0, "width": 180.0, "height": 150.0},
                {"id": "t1", "x": 720.0, "y": 12.0, "width": 300.0, "height": 150.0},
                {"id": "q2", "x": 1500.0, "y": 12.0, "width": 200.0, "height": 150.0},
                {"id": "t2", "x": 1760.0, "y": 12.0, "width": 320.0, "height": 150.0},
                {
                    "id": "rw_q",
                    "x": 2400.0,
                    "y": 220.0,
                    "width": 220.0,
                    "height": 150.0,
                },
                {
                    "id": "rw_t",
                    "x": 2100.0,
                    "y": 220.0,
                    "width": 220.0,
                    "height": 150.0,
                },
                {"id": "finish", "x": 2500.0, "y": 40.0, "width": 90.0, "height": 80.0},
            ],
            "edges": [
                {
                    "id": "e0:start->q1",
                    "sources": ["start__port_east"],
                    "targets": ["q1__port_west"],
                    "sections": [
                        {
                            "startPoint": {"x": 120.0, "y": 80.0},
                            "endPoint": {"x": 500.0, "y": 87.0},
                        }
                    ],
                },
                {
                    "id": "e1:q1->t1",
                    "sources": ["q1__port_east"],
                    "targets": ["t1__port_west"],
                    "sections": [
                        {
                            "startPoint": {"x": 680.0, "y": 87.0},
                            "endPoint": {"x": 720.0, "y": 87.0},
                        }
                    ],
                },
                {
                    "id": "e2:t1->q2",
                    "sources": ["t1__port_east"],
                    "targets": ["q2__port_west"],
                    "sections": [
                        {
                            "startPoint": {"x": 1020.0, "y": 87.0},
                            "endPoint": {"x": 1500.0, "y": 87.0},
                        }
                    ],
                },
                {
                    "id": "e3:q2->t2",
                    "sources": ["q2__port_east"],
                    "targets": ["t2__port_west"],
                    "sections": [
                        {
                            "startPoint": {"x": 1700.0, "y": 87.0},
                            "endPoint": {"x": 1760.0, "y": 87.0},
                        }
                    ],
                },
                {
                    "id": "e4:t2->finish",
                    "sources": ["t2__port_east"],
                    "targets": ["finish__port_west"],
                    "sections": [
                        {
                            "startPoint": {"x": 2080.0, "y": 87.0},
                            "endPoint": {"x": 2500.0, "y": 80.0},
                        }
                    ],
                },
                {
                    "id": "e5:t2->rw_q",
                    "sources": ["t2__port_south"],
                    "targets": ["rw_q__port_north"],
                    "sections": [
                        {
                            "startPoint": {"x": 1920.0, "y": 162.0},
                            "endPoint": {"x": 2510.0, "y": 220.0},
                        }
                    ],
                },
                {
                    "id": "e6:rw_q->rw_t",
                    "sources": ["rw_q__port_west"],
                    "targets": ["rw_t__port_east"],
                    "sections": [
                        {
                            "startPoint": {"x": 2400.0, "y": 295.0},
                            "endPoint": {"x": 2320.0, "y": 295.0},
                        }
                    ],
                },
                {
                    "id": "e7:rw_t->t2",
                    "sources": ["rw_t__port_north"],
                    "targets": ["t2__port_south"],
                    "sections": [
                        {
                            "startPoint": {"x": 2210.0, "y": 220.0},
                            "endPoint": {"x": 1920.0, "y": 162.0},
                        }
                    ],
                },
            ],
        },
        request=request,
    )

    ordered_ids = sorted(
        ["start", "q1", "t1", "q2", "t2", "finish"],
        key=lambda node_id: result.node_bounds[node_id].x_px,
    )
    gaps = []
    for left_id, right_id in zip(ordered_ids, ordered_ids[1:]):
        left = result.node_bounds[left_id]
        right = result.node_bounds[right_id]
        gaps.append(right.x_px - (left.x_px + left.width_px))

    assert max(gaps) - min(gaps) <= 1.0


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


def test_normalize_elk_layout_result_reports_missing_expected_edge_diagnostic():
    request = build_flowchart_elk_layout_request(
        {
            "nodes": [
                {"id": "start", "kind": "start", "name": "Start"},
                {"id": "finish", "kind": "end", "name": "Finish"},
            ],
            "edges": [{"source": "start", "target": "finish"}],
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
            "edges": [],
        },
        request=request,
    )

    assert any(
        diagnostic.code == "elk-edge-missing" for diagnostic in result.diagnostics
    )
    assert all(diagnostic.severity == "warning" for diagnostic in result.diagnostics)


def test_execute_elk_layout_raises_render_error_for_strict_diagnostics():
    request = build_flowchart_elk_layout_request(
        {
            "nodes": [
                {"id": "start", "kind": "start", "name": "Start"},
                {"id": "finish", "kind": "end", "name": "Finish"},
            ],
            "edges": [{"source": "start", "target": "finish"}],
        },
        options=RenderOptions(
            diagram="flowchart", orientation="lr", layout_fit="fit-strict"
        ),
    )

    def fake_engine(_payload: dict[str, object]) -> dict[str, object]:
        return {
            "id": "flo:flowchart",
            "width": 360,
            "height": 160,
            "children": [
                {"id": "start", "x": 20, "y": 54, "width": 120, "height": 52},
                {"id": "finish", "x": 220, "y": 54, "width": 120, "height": 52},
            ],
            "edges": [],
        }

    with pytest.raises(RenderError, match="did not normalize requested edge"):
        execute_elk_layout(request, engine=fake_engine)


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


def test_layout_swimlane_with_elk_logs_render_diagnostics(monkeypatch, capsys):
    def fake_execute_elk_layout(_request, *, engine):
        return LayoutResult(
            orientation="tb",
            canvas_bounds=LayoutBounds(x_px=0, y_px=0, width_px=320, height_px=280),
            node_bounds={
                "start": LayoutBounds(x_px=36, y_px=44, width_px=120, height_px=52),
                "review": LayoutBounds(x_px=36, y_px=180, width_px=140, height_px=52),
            },
            edge_paths={
                ("start", "review"): RoutedEdgePath(
                    edge=("start", "review"),
                    points=(
                        LayoutPoint(x_px=96, y_px=96),
                        LayoutPoint(x_px=96, y_px=180),
                    ),
                    label="handoff",
                )
            },
            diagnostics=(
                RenderDiagnostic(
                    code="elk-edge-missing",
                    severity="warning",
                    message="ELK response did not normalize requested edge 'start->review'.",
                    metadata={"source_id": "start", "target_id": "review"},
                ),
            ),
        )

    root = logging.getLogger()
    old_handlers = list(root.handlers)
    old_level = root.level
    try:
        root.handlers.clear()
        configure_logging(level=logging.INFO)
        monkeypatch.setattr(elk_adapter, "execute_elk_layout", fake_execute_elk_layout)

        result = layout_swimlane_with_elk(
            {
                "lanes": [{"id": "sales", "name": "Sales"}],
                "nodes": [
                    {"id": "start", "kind": "start", "name": "Start", "lane": "sales"},
                    {"id": "review", "kind": "task", "name": "Review", "lane": "sales"},
                ],
                "edges": [
                    {"source": "start", "target": "review", "outcome": "handoff"}
                ],
            },
            engine=lambda payload: payload,
            options=RenderOptions(diagram="swimlane", orientation="tb"),
        )

        assert result.diagnostics[0].code == "elk-edge-missing"
        captured = capsys.readouterr()
        assert "render_diagnostics_summary" in captured.err
        assert "render_diagnostic" in captured.err
        assert (
            "backend='elk'" in captured.err
            or 'backend="elk"' in captured.err
            or "backend=elk" in captured.err
        )
        assert "layout_result" in captured.err
        assert "start->review" in captured.err
    finally:
        root.handlers = old_handlers
        root.setLevel(old_level)


def test_layout_sppm_with_elk_logs_render_diagnostics(monkeypatch, capsys):
    def fake_execute_elk_layout(_request, *, engine):
        return LayoutResult(
            orientation="lr",
            canvas_bounds=LayoutBounds(x_px=0, y_px=0, width_px=320, height_px=160),
            node_bounds={
                "start": LayoutBounds(x_px=20, y_px=54, width_px=120, height_px=52),
                "queue": LayoutBounds(x_px=180, y_px=54, width_px=120, height_px=52),
            },
            edge_paths={
                ("start", "queue"): RoutedEdgePath(
                    edge=("start", "queue"),
                    points=(
                        LayoutPoint(x_px=140, y_px=80),
                        LayoutPoint(x_px=180, y_px=80),
                    ),
                    label="next",
                )
            },
            diagnostics=(
                RenderDiagnostic(
                    code="elk-lane-frame-missing",
                    severity="warning",
                    message="ELK response did not produce geometry for expected lane 'front'.",
                    metadata={"lane_id": "front"},
                ),
            ),
        )

    root = logging.getLogger()
    old_handlers = list(root.handlers)
    old_level = root.level
    try:
        root.handlers.clear()
        configure_logging(level=logging.INFO)
        monkeypatch.setattr(elk_adapter, "execute_elk_layout", fake_execute_elk_layout)

        result = layout_sppm_with_elk(
            {
                "lanes": [{"id": "front", "name": "Front"}],
                "nodes": [
                    {"id": "start", "kind": "start", "name": "Start", "lane": "front"},
                    {
                        "id": "queue",
                        "kind": "queue",
                        "name": "Wait Queue",
                        "lane": "front",
                    },
                ],
                "edges": [{"source": "start", "target": "queue", "outcome": "next"}],
            },
            engine=lambda payload: payload,
            options=RenderOptions(diagram="sppm", orientation="lr"),
        )

        assert result.diagnostics[0].code == "elk-lane-frame-missing"
        captured = capsys.readouterr()
        assert "render_diagnostics_summary" in captured.err
        assert "render_diagnostic" in captured.err
        assert (
            "backend='elk'" in captured.err
            or 'backend="elk"' in captured.err
            or "backend=elk" in captured.err
        )
        assert "expected lane 'front'" in captured.err
    finally:
        root.handlers = old_handlers
        root.setLevel(old_level)


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


def test_normalize_elk_layout_result_captures_edge_label_point_from_elk_geometry():
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
                    "labels": [
                        {
                            "text": "done",
                            "x": 170,
                            "y": 64,
                            "width": 20,
                            "height": 10,
                        }
                    ],
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

    edge_path = result.path_for("start", "finish")
    assert edge_path is not None
    assert edge_path.label == "done"
    assert edge_path.label_point is not None
    assert edge_path.label_point.x_px == 180.0
    assert edge_path.label_point.y_px == 69.0


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
