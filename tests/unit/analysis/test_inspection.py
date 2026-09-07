from __future__ import annotations

from copy import deepcopy
from typing import Any, cast

import pytest

from flo.process.analysis import inspect_process_model
from flo.process.ir._internal_shape import ir_to_internal_dict
from flo.process.ir.models import IR, Edge, Node


def test_model_inspection_summarizes_context_entities_paths_and_views() -> None:
    process = _inspectable_process()
    before = deepcopy(ir_to_internal_dict(process))

    report = inspect_process_model(
        process,
        entry_source="process.flo",
        included_sources=("parts/resources.flo", "parts/flow.flo"),
        requested_analysis="timing",
        requested_diagram="sppm",
        supported_diagrams=("sppm", "spaghetti", "swimlane"),
    )
    payload = report.as_dict()

    assert payload["report_version"] == "0.1"
    assert payload["validation_status"] == "valid"
    assert payload["process"] == {
        "id": "claims",
        "name": "Claims",
        "version": 4,
        "owner": {"id": "owner", "name": "Owner"},
        "business_unit_ids": ["ops"],
    }
    assert payload["composition"] == {
        "entry_source": "process.flo",
        "included_sources": ["parts/flow.flo", "parts/resources.flo"],
        "source_count": 3,
        "composed": True,
    }
    assert payload["model_summary"] == {
        "node_count": 3,
        "edge_count": 2,
        "lane_count": 1,
        "lane_ids": ["ops"],
    }
    assert payload["entities"] == {
        "items": {"count": 1, "ids": ["claim"]},
        "resources": {"count": 1, "ids": ["reviewer"]},
        "locations": {"count": 1, "ids": ["desk"]},
    }
    assert payload["paths"]["items"][0]["node_ids"] == [
        "start",
        "review",
        "end",
    ]
    assert payload["views"] == [
        {"view_id": "default", "label": "Default", "diagram": "sppm"},
        {"view_id": "book", "label": "Book", "diagram": "sppm"},
        {"view_id": "movement", "label": None, "diagram": "spaghetti"},
    ]
    assert [item["status"] for item in payload["readiness"]] == ["ready", "ready"]
    assert ir_to_internal_dict(process) == before


def test_model_inspection_distinguishes_missing_and_unsupported_readiness() -> None:
    process = IR(
        name="Minimal",
        nodes=[Node(id="start", type="start"), Node(id="end", type="end")],
        edges=[Edge(source="start", target="end")],
    )

    timing = inspect_process_model(process, requested_analysis="timing")
    swimlane = inspect_process_model(
        process,
        requested_diagram="swimlane",
        supported_diagrams=("swimlane",),
    )
    value_stream = inspect_process_model(
        process,
        requested_diagram="value_stream",
        supported_diagrams=("sppm",),
    )

    assert timing.readiness[0].status == "unavailable"
    assert timing.readiness[0].findings[0].kind == "missing_required"
    assert swimlane.readiness[0].status == "partial"
    assert swimlane.readiness[0].findings[0].kind == "missing_optional"
    assert value_stream.readiness[0].status == "unavailable"
    assert value_stream.readiness[0].findings[0].kind == "unsupported"


@pytest.mark.parametrize(
    ("position_target", "expected_status", "expected_code"),
    [
        (True, "ready", None),
        (False, "unavailable", "readiness-spaghetti-spatial-missing"),
    ],
)
def test_spaghetti_readiness_checks_inferred_routes_and_spatial_data(
    position_target: bool,
    expected_status: str,
    expected_code: str | None,
) -> None:
    target_spatial = {"x": 2, "y": 1} if position_target else {}
    process = IR(
        name="Movement",
        nodes=[
            Node(id="start", type="start", attrs={"location": "a"}),
            Node(id="end", type="end", attrs={"location": "b"}),
        ],
        edges=[Edge(source="start", target="end")],
        locations=[
            {"id": "a", "name": "A", "metadata": {"spatial": {"x": 0, "y": 0}}},
            {"id": "b", "name": "B", "metadata": {"spatial": target_spatial}},
        ],
    )

    report = inspect_process_model(
        process,
        requested_diagram="spaghetti",
        supported_diagrams=("spaghetti",),
    )

    readiness = report.readiness[0]
    assert readiness.status == expected_status
    assert (readiness.findings[0].code if readiness.findings else None) == expected_code


def test_inspection_requires_canonical_ir() -> None:
    with pytest.raises(TypeError, match="requires canonical IR"):
        inspect_process_model(cast(Any, {}))  # type: ignore[arg-type]


def _inspectable_process() -> IR:
    return IR(
        name="Claims",
        process_version=4,
        process_metadata={"process_id": "claims", "process_name": "Claims"},
        process_owner={"id": "owner", "name": "Owner"},
        business_units=[{"id": "ops", "name": "Operations"}],
        lanes=[{"id": "ops", "name": "Operations", "type": "team"}],
        items=[{"id": "claim", "name": "Claim", "kind": "information"}],
        resources=[{"id": "reviewer", "name": "Reviewer", "kind": "person"}],
        locations=[{"id": "desk", "name": "Desk"}],
        render_intent={
            "defaults": {"diagram": "sppm"},
            "views": {
                "movement": {"diagram": "spaghetti"},
                "book": {"label": "Book"},
            },
        },
        nodes=[
            Node(id="start", type="start"),
            Node(
                id="review",
                type="task",
                attrs={
                    "lane": "ops",
                    "metadata": {
                        "value_class": "VA",
                        "cycle_time": {"value": 5, "unit": "min"},
                    },
                },
            ),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="review"),
            Edge(source="review", target="end"),
        ],
    )
