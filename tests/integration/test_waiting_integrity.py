"""CLI/API delivery preserves waiting evidence and warning-only success."""

import json
from copy import deepcopy

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
        "metadata": {
            "cycle_time": {"value": 1, "unit": "min"},
            "wait_before": {"value": minutes, "unit": "min", "measurement_id": node_id},
            "crossover_time": {"value": 0, "unit": "s"},
        },
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
                "metadata": {
                    "wait_time": {
                        "value": 5,
                        "unit": "min",
                        "measurement_refs": ["work"],
                    }
                },
            },
            _work("work", 5),
            {"id": "end", "kind": "end"},
        ],
    }


@pytest.mark.parametrize("aggregate", [False, True])
def test_contradictory_waits_stop_all_validated_consumers(tmp_path, aggregate):
    model = _model()
    wait = model["steps"][1]["metadata"]["wait_time"]
    wait["value"] = 100
    if not aggregate:
        wait.pop("measurement_refs")
        wait["measurement_id"] = "work"
    content = yaml.safe_dump(model, sort_keys=False)
    source = tmp_path / "invalid.flo"
    source.write_text(content)
    expected_code = "E1510" if aggregate else "E1509"
    expected = api.validate(content, source_path=str(source)).report
    diagnostic = expected.diagnostics[0]
    assert diagnostic.code == expected_code and diagnostic.stage == "validate"
    assert diagnostic.source == str(source)
    assert diagnostic.line and diagnostic.excerpt and diagnostic.field_path
    assert diagnostic.suggestion
    for operation in (api.inspect, api.export):
        result = operation(content, source_path=str(source))
        assert not result.ok and result.value is None
        assert result.report == expected
    output = tmp_path / "invalid.svg"
    for args in (
        ["validate", str(source)],
        ["inspect", str(source), "--format", "json"],
        ["export", str(source)],
        ["render", str(source), "--render-to", str(output)],
    ):
        command = CliRunner().invoke(cli, [*args, "--diagnostics-format", "json"])
        assert command.exit_code == 4 and command.stdout == ""
        assert json.loads(command.stderr) == json.loads(json.dumps(expected.as_dict()))
    assert not output.exists()


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
    model["items"] = {"batch": {"items": items}} if grouped else items
    model["steps"][2]["consumes"] = ["material", "signal"]
    before = deepcopy(model)
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
    assert model == before


def test_included_wait_contradiction_reports_the_actual_source_file(tmp_path):
    model = _model()
    fragment = {"steps": [model["steps"].pop(2)]}
    model["steps"][1]["metadata"]["wait_time"] = {
        "value": 100,
        "unit": "min",
        "measurement_id": "work",
    }
    # Explicit transitions make include-order irrelevant to the control flow.
    model["transitions"] = [
        {"source": "start", "target": "queue"},
        {"source": "queue", "target": "work"},
        {"source": "work", "target": "end"},
    ]
    model["includes"] = ["part.flo"]
    included = tmp_path / "part.flo"
    included.write_text(yaml.safe_dump(fragment))
    result = api.validate(yaml.safe_dump(model), source_path=str(tmp_path / "root.flo"))
    assert not result.ok
    assert result.diagnostics[0].code == "E1509"
    assert result.diagnostics[0].source == str(included)
    assert result.diagnostics[0].include_chain[-1] == str(included)
