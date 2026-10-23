import json

import pytest

from flo.process.analysis.timing import analyze_process_timing
from flo.process.ir.models import IR, Edge, Node


def _process(metadata):
    return IR(
        name="Timing states",
        nodes=[
            Node(id="start", type="start"),
            Node(id="work", type="task", attrs={"metadata": metadata}),
            Node(id="end", type="end"),
        ],
        edges=[Edge(source="start", target="work"), Edge(source="work", target="end")],
    )


@pytest.mark.parametrize(
    "raw",
    [
        None,
        {},
        {"value": 1},
        {"value": True, "unit": "min"},
        {"value": float("nan"), "unit": "min"},
        {"value": float("inf"), "unit": "s"},
        {"value": 1e308, "unit": "d"},
        {"value": 10**400, "unit": "s"},
    ],
)
def test_invalid_optional_timing_cannot_produce_complete_lead_time(raw):
    result = analyze_process_timing(
        _process({"cycle_time": {"value": 1, "unit": "min"}, "changeover_time": raw})
    )
    assert not result.timing_complete
    assert not result.paths[0].complete
    assert result.modeled_lead_time_seconds is None
    assert result.declared_totals.changeover_time_seconds is None
    assert any(
        item.code == "timing-invalid-duration" and item.field == "changeover_time"
        for item in result.diagnostics
    )
    json.dumps(result.as_dict(), allow_nan=False)


def test_omitted_timing_and_explicit_null_have_different_diagnostics():
    omitted = analyze_process_timing(_process({}))
    invalid = analyze_process_timing(_process({"cycle_time": None}))
    assert [item.code for item in omitted.diagnostics] == ["timing-incomplete"]
    assert [item.code for item in invalid.diagnostics] == [
        "timing-invalid-duration",
        "timing-incomplete",
    ]
    assert omitted.declared_totals.cycle_time_seconds is None
    zero = analyze_process_timing(_process({"cycle_time": {"value": 0, "unit": "min"}}))
    assert zero.modeled_lead_time_seconds == 0
    assert not zero.diagnostics


def test_numeric_overflow_does_not_crash_or_report_partial_lead_time():
    process = _process(
        {
            "cycle_time": {"value": 1e308, "unit": "s"},
            "wait_before": {"value": 1e308, "unit": "s"},
        }
    )
    result = analyze_process_timing(process)
    assert result.modeled_lead_time_seconds is None
    assert not result.paths[0].complete
    assert any(item.code == "timing-total-overflow" for item in result.diagnostics)
    json.dumps(result.as_dict(), allow_nan=False)
    process.nodes.insert(
        2,
        Node(
            id="other",
            type="task",
            attrs={"metadata": {"cycle_time": {"value": 1e308, "unit": "s"}}},
        ),
    )
    process.edges = [
        Edge(source="start", target="work"),
        Edge(source="work", target="other"),
        Edge(source="other", target="end"),
    ]
    result = analyze_process_timing(process)
    assert result.declared_totals.cycle_time_seconds is None
    assert result.declared_totals.wait_time_seconds == 1e308
    assert result.declared_totals.elapsed_time_seconds is None
    assert result.maximum_path_lead_time_seconds is None
    json.dumps(result.as_dict(), allow_nan=False)
