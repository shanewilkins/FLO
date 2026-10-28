"""CLI/API delivery preserves waiting evidence and warning-only success."""

import json

import pytest
import yaml
from click.testing import CliRunner

from flo import api
from flo.app.cli import cli
from flo.process.analysis import analyze_process_timing


def _work(node_id, minutes):
    return {
        "id": node_id,
        "kind": "task",
        "cycle_time": _profile(1, "min"),
        "wait_time": _profile(minutes, "min"),
        "changeover_time": _profile(0, "s"),
    }


def _profile(value, unit):
    return {
        "basis": "observed",
        "results": {
            "mean": {"method": "mean", "value": value, "unit": unit},
        },
        "primary": "mean",
        "analysis_input": "mean",
    }


def _model():
    return {
        "spec_version": "0.1",
        "process": {"id": "waiting", "name": "Waiting"},
        "steps": [
            {"id": "start", "kind": "start"},
            {
                "id": "queue",
                "kind": "queue",
                "wait_time": {"ref": "work.wait_time"},
            },
            _work("work", 5),
            {"id": "end", "kind": "end"},
        ],
    }


def _incomplete_model(case):
    model = _model()
    if case == "hold":
        model["steps"][1] = {"id": "hold", "kind": "wait"}
    else:
        model["steps"].insert(
            2,
            {
                "id": "choice",
                "kind": "decision",
            },
        )
        model["steps"].insert(-1, _work("other", 0))
        model["transitions"] = [
            {"source": "start", "target": "queue"},
            {"source": "queue", "target": "choice"},
            {"source": "choice", "target": "work", "outcome": "measured"},
            {"source": "choice", "target": "other", "outcome": "other"},
            {"source": "work", "target": "end"},
            {"source": "other", "target": "end"},
        ]
    return model


@pytest.mark.parametrize(
    "case,code",
    [("hold", "timing-incomplete"), ("branch", "timing-projection-incomplete")],
)
def test_unknown_waiting_api_remains_successful_without_claiming_lead_time(case, code):
    content = yaml.safe_dump(_incomplete_model(case))
    result = api.validate(content, source_path="-")
    assert result.ok and result.report.error_count == 0
    warnings = [item for item in result.diagnostics if item.severity == "warning"]
    assert len(warnings) == 1 and warnings[0].code == code
    analysis = analyze_process_timing(result.value)
    assert not analysis.timing_complete
    assert analysis.modeled_lead_time_seconds is None
    for operation in (api.inspect, api.export):
        delivered = operation(content, source_path="-")
        assert delivered.ok
        assert (
            next(item for item in delivered.diagnostics if item.code == code)
            == warnings[0]
        )


@pytest.mark.parametrize("case", ["hold", "branch"])
@pytest.mark.parametrize("command", ["validate", "inspect", "export", "render"])
def test_unknown_waiting_cli_preserves_warning_only_success(case, command):
    content = yaml.safe_dump(_incomplete_model(case))
    expected = api.validate(content, source_path="-").report
    args = [command, "-", "--diagnostics-format", "json"]
    if command == "inspect":
        args += ["--format", "json"]
    delivered = CliRunner().invoke(cli, args, input=content)
    assert delivered.exit_code == 0, delivered.output
    report = json.loads(delivered.stderr)
    assert report["warning_count"] == 1 and report["error_count"] == 0
    assert report == json.loads(json.dumps(expected.as_dict()))
    if command == "render":
        assert (
            "<svg" in delivered.stdout and "Lead Time: Unavailable" in delivered.stdout
        )


@pytest.mark.parametrize("grouped", [False, True])
def test_value_stream_svg_retains_item_flows_and_both_copies_of_waiting(grouped):
    model = _model()
    items = [
        {"id": "material", "name": "Material", "kind": "material"},
        {"id": "signal", "name": "Signal", "kind": "information"},
    ]
    model["process"]["items"] = {"batch": {"items": items}} if grouped else items
    model["steps"][2]["consumes"] = ["material", "signal"]
    result = CliRunner().invoke(
        cli,
        ["render", "-", "--diagram", "value_stream", "--diagnostics-format", "json"],
        input=yaml.safe_dump(model),
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stderr)["diagnostics"] == []
    assert result.stdout.count("WT 5 min") == 2
    assert "Modeled lead time: 6 min" in result.stdout
    assert "Partial map" not in result.stdout
