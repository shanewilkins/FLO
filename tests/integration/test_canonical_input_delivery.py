"""Validated consumers reject malformed compiler-produced canonical values."""

import json
from copy import deepcopy

import pytest
import yaml
from click.testing import CliRunner

from flo import api
from flo.app.cli import cli
from flo.process.ir._internal_shape import ir_from_internal_dict, ir_to_internal_dict
from flo.source import compile_adapter


def _profile(value=0):
    return {
        "basis": "observed",
        "results": {"mean": {"method": "mean", "value": value, "unit": "min"}},
        "primary": "mean",
        "analysis_input": "mean",
    }


def _source(node_id):
    return {
        "spec_version": "0.1",
        "process": {"id": "integrity", "name": "Integrity", "lead_time": _profile()},
        "steps": [
            {"id": "start", "kind": "start"},
            {
                "id": node_id,
                "kind": "task",
                "cycle_time": _profile(),
                "wait_time": _profile(),
                "changeover_time": _profile(),
                "consumes": [],
                "produces": [],
                "performed_by": [],
                "uses": [],
            },
            {"id": "end", "kind": "end"},
        ],
        "transitions": [
            {"source": "start", "target": node_id, "handoff": {}, "rework": {}},
            {"source": node_id, "target": "end"},
        ],
    }


@pytest.mark.parametrize(
    "field,value,code",
    [
        *[
            (field, False, "E1310")
            for field in ("consumes", "produces", "performed_by", "uses")
        ],
        *[
            (field, ["item", 2], "E1311")
            for field in ("consumes", "produces", "performed_by", "uses")
        ],
        *[
            (field, False, "E1301")
            for field in ("cycle_time", "wait_time", "changeover_time", "lead_time")
        ],
        *[(field, False, "E1401") for field in ("handoff", "rework")],
    ],
)
@pytest.mark.parametrize("node_id", ["route", "cycle_time"])
def test_invalid_canonical_producer_output_stops_every_validated_consumer(
    monkeypatch, tmp_path, field, value, code, node_id
):
    # Legal step IDs can coincide with field names; diagnostics must still
    # identify the violated field rather than a word inside an endpoint ID.
    model = _source(node_id)
    payload = ir_to_internal_dict(compile_adapter(model))
    owner = (
        payload
        if field == "lead_time"
        else payload["edges"][0]
        if field in {"handoff", "rework"}
        else payload["nodes"][1]
    )
    owner[field] = value
    # Exercise the real canonical loader and validator; substitute only the
    # compiler producer so source-shape checks cannot mask constructor loss.
    monkeypatch.setattr(
        "flo.app.compile_adapter",
        lambda _source: ir_from_internal_dict(deepcopy(payload)),
    )
    calls = []

    def forbidden_consumer(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("Malformed canonical data reached a consumer")

    for target in (
        "flo.api.inspect_process_model",
        "flo.api.export_ir",
        "flo.app._run_inspect_output",
        "flo.app._run_export_output",
        "flo.app._run_render_output",
        "flo.app.timing_diagnostic_report",
        "flo.api.timing_diagnostic_report",
    ):
        monkeypatch.setattr(target, forbidden_consumer)
    content = yaml.safe_dump(model, sort_keys=False)
    expected = api.validate(content, source_path="-").report
    assert expected.error_count == 1
    diagnostic = expected.diagnostics[0]
    assert diagnostic.code == code and diagnostic.stage == "validate"
    assert diagnostic.field_path.endswith(field)
    assert "pydantic" not in diagnostic.message.lower()
    for operation in (api.validate, api.inspect, api.export):
        result = operation(content, source_path="-")
        assert not result.ok and result.value is None
        assert result.report == expected
    output = tmp_path / "invalid.svg"
    for command in ("validate", "inspect", "export", "render"):
        args = [command, "-", "--diagnostics-format", "json"]
        if command == "inspect":
            args += ["--format", "json"]
        if command == "render":
            args += ["--render-to", str(output)]
        result = CliRunner().invoke(cli, args, input=content)
        assert result.exit_code == 4, result.output
        assert result.stdout == ""
        assert json.loads(result.stderr) == json.loads(json.dumps(expected.as_dict()))
    assert not output.exists()
    assert calls == []
