from pathlib import Path

from flo.adapters import parse_adapter
from flo.render._sppm_node_content import build_sppm_node_content
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


def test_build_sppm_elk_layout_request_accepts_reference_example_without_inventing_lanes():
    path = Path("examples/reference/washnfold.flo")
    adapter_model = parse_adapter(
        path.read_text(encoding="utf-8"), source_path=str(path)
    )

    request = build_sppm_elk_layout_request(
        adapter_model,
        options=RenderOptions(diagram="sppm", orientation="lr"),
    )

    assert request.diagram == "sppm"
    assert request.direction == "RIGHT"
    assert request.lanes == ()
    assert any(
        node.id == "sort_tag_wait_queue" and node.kind == "queue"
        for node in request.nodes
    )
    assert any(node.id == "wash" and node.kind == "task" for node in request.nodes)
    assert any(
        edge.source_id == "stage_notify" and edge.target_id == "payment_delivery"
        for edge in request.edges
    )


def test_build_sppm_elk_layout_request_preserves_explicit_lane_structure_when_present():
    process = {
        "lanes": [{"id": "front", "name": "Front Office"}],
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start", "lane": "front"},
            {"id": "finish", "kind": "end", "name": "Done", "lane": "front"},
        ],
        "edges": [{"source": "start", "target": "finish"}],
    }

    request = build_sppm_elk_layout_request(
        process,
        options=RenderOptions(diagram="sppm", orientation="tb"),
    )

    assert [lane.id for lane in request.lanes] == ["front"]
    assert request.lanes[0].node_ids == ("start", "finish")
    assert [node.lane_id for node in request.nodes] == ["front", "front"]


def test_build_sppm_elk_layout_request_adds_synthetic_rows_for_rework_loops():
    request = build_sppm_elk_layout_request(
        {
            "nodes": [
                {"id": "start", "kind": "start", "name": "Start"},
                {"id": "review", "kind": "task", "name": "Review"},
                {"id": "decision", "kind": "decision", "name": "Approved?"},
                {"id": "rework_queue", "kind": "queue", "name": "Rework Queue"},
                {"id": "rework_task", "kind": "task", "name": "Fix"},
                {"id": "finish", "kind": "end", "name": "Finish"},
            ],
            "edges": [
                {"source": "start", "target": "review"},
                {"source": "review", "target": "decision"},
                {"source": "decision", "target": "finish", "outcome": "yes"},
                {
                    "source": "decision",
                    "target": "rework_queue",
                    "outcome": "no",
                    "edge_type": "rework",
                },
                {"source": "rework_queue", "target": "rework_task"},
                {
                    "source": "rework_task",
                    "target": "decision",
                    "edge_type": "rework",
                },
            ],
        },
        options=RenderOptions(diagram="sppm", orientation="lr"),
    )

    assert [lane.id for lane in request.lanes] == [
        "__sppm_row_mainline",
        "__sppm_row_rework",
    ]
    assert request.lanes[0].node_ids == ("start", "review", "decision", "finish")
    assert request.lanes[1].node_ids == ("rework_queue", "rework_task")


def test_build_sppm_elk_layout_request_measures_richer_node_content_for_elk():
    request = build_sppm_elk_layout_request(
        {
            "nodes": [
                {
                    "id": "queue",
                    "kind": "queue",
                    "name": "Intake Queue",
                    "metadata": {"wait_time": {"value": 12, "unit": "min"}},
                },
                {
                    "id": "task",
                    "kind": "task",
                    "name": "Review Request Context",
                    "workers": ["Coordinator", "Requester"],
                    "metadata": {
                        "description": "Capture request details and clarify missing context.",
                        "cycle_time": {"value": 4, "unit": "min"},
                    },
                },
            ],
            "edges": [{"source": "queue", "target": "task"}],
        },
        options=RenderOptions(diagram="sppm", orientation="lr"),
    )

    queue_node = next(node for node in request.nodes if node.id == "queue")
    task_node = next(node for node in request.nodes if node.id == "task")

    assert queue_node.width_px >= 150
    assert queue_node.height_px >= 150
    assert task_node.width_px > 140
    assert task_node.height_px > 52


def test_build_sppm_elk_layout_request_expands_decision_nodes_for_long_titles():
    request = build_sppm_elk_layout_request(
        {
            "nodes": [
                {
                    "id": "triage",
                    "kind": "decision",
                    "name": "Information Complete?",
                },
                {"id": "finish", "kind": "end", "name": "Done"},
            ],
            "edges": [{"source": "triage", "target": "finish", "outcome": "yes"}],
        },
        options=RenderOptions(diagram="sppm", orientation="lr"),
    )

    decision_node = next(node for node in request.nodes if node.id == "triage")

    assert decision_node.width_px > 158
    assert decision_node.height_px > 90


def test_build_sppm_elk_layout_request_wraps_queue_titles_without_forcing_ellipsis():
    content = build_sppm_node_content(
        node_id="queue",
        kind="queue",
        name="Assess Scope Wait Queue",
        metadata={},
        workers=[],
        note="",
        options=RenderOptions(diagram="sppm", orientation="lr"),
    )
    request = build_sppm_elk_layout_request(
        {
            "nodes": [
                {
                    "id": "queue",
                    "kind": "queue",
                    "name": "Assess Scope Wait Queue",
                },
                {"id": "task", "kind": "task", "name": "Next"},
            ],
            "edges": [{"source": "queue", "target": "task"}],
        },
        options=RenderOptions(diagram="sppm", orientation="lr"),
    )

    queue_node = next(node for node in request.nodes if node.id == "queue")

    assert "..." not in content.title
    assert queue_node.width_px >= 150
    assert queue_node.width_px > 150


def test_build_sppm_elk_layout_request_preserves_rework_callout_content():
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
                    "metadata": {"rate": 0.08, "reason": "Missing approvals"},
                }
            ],
        },
        options=RenderOptions(diagram="sppm", orientation="lr"),
    )

    rework_edge = request.edges[0]

    assert rework_edge.label == "no"
    assert rework_edge.is_rework is True
    assert rework_edge.rework_variant == "branch"
    assert rework_edge.callout_lines == (
        "Rate: 8%",
        "Reason: Missing approvals",
    )
    assert rework_edge.callout_near_source is True


def test_build_sppm_elk_layout_request_preserves_explicit_continuation_tokens():
    request = build_sppm_elk_layout_request(
        {
            "nodes": [
                {"id": "handoff", "kind": "task", "name": "Handoff"},
                {"id": "end", "kind": "end", "name": "End"},
            ],
            "edges": [
                {
                    "source": "handoff",
                    "target": "end",
                    "metadata": {
                        "continuation_to": "P2-OPS",
                        "continuation_from": "P1-H",
                    },
                }
            ],
        },
        options=RenderOptions(diagram="sppm", orientation="lr"),
    )

    edge = request.edges[0]

    assert edge.outgoing_token == "P2-OPS"
    assert edge.incoming_token == "P1-H"


def test_serialize_sppm_elk_layout_request_activates_partitioning_and_preserves_step_order():
    request = build_sppm_elk_layout_request(
        {
            "nodes": [
                {"id": "start", "kind": "start", "name": "Start"},
                {"id": "queue", "kind": "queue", "name": "Queue"},
                {"id": "task", "kind": "task", "name": "Task"},
                {"id": "decision", "kind": "decision", "name": "Decision?"},
            ],
            "edges": [
                {"source": "start", "target": "queue"},
                {"source": "queue", "target": "task"},
                {"source": "task", "target": "decision"},
            ],
        },
        options=RenderOptions(diagram="sppm", orientation="lr"),
    )

    payload = serialize_elk_layout_request(request)

    assert payload["layoutOptions"]["elk.partitioning.activate"] == "true"
    assert (
        payload["layoutOptions"]["elk.layered.considerModelOrder.strategy"]
        == "NODES_AND_EDGES"
    )
    assert payload["layoutOptions"]["elk.layered.feedbackEdges"] == "true"
    assert payload["layoutOptions"]["elk.edgeRouting"] == "ORTHOGONAL"
    assert payload["layoutOptions"]["elk.spacing.nodeNode"] == "56"
    assert (
        payload["layoutOptions"]["elk.layered.spacing.nodeNodeBetweenLayers"] == "120"
    )
    assert (
        payload["layoutOptions"]["elk.layered.nodePlacement.strategy"]
        == "BRANDES_KOEPF"
    )
    assert (
        payload["layoutOptions"]["elk.layered.nodePlacement.bk.fixedAlignment"]
        == "BALANCED"
    )
    assert (
        payload["layoutOptions"]["elk.layered.nodePlacement.favorStraightEdges"]
        == "true"
    )
    assert [child["id"] for child in payload["children"]] == [
        "start",
        "queue",
        "task",
        "decision",
    ]
    assert [
        child["layoutOptions"]["elk.partitioning.partition"]
        for child in payload["children"]
    ] == ["0", "1", "2", "3"]


def test_serialize_sppm_elk_layout_request_sets_start_end_layer_constraints():
    request = build_sppm_elk_layout_request(
        {
            "nodes": [
                {"id": "start", "kind": "start", "name": "Start"},
                {"id": "task", "kind": "task", "name": "Task"},
                {"id": "end", "kind": "end", "name": "End"},
            ],
            "edges": [
                {"source": "start", "target": "task"},
                {"source": "task", "target": "end"},
            ],
        },
        options=RenderOptions(diagram="sppm", orientation="lr"),
    )

    payload = serialize_elk_layout_request(request)
    children = {child["id"]: child for child in payload["children"]}

    assert (
        children["start"]["layoutOptions"]["elk.layered.layering.layerConstraint"]
        == "FIRST"
    )
    assert (
        children["end"]["layoutOptions"]["elk.layered.layering.layerConstraint"]
        == "LAST"
    )


def test_serialize_sppm_elk_layout_request_emits_cardinal_ports_and_port_attached_edges():
    request = build_sppm_elk_layout_request(
        {
            "nodes": [
                {"id": "triage", "kind": "decision", "name": "Triage?"},
                {"id": "rework_queue", "kind": "queue", "name": "Rework Queue"},
            ],
            "edges": [
                {
                    "source": "triage",
                    "target": "rework_queue",
                    "outcome": "no",
                    "edge_type": "rework",
                }
            ],
        },
        options=RenderOptions(diagram="sppm", orientation="lr"),
    )

    payload = serialize_elk_layout_request(request)
    all_nodes: dict[str, dict[str, object]] = {}
    for child in payload["children"]:
        child_id = child.get("id")
        if isinstance(child_id, str) and "ports" in child:
            all_nodes[child_id] = child
        nested_children = child.get("children")
        if isinstance(nested_children, list):
            for nested in nested_children:
                if not isinstance(nested, dict):
                    continue
                nested_id = nested.get("id")
                if isinstance(nested_id, str):
                    all_nodes[nested_id] = nested

    triage_ports = all_nodes["triage"]["ports"]
    rework_ports = all_nodes["rework_queue"]["ports"]
    assert {port["layoutOptions"]["elk.port.side"] for port in triage_ports} == {
        "NORTH",
        "EAST",
        "SOUTH",
        "WEST",
    }
    assert {port["layoutOptions"]["elk.port.side"] for port in rework_ports} == {
        "NORTH",
        "EAST",
        "SOUTH",
        "WEST",
    }
    assert all_nodes["triage"]["layoutOptions"]["elk.portConstraints"] == "FIXED_ORDER"

    edge = payload["edges"][0]
    assert edge["sources"] == ["triage__port_south"]
    assert edge["targets"] == ["rework_queue__port_north"]


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
