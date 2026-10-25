import json
from itertools import pairwise

import pytest
import yaml
from click.testing import CliRunner

from flo import api
from flo.app.cli import cli
from flo.errors import EXIT_VALIDATION_ERROR


def _source(metadata, *, queue=None):
    steps = [{"id": "start", "name": "Start", "kind": "start"}]
    if queue is not None:
        steps.append(
            {"id": "queue", "name": "Queue", "kind": "queue", "metadata": queue}
        )
    steps.extend(
        [
            {"id": "work", "name": "Work", "kind": "task", "metadata": metadata},
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
    ("raw", "code"),
    [
        (None, "E1301"),
        ({}, "E1302"),
        ({"value": True, "unit": "min"}, "E1302"),
        ({"value": -1, "unit": "min"}, "E1302"),
        ({"value": "0", "unit": "min"}, "E1302"),
        ({"value": float("nan"), "unit": "min"}, "E1302"),
        ({"value": float("inf"), "unit": "s"}, "E1302"),
        ({"value": 1e308, "unit": "d"}, "E1302"),
        ({"value": 10**400, "unit": "s"}, "E1302"),
        ({"value": 1}, "E1303"),
        ({"value": 1, "unit": "fortnight"}, "E1303"),
        ({"value": 1, "unit": "minute"}, "E1303"),
    ],
)
@pytest.mark.parametrize(
    "field",
    [
        "cycle_time",
        "wait_before",
        "crossover_time",
        "transfer_time",
        "changeover_time",
        "wait_time",
    ],
)
def test_invalid_timing_is_rejected_before_analysis_export_or_render(
    tmp_path, raw, code, field
):
    source = tmp_path / "invalid.flo"
    if field == "wait_time":
        source.write_text(
            _source({"cycle_time": {"value": 1, "unit": "min"}}, queue={field: raw})
        )
    else:
        source.write_text(
            _source({"cycle_time": {"value": 1, "unit": "min"}, field: raw})
        )
    output = tmp_path / "invalid.svg"
    runner = CliRunner()
    validation = runner.invoke(cli, ["validate", str(source), "--format", "json"])
    assert validation.exit_code == EXIT_VALIDATION_ERROR, validation.output
    diagnostic = json.loads(validation.output)
    assert diagnostic["code"] == code
    assert field in diagnostic["message"]
    assert diagnostic["field_path"].endswith(f"metadata.{field}")
    assert diagnostic["suggestion"]
    for command in (
        ["inspect", str(source), "--format", "json"],
        ["export", str(source)],
        ["render", str(source), "--render-to", str(output)],
    ):
        result = runner.invoke(cli, command)
        assert result.exit_code == EXIT_VALIDATION_ERROR, result.output
        assert code in result.output
    assert not output.exists()


@pytest.mark.parametrize(("zero", "value"), [(False, None), (True, 0), (True, 0.0)])
@pytest.mark.parametrize("density", ["full", "compact"])
def test_omitted_and_measured_zero_survive_export_inspection_and_svg(
    tmp_path, zero, value, density
):
    metadata = (
        {
            key: {"value": value, "unit": "min"}
            for key in ("cycle_time", "wait_before", "changeover_time")
        }
        if zero
        else {}
    )
    source = tmp_path / "timing.flo"
    source.write_text(_source(metadata))
    runner = CliRunner()
    export = runner.invoke(cli, ["export", str(source)])
    assert export.exit_code == 0, export.output
    node = next(
        node for node in json.loads(export.stdout)["nodes"] if node["id"] == "work"
    )
    assert node.get("metadata", {}) == metadata
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
    assert ("Lead Time: 0 min" in svg) is zero
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
            {"cycle_time": {"value": 1, "unit": "min"}},
            queue={"wait_time": {"value": value, "unit": unit}},
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
    quantity = {"value": 0.5, "unit": unit}
    metadata = {
        field: dict(quantity)
        for field in ("cycle_time", "wait_before", "crossover_time")
    }
    metadata["wait_before"]["measurement_id"] = "work-wait"
    queue_quantity = {**quantity, "measurement_id": "queue-wait"}
    source = _source(metadata, queue={"wait_time": queue_quantity})
    validated = api.validate(source)
    assert validated.ok and not validated.report.diagnostics
    exported = api.export(source)
    assert exported.ok and not exported.report.diagnostics
    nodes = {node["id"]: node for node in json.loads(exported.value)["nodes"]}
    assert nodes["work"]["metadata"] == metadata
    assert nodes["queue"]["metadata"]["wait_time"] == queue_quantity

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
    source.write_text(_source({"wait_before": {"value": 2, "unit": "min"}}))
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
    model = yaml.safe_load(_source({"cycle_time": {"value": 0, "unit": "min"}}))
    model["steps"].insert(2, {"id": "check", "name": "Recheck?", "kind": "decision"})
    model["transitions"] = [
        {"source": "start", "target": "work"},
        {"source": "work", "target": "check"},
        {"source": "check", "target": "end", "outcome": "pass"},
        {"source": "check", "target": "work", "outcome": "fail", "rework": True},
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
