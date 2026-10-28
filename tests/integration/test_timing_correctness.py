import json
from itertools import pairwise

import pytest
import yaml
from click.testing import CliRunner

from flo import api
from flo.app.cli import cli
from flo.errors import EXIT_COMPILE_ERROR, EXIT_VALIDATION_ERROR


def _profile(value, unit):
    return {
        "basis": "observed",
        "results": {
            "mean": {"method": "mean", "value": value, "unit": unit},
        },
        "primary": "mean",
        "analysis_input": "mean",
    }


def _source(measurements, *, queue=None):
    steps = [{"id": "start", "name": "Start", "kind": "start"}]
    if queue is not None:
        steps.append({"id": "queue", "name": "Queue", "kind": "queue", **queue})
    steps.extend(
        [
            {"id": "work", "name": "Work", "kind": "task", **measurements},
            {"id": "end", "name": "Stop", "kind": "end"},
        ]
    )
    return yaml.safe_dump(
        {
            "spec_version": "0.1",
            "process": {"id": "timing", "name": "Timing"},
            "steps": steps,
            "transitions": [
                {"source": a["id"], "target": b["id"]} for a, b in pairwise(steps)
            ],
        }
    )


@pytest.mark.parametrize(
    "raw",
    [
        None,
        {},
        _profile(True, "min"),
        _profile(-1, "min"),
        _profile(float("nan"), "min"),
        _profile(float("inf"), "s"),
    ],
)
@pytest.mark.parametrize(
    "field",
    [
        "cycle_time",
        "changeover_time",
        "wait_time",
    ],
)
def test_invalid_timing_is_rejected_before_analysis_export_or_render(
    tmp_path, raw, field
):
    source = tmp_path / "invalid.flo"
    source.write_text(_source({"cycle_time": _profile(1, "min"), field: raw}))
    output = tmp_path / "invalid.svg"
    runner = CliRunner()
    validation = runner.invoke(cli, ["validate", str(source), "--format", "json"])
    assert validation.exit_code == EXIT_COMPILE_ERROR, validation.output
    diagnostic = json.loads(validation.output)
    assert diagnostic["code"] == ("E0221" if raw == {} else "E0222")
    assert field in diagnostic["message"]
    assert field in diagnostic["field_path"]
    for command in (
        ["inspect", str(source), "--format", "json"],
        ["export", str(source)],
        ["render", str(source), "--render-to", str(output)],
    ):
        result = runner.invoke(cli, command)
        assert result.exit_code == EXIT_COMPILE_ERROR, result.output
    assert not output.exists()


@pytest.mark.parametrize("field", ["cycle_time", "wait_time", "changeover_time"])
def test_invalid_duration_units_stop_validated_consumers(tmp_path, field):
    source = tmp_path / "invalid-unit.flo"
    source.write_text(
        _source({"cycle_time": _profile(1, "min"), field: _profile(1, "fortnight")})
    )
    output = tmp_path / "invalid.svg"
    runner = CliRunner()
    for command in (
        ["validate", str(source)],
        ["inspect", str(source), "--format", "json"],
        ["export", str(source)],
        ["render", str(source), "--render-to", str(output)],
    ):
        result = runner.invoke(cli, command)
        assert result.exit_code == EXIT_VALIDATION_ERROR, result.output
        assert "E1303" in result.output
    assert not output.exists()


@pytest.mark.parametrize(("zero", "value"), [(False, None), (True, 0), (True, 0.0)])
@pytest.mark.parametrize("density", ["full", "compact"])
def test_omitted_and_measured_zero_survive_export_inspection_and_svg(
    tmp_path, zero, value, density
):
    measurements = (
        {
            key: _profile(value, "min")
            for key in ("cycle_time", "wait_time", "changeover_time")
        }
        if zero
        else {}
    )
    source = tmp_path / "timing.flo"
    source.write_text(_source(measurements))
    runner = CliRunner()
    export = runner.invoke(cli, ["export", str(source)])
    assert export.exit_code == 0, export.output
    node = next(
        node for node in json.loads(export.stdout)["nodes"] if node["id"] == "work"
    )
    assert {key: node.get(key) for key in measurements} == measurements
    inspect = runner.invoke(cli, ["inspect", str(source), "--format", "json"])
    assert inspect.exit_code == 0, inspect.output
    result = json.loads(inspect.stdout)
    assert result["timing_complete"] is zero
    assert result["modeled_lead_time_seconds"] == (0 if zero else None)
    assert result["declared_totals"]["cycle_time_seconds"] == (0 if zero else None)
    assert json.dumps(result, allow_nan=False)
    svg = runner.invoke(cli, ["render", str(source), "--sppm-label-density", density])
    assert svg.exit_code == 0, svg.output
    _assert_zero_labels(svg.output, value, zero)


def _assert_zero_labels(svg, value, zero):
    amount = value if zero else 0
    for label in (f"P/T: {amount} min", "W/T: 0 min", f"S/T: {amount} min"):
        assert (label in svg) is zero
    assert ("Modeled Lead Time: 0 min" in svg) is zero
    for label in ("P/T: ?", "W/T: ?", "S/T: ?"):
        assert (label in svg) is not zero


@pytest.mark.parametrize(
    ("value", "unit", "minutes"),
    [(30, "s", 0.5), (2, "m", 2), (2, "min", 2), (0.5, "hr", 30), (0.25, "d", 360)],
)
def test_queue_wait_units_agree_between_source_analysis_and_display(
    tmp_path, value, unit, minutes
):
    source = tmp_path / "units.flo"
    source.write_text(
        _source(
            {"cycle_time": _profile(1, "min")},
            queue={"wait_time": _profile(value, unit)},
        )
    )
    runner = CliRunner()
    inspect = runner.invoke(cli, ["inspect", str(source), "--format", "json"])
    assert inspect.exit_code == 0, inspect.output
    result = json.loads(inspect.stdout)
    assert result["declared_totals"]["wait_time_seconds"] == minutes * 60
    assert result["modeled_lead_time_seconds"] == minutes * 60 + 60
    svg = runner.invoke(cli, ["render", str(source)])
    assert svg.exit_code == 0, svg.output
    assert f"W/T: {minutes:g} min" in svg.output


@pytest.mark.parametrize(
    ("unit", "seconds"),
    [("s", 0.5), ("m", 30), ("min", 30), ("hr", 1800), ("d", 43200)],
)
def test_duration_migration_preserves_authored_exchange_and_operation_reports(
    unit, seconds
):
    measurements = {
        field: _profile(0.5, unit)
        for field in ("cycle_time", "wait_time", "changeover_time")
    }
    queue_measurement = _profile(0.5, unit)
    source = _source(measurements, queue={"wait_time": queue_measurement})
    validated = api.validate(source)
    assert validated.ok and not validated.report.diagnostics
    exported = api.export(source)
    assert exported.ok and not exported.report.diagnostics
    nodes = {node["id"]: node for node in json.loads(exported.value)["nodes"]}
    assert all(nodes["work"][field] == value for field, value in measurements.items())
    assert nodes["queue"]["wait_time"] == queue_measurement

    runner = CliRunner()
    inspected = runner.invoke(
        cli,
        ["inspect", "-", "--format", "json", "--diagnostics-format", "json"],
        input=source,
    )
    assert inspected.exit_code == 0
    analysis = json.loads(inspected.stdout)
    assert analysis["modeled_lead_time_seconds"] == seconds * 4
    assert analysis["declared_totals"]["wait_time_seconds"] == seconds * 2
    assert json.loads(inspected.stderr) == validated.report.as_dict()
    rendered = runner.invoke(
        cli, ["render", "-", "--diagnostics-format", "json"], input=source
    )
    assert rendered.exit_code == 0 and "<svg" in rendered.stdout
    assert json.loads(rendered.stderr) == validated.report.as_dict()


def test_partial_wait_evidence_is_shown_with_unavailable_lead_time(tmp_path):
    source = tmp_path / "partial.flo"
    source.write_text(_source({"wait_time": _profile(2, "min")}))
    runner = CliRunner()
    inspect = runner.invoke(cli, ["inspect", str(source), "--format", "json"])
    assert inspect.exit_code == 0, inspect.output
    payload = json.loads(inspect.stdout)
    assert payload["declared_totals"]["wait_time_seconds"] == 120
    assert payload["modeled_lead_time_seconds"] is None
    svg = runner.invoke(cli, ["render", str(source)])
    assert svg.exit_code == 0, svg.output
    assert "Waiting Time: 2 min" in svg.output
    assert "Lead Time: Unavailable" in svg.output
    assert "P/T: 0" not in svg.output


def test_valid_cyclic_zero_timing_is_unavailable_rather_than_missing(tmp_path):
    model = yaml.safe_load(_source({"cycle_time": _profile(0, "min")}))
    model["steps"].insert(2, {"id": "check", "name": "Recheck?", "kind": "decision"})
    model["transitions"] = [
        {"source": "start", "target": "work"},
        {"source": "work", "target": "check"},
        {"source": "check", "target": "end", "outcome": "pass"},
        {"source": "check", "target": "work", "outcome": "fail", "rework": {}},
    ]
    source = tmp_path / "cycle.flo"
    source.write_text(yaml.safe_dump(model))
    runner = CliRunner()
    result = runner.invoke(cli, ["inspect", str(source), "--format", "json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["timing_complete"]
    assert payload["declared_totals"]["cycle_time_seconds"] == 0
    assert payload["missing_timing_node_ids"] == []
    assert payload["modeled_lead_time_seconds"] is None
    assert [item["code"] for item in payload["diagnostics"]] == [
        "timing-cycle-unsupported"
    ]
    rendered = runner.invoke(cli, ["render", str(source)])
    assert rendered.exit_code == 0, rendered.output
    assert "Lead Time: Unavailable" in rendered.output
    assert "P/T: 0 min" in rendered.output


_SELECTED_DURATION_SCOPES = [
    "cycle_time",
    "wait_time",
    "changeover_time",
    "queue_wait",
    "lead_time",
]
_INVALID_SELECTED_RESULTS = [
    pytest.param({"method": "mean", "value": "5", "unit": "min"}, id="numeric-text"),
    pytest.param({"method": "mode", "value": [1, 2], "unit": "min"}, id="non-scalar"),
    pytest.param({"method": "mean", "value": 1, "unit": "kg"}, id="non-duration-unit"),
    pytest.param(
        {"method": "mean", "value": 1e308, "unit": "d"}, id="seconds-overflow"
    ),
]


def _source_with_selected_profile(scope, profile):
    model = yaml.safe_load(
        _source(
            {
                field: _profile(0, "min")
                for field in ("cycle_time", "wait_time", "changeover_time")
            }
        )
    )
    if scope == "lead_time":
        model["process"][scope] = profile
    elif scope == "queue_wait":
        model["steps"].insert(1, {"id": "queue", "kind": "queue", "wait_time": profile})
    else:
        model["steps"][1][scope] = profile
        if scope == "wait_time":
            model["steps"].insert(
                1,
                {
                    "id": "queue",
                    "kind": "queue",
                    "wait_time": {"ref": "work.wait_time"},
                },
            )
    model["transitions"] = [
        {"source": a["id"], "target": b["id"]} for a, b in pairwise(model["steps"])
    ]
    return yaml.safe_dump(model, sort_keys=False)


@pytest.mark.parametrize("scope", _SELECTED_DURATION_SCOPES)
@pytest.mark.parametrize("selector", ["primary", "analysis_input"])
@pytest.mark.parametrize("invalid", _INVALID_SELECTED_RESULTS)
def test_invalid_selected_duration_stops_all_validated_consumers(
    tmp_path, scope, selector, invalid
):
    profile = _profile(1, "min")
    profile["results"]["invalid"] = invalid
    profile[selector] = "invalid"
    source = _source_with_selected_profile(scope, profile)
    expected = api.validate(source, source_path="-").report
    assert expected.error_count == 1
    diagnostic = expected.diagnostics[0]
    assert diagnostic.code == "E1303" and diagnostic.stage == "validate"
    assert selector in diagnostic.message
    field = "wait_time" if scope == "queue_wait" else scope
    assert diagnostic.field_path.endswith(field)
    assert diagnostic.line is not None
    assert diagnostic.excerpt.strip().removeprefix("- ") == f"{field}:"
    for operation in (api.inspect, api.export):
        result = operation(source, source_path="-")
        assert not result.ok and result.value is None
        assert result.report == expected
    output = tmp_path / "invalid.svg"
    for command in ("validate", "inspect", "export", "render"):
        args = [command, "-", "--diagnostics-format", "json"]
        if command == "inspect":
            args += ["--format", "json"]
        if command == "render":
            args += ["--render-to", str(output)]
        result = CliRunner().invoke(cli, args, input=source)
        assert result.exit_code == EXIT_VALIDATION_ERROR, result.output
        assert result.stdout == ""
        assert json.loads(result.stderr) == json.loads(json.dumps(expected.as_dict()))
    assert not output.exists()


@pytest.mark.parametrize("scope", _SELECTED_DURATION_SCOPES)
@pytest.mark.parametrize("invalid", _INVALID_SELECTED_RESULTS)
def test_invalid_primary_without_analysis_input_is_rejected(scope, invalid):
    profile = {
        "basis": "observed",
        "results": {"display": invalid},
        "primary": "display",
    }
    result = api.validate(_source_with_selected_profile(scope, profile))
    assert not result.ok
    assert result.report.diagnostics[0].code == "E1303"
    assert "primary" in result.report.diagnostics[0].message


@pytest.mark.parametrize("scope", _SELECTED_DURATION_SCOPES)
def test_distinct_selector_roles_and_unselected_statistics_survive_validation(scope):
    from flo.process.analysis import analyze_process_timing

    profile = _profile(30, "s")
    profile["results"].update(
        {
            "display": {"method": "median", "value": 2, "unit": "min"},
            "modes": {"method": "mode", "value": [1, 2], "unit": "min"},
            "n": {"method": "count", "value": 5, "unit": "cases"},
        }
    )
    profile["primary"] = "display"
    source = _source_with_selected_profile(scope, profile)
    validated = api.validate(source)
    assert validated.ok, validated.diagnostics
    analysis = analyze_process_timing(validated.value)
    # Supplied process evidence must never be substituted into a modeled total.
    assert analysis.modeled_lead_time_seconds == (0 if scope == "lead_time" else 30)
    exported = api.export(source)
    assert exported.ok
    payload = json.loads(exported.value)
    if scope == "lead_time":
        preserved = payload["process"][scope]
    else:
        node_id = "queue" if scope == "queue_wait" else "work"
        field = "wait_time" if scope == "queue_wait" else scope
        preserved = next(n for n in payload["nodes"] if n["id"] == node_id)[field]
    assert preserved == profile
    rendered = CliRunner().invoke(cli, ["render", "-"], input=source)
    assert rendered.exit_code == 0, rendered.output
    if scope != "lead_time":
        label = {
            "cycle_time": "P/T",
            "changeover_time": "S/T",
            "wait_time": "W/T",
            "queue_wait": "W/T",
        }[scope]
        assert f"{label}: 2 min" in rendered.stdout


@pytest.mark.parametrize("scope", _SELECTED_DURATION_SCOPES)
@pytest.mark.parametrize("explicit_null", [False, True])
def test_primary_only_profile_does_not_invent_an_analysis_selection(
    scope, explicit_null
):
    from flo.process.analysis import analyze_process_timing

    profile = _profile(0, "min")
    profile.pop("analysis_input")
    if explicit_null:
        profile["analysis_input"] = None
    source = _source_with_selected_profile(scope, profile)
    validated = api.validate(source)
    assert validated.ok, validated.diagnostics
    analysis = analyze_process_timing(validated.value)
    assert analysis.modeled_lead_time_seconds == (0 if scope == "lead_time" else None)
    payload = json.loads(api.export(source).value)
    if scope == "lead_time":
        assert payload["process"][scope] == profile
    else:
        node_id = "queue" if scope == "queue_wait" else "work"
        field = "wait_time" if scope == "queue_wait" else scope
        assert next(n for n in payload["nodes"] if n["id"] == node_id)[field] == profile


@pytest.mark.parametrize("scope", ["cycle_time", "lead_time"])
def test_selected_duration_error_keeps_included_evidence_provenance(tmp_path, scope):
    profile = _profile(1, "min")
    profile["results"]["display"] = {
        "method": "mean",
        "value": "invalid",
        "unit": "min",
    }
    profile["primary"] = "display"
    model = yaml.safe_load(
        _source(
            {
                field: _profile(0, "min")
                for field in ("cycle_time", "wait_time", "changeover_time")
            }
        )
    )
    if scope == "lead_time":
        fragment = {"process": {scope: profile}}
    else:
        work = model["steps"].pop(1)
        work[scope] = profile
        fragment = {"steps": [work]}
    model["includes"] = ["evidence.flo"]
    evidence = tmp_path / "evidence.flo"
    evidence.write_text(yaml.safe_dump(fragment, sort_keys=False))
    root = tmp_path / "process.flo"
    content = yaml.safe_dump(model, sort_keys=False)
    root.write_text(content)
    expected = api.validate(content, source_path=str(root)).report
    diagnostic = expected.diagnostics[0]
    assert diagnostic.code == "E1303" and diagnostic.stage == "validate"
    assert diagnostic.source == str(evidence)
    assert diagnostic.field_path.endswith(scope)
    assert diagnostic.excerpt.strip() == f"{scope}:"
    assert diagnostic.include_chain == (str(root), str(evidence))
    for operation in (api.inspect, api.export):
        assert operation(content, source_path=str(root)).report == expected
    command = CliRunner().invoke(
        cli, ["validate", str(root), "--diagnostics-format", "json"]
    )
    assert command.exit_code == EXIT_VALIDATION_ERROR
    assert json.loads(command.stderr) == json.loads(json.dumps(expected.as_dict()))
