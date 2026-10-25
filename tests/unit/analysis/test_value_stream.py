import pytest

from flo.process.analysis import inspect_process_model, project_value_stream
from flo.process.ir.models import IR, Edge, Node
from flo.process.ir.validate import validate_ir


def test_value_stream_projection_separates_item_kinds_and_reuses_timing() -> None:
    projection = project_value_stream(_dual_flow_process())

    assert [flow.item_id for flow in projection.information_flows] == [
        "order",
        "ticket",
    ]
    assert [flow.item_id for flow in projection.material_flows] == [
        "finished",
        "raw",
    ]
    assert projection.information_flows[0].source_node_id is None
    assert projection.information_flows[1].source_node_id == "intake"
    assert projection.information_flows[1].target_node_id == "make"
    assert projection.nodes[1].cycle_time_seconds == 300.0
    assert projection.nodes[1].changeover_time_seconds == 120.0
    assert projection.nodes[2].wait_time_seconds == 600.0
    assert projection.modeled_lead_time_seconds == 1260.0
    assert projection.partial is False
    assert projection.diagnostics == ()


def test_value_stream_projection_reports_absent_surface_without_inventing_it() -> None:
    process = _dual_flow_process()
    process.items = [
        item
        for item in (process.items or [])
        if isinstance(item, dict) and item.get("kind") == "material"
    ]

    projection = project_value_stream(process)

    assert projection.information_flows == ()
    assert projection.material_flows
    assert projection.partial is True
    assert [item.code for item in projection.diagnostics] == [
        "value-stream-information-absent"
    ]


def test_value_stream_inspection_readiness_tracks_projection_surfaces() -> None:
    process = _dual_flow_process()

    ready = inspect_process_model(
        process,
        requested_diagram="value_stream",
        supported_diagrams=("value_stream",),
    )
    process.items = [
        item
        for item in (process.items or [])
        if isinstance(item, dict) and item.get("kind") == "material"
    ]
    partial = inspect_process_model(
        process,
        requested_diagram="value_stream",
        supported_diagrams=("value_stream",),
    )

    assert ready.readiness[0].status == "ready"
    assert partial.readiness[0].status == "partial"
    assert partial.readiness[0].findings[0].code == ("value-stream-information-absent")


@pytest.mark.parametrize("groups", [("batch",), ("outer", "inner")])
def test_grouped_items_project_identically_to_flat_items(groups) -> None:
    process = _dual_flow_process()
    expected = project_value_stream(process)
    entries = process.items
    for group in groups:
        entries = {"name": "Group label", group: entries}
    process.items = entries
    validate_ir(process)
    assert project_value_stream(process) == expected


@pytest.mark.parametrize("seconds", [0, 300])
def test_work_card_preserves_canonical_wait_before(seconds) -> None:
    process = _dual_flow_process()
    process.nodes[1].attrs["metadata"]["wait_before"] = {"value": seconds, "unit": "s"}
    validate_ir(process)
    result = project_value_stream(process)
    assert result.nodes[0].wait_time_seconds == seconds
    assert result.modeled_lead_time_seconds == 1260 + seconds


def _dual_flow_process() -> IR:
    return IR(
        name="Dual flow",
        process_metadata={"process_id": "dual", "process_name": "Dual flow"},
        items=[
            {"id": "order", "name": "Order", "kind": "information"},
            {"id": "ticket", "name": "Work ticket", "kind": "information"},
            {"id": "raw", "name": "Raw stock", "kind": "material"},
            {"id": "finished", "name": "Finished unit", "kind": "material"},
        ],
        nodes=[
            Node("start", "start", {"name": "Start"}),
            Node(
                "intake",
                "task",
                {
                    "name": "Intake",
                    "consumes": ["order"],
                    "produces": ["ticket"],
                    "metadata": {"cycle_time": {"value": 2, "unit": "min"}},
                },
            ),
            Node(
                "make",
                "task",
                {
                    "name": "Make",
                    "consumes": ["ticket", "raw"],
                    "produces": ["finished"],
                    "metadata": {
                        "cycle_time": {"value": 5, "unit": "min"},
                        "changeover_time": {"value": 2, "unit": "min"},
                    },
                },
            ),
            Node(
                "buffer",
                "queue",
                {
                    "name": "Finished queue",
                    "metadata": {"wait_time": {"value": 10, "unit": "min"}},
                },
            ),
            Node(
                "ship",
                "task",
                {
                    "name": "Ship",
                    "consumes": ["finished"],
                    "metadata": {"cycle_time": {"value": 2, "unit": "min"}},
                },
            ),
            Node("end", "end", {"name": "End"}),
        ],
        edges=[
            Edge("start", "intake"),
            Edge("intake", "make"),
            Edge("make", "buffer"),
            Edge("buffer", "ship"),
            Edge("ship", "end"),
        ],
    )
