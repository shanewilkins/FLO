"""Waiting references preserve the same step identifiers accepted by source."""

import json

import jsonschema
import pytest
import yaml

from flo import api
from flo.process.contracts import CanonicalIRContract
from flo.process.ir import validate_ir
from flo.source import compile_adapter, parse_adapter
from flo.source.models import SourceDocument


def _source(identifier):
    profile = {
        "basis": "observed",
        "results": {"mean": {"method": "mean", "value": 1, "unit": "min"}},
        "primary": "mean",
        "analysis_input": "mean",
    }
    return {
        "spec_version": "0.1",
        "process": {"id": "references", "name": "References"},
        "steps": [
            {"id": "start", "kind": "start"},
            {
                "id": "queue",
                "kind": "queue",
                "wait_time": {"ref": f"{identifier}.wait_time"},
            },
            {"id": identifier, "kind": "task", "wait_time": profile},
            {"id": "end", "kind": "end"},
        ],
    }


@pytest.mark.parametrize(
    "identifier",
    [
        "révision",
        "生产",
        "work.stage",
        "work / stage",
        "work:stage",
        "  work  ",
        "work\nstage",
    ],
)
def test_supported_step_ids_resolve_and_round_trip_without_slugging(identifier):
    source = _source(identifier)
    jsonschema.validate(source, SourceDocument.model_json_schema())
    text = yaml.safe_dump(source)
    process = compile_adapter(parse_adapter(text))
    validate_ir(process)
    assert process.nodes[2].id == identifier
    result = api.export(text)
    assert result.ok, result.diagnostics
    payload = json.loads(result.value)
    assert payload["nodes"][1]["wait_time"] == {"ref": f"{identifier}.wait_time"}
    assert payload["nodes"][2]["id"] == identifier
    CanonicalIRContract.model_validate(payload)
    jsonschema.validate(payload, CanonicalIRContract.model_json_schema())


@pytest.mark.parametrize(
    "reference", ["", "work", ".wait_time", " .wait_time", 123, None]
)
def test_malformed_reference_reports_authored_ref_instead_of_profile_basis(reference):
    source = _source("work")
    source["steps"][1]["wait_time"] = {"ref": reference}
    result = api.validate(yaml.safe_dump(source), source_path="references.flo")
    assert not result.ok
    diagnostic = result.diagnostics[0]
    assert diagnostic.code == "E0222"
    assert diagnostic.field_path == "steps[1].wait_time.ref"
    assert "<step-id>.<measurement-field>" in diagnostic.message
    assert "basis" not in diagnostic.message
    assert diagnostic.line is not None


@pytest.mark.parametrize(
    "reference,reason",
    [("missing.wait_time", "unknown"), ("work.cycle_time", "work step's wait_time")],
)
def test_well_formed_references_still_fail_their_domain_rule(reference, reason):
    source = _source("work")
    source["steps"][1]["wait_time"] = {"ref": reference}
    result = api.validate(yaml.safe_dump(source))
    assert not result.ok
    assert result.diagnostics[0].code == "E1507"
    assert reason in result.diagnostics[0].message
