import json

import pytest

from flo.process.analysis.timing import analyze_process_timing
from flo.process.ir.models import IR, Edge, Node


def _profile(value, unit):
    return {
        "basis": "observed",
        "results": {
            "mean": {"method": "mean", "value": value, "unit": unit},
        },
        "primary": "mean",
        "analysis_input": "mean",
    }


def _process(**measurements):
    return IR(
        name="Timing states",
        nodes=[
            Node(id="start", type="start"),
            Node(id="work", type="task", **measurements),
            Node(id="end", type="end"),
        ],
        edges=[Edge(source="start", target="work"), Edge(source="work", target="end")],
    )


@pytest.mark.parametrize(
    "raw",
    [
        {},
        _profile(True, "min"),
        _profile(float("nan"), "min"),
        _profile(float("inf"), "s"),
        _profile(1e308, "d"),
        _profile(10**400, "s"),
    ],
)
def test_invalid_optional_timing_cannot_produce_complete_lead_time(raw):
    result = analyze_process_timing(
        _process(cycle_time=_profile(1, "min"), changeover_time=raw)
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


def test_omitted_timing_and_measured_zero_have_different_diagnostics():
    omitted = analyze_process_timing(_process())
    assert [item.code for item in omitted.diagnostics] == ["timing-incomplete"]
    assert omitted.declared_totals.cycle_time_seconds is None
    zero = analyze_process_timing(_process(cycle_time=_profile(0, "min")))
    assert zero.modeled_lead_time_seconds == 0
    assert not zero.diagnostics


def test_numeric_overflow_does_not_crash_or_report_partial_lead_time():
    process = _process(
        cycle_time=_profile(1e308, "s"),
        wait_time=_profile(1e308, "s"),
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
            cycle_time=_profile(1e308, "s"),
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
