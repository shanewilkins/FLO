"""Lane declaration presence survives composition and canonical boundaries."""

import json
from copy import deepcopy

import pytest
import yaml
from click.testing import CliRunner

from flo import api
from flo.app.cli import cli
from flo.errors import ValidationError
from flo.process.contracts import CanonicalIRContract
from flo.process.ir._internal_shape import (
    ir_from_internal_dict,
    ir_to_internal_dict,
    ir_to_internal_json,
)
from flo.process.ir.models import IR, Edge, Node
from flo.process.ir.schema_projection import ir_to_schema_dict
from flo.process.ir.validate import ensure_schema_aligned, validate_ir
from flo.render import render_artifact
from flo.source import compile_adapter, parse_adapter

LANES = [{"id": "ops", "name": "Operations"}]
STATES = ["omitted", "null", "empty", "declared"]


def model(state="omitted", reference=None):
    document = {
        "spec_version": "0.1",
        "process": {"id": "presence", "name": "Presence"},
        "steps": [
            {"id": "s", "kind": "start"},
            {"id": "work", "kind": "task"},
            {"id": "e", "kind": "end"},
        ],
    }
    if state != "omitted":
        document["lanes"] = {"null": None, "empty": [], "declared": deepcopy(LANES)}[
            state
        ]
    if reference is not None:
        document["steps"][1]["lane"] = reference
    return document


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("reference", [None, "ops", "missing"])
def test_source_reference_resolution_depends_on_declaration_presence(state, reference):
    source = yaml.safe_dump(model(state, reference), sort_keys=False)
    result = api.validate(source)
    valid = (
        reference is None
        or state in {"omitted", "null"}
        or (state == "declared" and reference == "ops")
    )
    assert result.ok == valid
    if valid:
        assert result.value.lanes == (
            LANES if state == "declared" else [] if state == "empty" else None
        )
    else:
        diagnostic = result.report.diagnostics[0]
        assert diagnostic.code == "E1316" and diagnostic.stage == "validate"
        assert diagnostic.field_path == "steps[1].lane"


@pytest.mark.parametrize("state", STATES)
def test_presence_survives_source_internal_json_and_exchange_roundtrips(state):
    source = yaml.safe_dump(model(state), sort_keys=False)
    process = compile_adapter(parse_adapter(source))
    expected = LANES if state == "declared" else [] if state == "empty" else None
    assert process.lanes == expected
    payload = json.loads(ir_to_internal_json(process))
    assert payload["lanes"] == expected
    restored = ir_from_internal_dict(payload)
    assert restored.lanes == expected
    validate_ir(restored)
    ensure_schema_aligned(restored)
    exchange = ir_to_schema_dict(restored)
    assert ("lanes" in exchange) == (expected is not None)
    if expected is not None:
        assert exchange["lanes"] == expected
    canonical = CanonicalIRContract.model_validate(exchange)
    assert (canonical.lanes is None) == (expected is None)
    assert canonical.model_dump(exclude_none=True).get("lanes") == expected
    exported = api.export(source)
    assert exported.ok
    assert json.loads(exported.value) == exchange


@pytest.mark.parametrize("root_state", STATES)
@pytest.mark.parametrize("include_state", STATES)
def test_include_presence_is_additive_and_omission_cannot_erase_declarations(
    root_state, include_state, tmp_path
):
    document = model(root_state)
    fragment = {
        key: value for key, value in model(include_state).items() if key == "lanes"
    }
    if root_state == include_state == "declared":
        # Distinct identities prove list composition remains additive.
        fragment["lanes"] = [{"id": "support", "name": "Support"}]
    (tmp_path / "fragment.flo").write_text(yaml.safe_dump(fragment))
    document["includes"] = ["fragment.flo"]
    result = api.validate(
        yaml.safe_dump(document), source_path=str(tmp_path / "root.flo")
    )
    assert result.ok, result.diagnostics
    if root_state == include_state == "declared":
        assert result.value.lanes == [{"id": "support", "name": "Support"}, *LANES]
    elif "declared" in {root_state, include_state}:
        assert result.value.lanes == LANES
    elif "empty" in {root_state, include_state}:
        assert result.value.lanes == []
    else:
        assert result.value.lanes is None


def test_empty_declaration_keeps_included_bad_reference_location(tmp_path):
    document = model("empty")
    document["transitions"] = [
        {"source": "s", "target": "work"},
        {"source": "work", "target": "e"},
    ]
    fragment = {"steps": [document["steps"].pop(1)]}
    fragment["steps"][0]["lane"] = "missing"
    (tmp_path / "fragment.flo").write_text(yaml.safe_dump(fragment))
    document["includes"] = ["fragment.flo"]
    result = api.validate(
        yaml.safe_dump(document), source_path=str(tmp_path / "root.flo")
    )
    assert not result.ok
    diagnostic = result.report.diagnostics[0]
    assert diagnostic.code == "E1316"
    assert diagnostic.source == str(tmp_path / "fragment.flo")
    assert diagnostic.field_path == "steps[0].lane"
    assert diagnostic.line is not None


@pytest.mark.parametrize("canonical", [False, True], ids=["source", "canonical"])
def test_empty_lanes_stop_validated_consumers_without_inventing_declarations(
    canonical, monkeypatch, tmp_path
):
    document = model("omitted" if canonical else "empty", "ops")
    if canonical:
        payload = ir_to_internal_dict(compile_adapter(document))
        payload["lanes"] = []
        monkeypatch.setattr(
            "flo.app.compile_adapter", lambda _source: ir_from_internal_dict(payload)
        )
    calls = []

    def forbidden_consumer(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("Unresolved lane reached consumer")

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
    source = yaml.safe_dump(document, sort_keys=False)
    expected = api.validate(source, source_path="-").report
    assert expected.error_count == 1 and expected.diagnostics[0].code == "E1316"
    for operation in (api.validate, api.inspect, api.export):
        result = operation(source, source_path="-")
        assert not result.ok and result.value is None and result.report == expected
    output = tmp_path / "invalid.svg"
    for command in ("validate", "inspect", "export", "render"):
        args = [command, "-", "--diagnostics-format", "json"]
        if command == "inspect":
            args += ["--format", "json"]
        if command == "render":
            args += ["--render-to", str(output)]
        result = CliRunner().invoke(cli, args, input=source)
        assert result.exit_code == 4 and result.stdout == ""
        assert json.loads(result.stderr) == json.loads(json.dumps(expected.as_dict()))
    assert not output.exists() and not calls


def test_direct_ir_default_is_unspecified_and_explicit_empty_is_enforced():
    process = IR(
        name="freeform",
        nodes=[
            Node("s", "start"),
            Node("work", "task", lane="freeform"),
            Node("e", "end"),
        ],
        edges=[Edge("s", "work"), Edge("work", "e")],
    )
    assert process.lanes is None
    validate_ir(process)
    process.lanes = []
    with pytest.raises(ValidationError, match="E1316"):
        validate_ir(process)
    assert process.lanes == []


def test_inspection_and_rendering_preserve_unspecified_lane_declarations():
    source = yaml.safe_dump(model("omitted", "freeform"))
    inspected = api.inspect(source)
    assert inspected.ok
    process = api.validate(source).value
    before = ir_to_internal_dict(process)
    artifact = render_artifact(process)
    assert artifact.kind == "svg" and "<svg" in artifact.content
    assert process.lanes is None and ir_to_internal_dict(process) == before
