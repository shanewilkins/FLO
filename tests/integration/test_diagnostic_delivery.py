"""Warning-only CLI/API/artifact parity and stable structured stderr reports."""

import io
import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from flo import api
from flo.app import run_content, run_operation
from flo.app.cli import cli, main
from flo.app.diagnostics import CommandResult
from flo.diagnostics import Diagnostic, diagnostic_report
from flo.render import render_artifact


def _profile(value, unit):
    return {
        "basis": "observed",
        "results": {
            "mean": {"method": "mean", "value": value, "unit": unit},
        },
        "primary": "mean",
        "analysis_input": "mean",
    }


def _source(*, work=None, queue=None):
    return yaml.safe_dump(
        {
            "spec_version": "0.1",
            "process": {"id": "example", "name": "Example"},
            "steps": [
                {"id": "start", "kind": "start"},
                {"id": "work", "kind": "task", **(work or {})},
                {"id": "queue", "kind": "queue", **(queue or {})},
                {"id": "end", "kind": "end"},
            ],
        },
        sort_keys=False,
    )


def _measured_source():
    return _source(
        work={
            key: _profile(0.0 if key == "wait_time" else 0, "s")
            for key in ("cycle_time", "wait_time", "changeover_time")
        },
        queue={"wait_time": _profile(0.0, "min")},
    )


def _incomplete(report):
    return [item for item in report.diagnostics if item.code == "timing-incomplete"]


def test_api_artifact_and_legacy_runner_share_one_aggregate_without_mutating_ir(capsys):
    source = _source()
    result = api.validate(source)
    assert result.ok and result.value is not None
    assert result.report.error_count == 0
    warning = _incomplete(result.report)[0]
    assert warning.details["affected_node_ids"] == ["queue", "work"]
    missing = {
        (item["node_id"], item["field"]) for item in warning.details["missing_fields"]
    }
    assert missing == {
        ("queue", "wait_time"),
        ("work", "cycle_time"),
        ("work", "wait_time"),
        ("work", "changeover_time"),
    }
    before = deepcopy(result.value)
    artifact = render_artifact(result.value, {"no_footer": True})
    assert artifact.diagnostic_report.as_dict() == result.report.as_dict()
    assert result.value == before
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""
    code, svg, warnings = run_content(source)
    assert code == 0 and "<svg" in svg
    assert warnings.count("timing-incomplete:") == 1
    assert api.export(source).ok
    assert _incomplete(api.export(source).report)[0] == warning
    inspected = api.inspect(source)
    assert inspected.ok and _incomplete(inspected.report)[0] == warning


@pytest.mark.parametrize("command", ["render", "export", "validate", "inspect"])
def test_every_command_keeps_its_payload_separate_from_the_json_report(command):
    args = [command, "-", "--diagnostics-format", "json"]
    if command == "inspect":
        args += ["--format", "json"]
    result = CliRunner().invoke(cli, args, input=_source())
    assert result.exit_code == 0, result.output
    report = json.loads(result.stderr)
    assert report["error_count"] == 0
    assert report["warning_count"] == 1
    assert len(report["diagnostics"]) == 1
    record = report["diagnostics"][0]
    assert record["code"] == "timing-incomplete"
    assert record["stage"] == "analysis.timing"
    assert record["source"] == "<stdin>"
    if command == "render":
        assert "<svg" in result.stdout and "Warning:" not in result.stdout
    elif command == "validate":
        assert result.stdout == ""
    else:
        assert json.loads(result.stdout)


@pytest.mark.parametrize("flags", [[], ["--no-footer"], ["--layout-fit", "fit-strict"]])
def test_warning_visibility_is_default_independent_of_footer_and_geometry_strictness(
    flags,
):
    result = CliRunner().invoke(cli, ["render", "-", *flags], input=_source())
    assert result.exit_code == 0
    assert result.stderr.count("Warning: timing-incomplete:") == 1
    assert "<svg" in result.stdout


def test_explicit_zero_is_measured_and_empty_json_report_is_still_emitted():
    source = _measured_source()
    result = api.validate(source)
    assert result.ok and not result.diagnostics
    cli_result = CliRunner().invoke(
        cli, ["validate", "-", "--diagnostics-format", "json"], input=source
    )
    assert cli_result.exit_code == 0
    assert json.loads(cli_result.stderr) == {
        "report_version": "0.1",
        "diagnostics": [],
        "error_count": 0,
        "warning_count": 0,
        "info_count": 0,
    }
    assert cli_result.stdout == ""


def test_omitted_optional_wait_and_setup_are_reported_without_labeling_zero_processing_missing():
    source = _source(
        work={"cycle_time": _profile(0, "min")},
        queue={"wait_time": _profile(0.0, "s")},
    )
    records = _incomplete(api.validate(source).report)
    assert len(records) == 1
    assert {item["field"] for item in records[0].details["missing_fields"]} == {
        "wait_time",
        "changeover_time",
    }


def test_invalid_declared_timing_preserves_cli_api_stage_parity():
    source = _source(work={"cycle_time": _profile(float("nan"), "s")})
    programmatic = api.validate(source, source_path="-")
    assert not programmatic.ok and programmatic.value is None
    result = CliRunner().invoke(
        cli, ["render", "-", "--diagnostics-format", "json"], input=source
    )
    assert result.exit_code == 3 and result.stdout == ""
    report = json.loads(result.stderr)
    assert report["error_count"] == 1 and report["warning_count"] == 0
    assert report["diagnostics"][0]["code"] == "E0222"
    assert report["diagnostics"][0]["stage"] == "compile"
    assert report == json.loads(json.dumps(programmatic.report.as_dict()))


def test_source_json_record_and_explicit_operation_envelope_both_remain_available():
    source = _source(work={"cycle_time": _profile(-1, "s")})
    legacy = CliRunner().invoke(
        cli, ["validate", "-", "--format", "json"], input=source
    )
    assert legacy.exit_code == 3
    assert json.loads(legacy.stderr)["code"] == "E0222"
    explicit = CliRunner().invoke(
        cli,
        ["validate", "-", "--format", "json", "--diagnostics-format", "json"],
        input=source,
    )
    assert json.loads(explicit.stderr)["diagnostics"][0]["code"] == "E0222"


def test_strict_geometry_failure_retains_render_exit_status():
    result = CliRunner().invoke(
        cli,
        [
            "render",
            "-",
            "--layout-width",
            "1px",
            "--layout-overflow",
            "error",
            "--diagnostics-format",
            "json",
        ],
        input=_source(),
    )
    assert result.exit_code == 5 and result.stdout == ""
    report = json.loads(result.stderr)
    assert report["error_count"] == 1
    assert report["diagnostics"][0]["stage"] == "render"


def test_write_failure_emits_one_final_report_with_prior_warnings(monkeypatch):
    monkeypatch.setattr("flo.app.io.write_output", lambda *_: (5, "write failed"))
    result = CliRunner().invoke(
        cli,
        ["export", "-", "-o", "output.json", "--diagnostics-format", "json"],
        input=_source(),
    )
    assert result.exit_code == 5
    report = json.loads(result.stderr)
    assert report["error_count"] == report["warning_count"] == 1
    assert any(item["stage"] == "write_output" for item in report["diagnostics"])


def test_implicit_entrypoint_accepts_the_same_report_switch(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(_source()))
    assert main(["-", "--export", "json", "--diagnostics-format", "json"]) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out)["process"]["id"] == "example"
    assert json.loads(captured.err)["warning_count"] == 1


def test_info_is_available_in_json_and_verbose_mode_but_not_default_stderr(monkeypatch):
    finding = Diagnostic(
        "timing-multiple-paths", "info", "Alternative paths", "analysis.timing"
    )
    monkeypatch.setattr(
        "flo.app.run_operation",
        lambda *_args, **_kwargs: CommandResult(0, "", diagnostic_report((finding,))),
    )
    default = CliRunner().invoke(cli, ["validate", "-"], input=_source())
    assert default.stderr == ""
    verbose = CliRunner().invoke(cli, ["validate", "-", "--verbose"], input=_source())
    assert "Info: timing-multiple-paths" in verbose.stderr
    structured = CliRunner().invoke(
        cli, ["validate", "-", "--diagnostics-format", "json"], input=_source()
    )
    assert json.loads(structured.stderr)["info_count"] == 1


def test_report_is_stable_when_discovery_order_changes():
    source = yaml.safe_load(_source())
    source["transitions"] = [
        {"source": "start", "target": "work"},
        {"source": "work", "target": "queue"},
        {"source": "queue", "target": "end"},
    ]
    original = run_operation(yaml.safe_dump(source), command="validate").report
    source["steps"].reverse()
    reordered = run_operation(yaml.safe_dump(source), command="validate").report
    assert reordered.as_dict() == original.as_dict()


def test_complete_book_has_no_missing_timing_and_starter_has_one_warning():
    book = Path("examples/reference/book_washnfold.flo").read_text()
    report = run_operation(book, command="validate").report
    assert _incomplete(report) == []
    assert len(_incomplete(api.validate(_source()).report)) == 1
