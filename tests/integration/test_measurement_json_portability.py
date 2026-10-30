"""All supplied measurement evidence must survive strict JSON exchange."""

import json
from copy import deepcopy

import pytest
import yaml
from pydantic import ValidationError as ContractError

from flo import api
from flo.errors import ValidationError
from flo.process.contracts import CanonicalIRContract, MeasurementResult
from flo.process.export.json_export import ir_to_schema_json
from flo.process.ir import validate_ir
from flo.process.ir.schema_projection import ir_to_schema_dict
from flo.source import compile_adapter, parse_adapter
from tests.integration.test_measurement_evidence_preservation import model


def _process():
    return compile_adapter(parse_adapter(yaml.safe_dump(model())))


@pytest.mark.parametrize(
    "field,value",
    [
        ("value", [1, float("nan")]),
        ("value", [{"nested": [float("inf")]}]),
        ("parameters", {"nested": {"value": float("-inf")}}),
        ("parameters", {"allowed": {1, 2}}),
    ],
)
def test_unselected_invalid_evidence_fails_source_and_canonical_boundaries(
    field, value
):
    evidence = {"method": "mode", "value": [1, 2], "unit": "min", field: value}
    source = model()
    source["steps"][1]["cycle_time"]["results"]["extra"] = evidence
    for operation in (api.validate, api.export):
        result = operation(yaml.safe_dump(source), source_path="evidence.flo")
        assert not result.ok
        diagnostic = result.diagnostics[0]
        assert diagnostic.code == "E0222"
        assert diagnostic.field_path == f"steps[1].cycle_time.results.extra.{field}"
        assert "finite JSON" in diagnostic.message
        assert diagnostic.line is not None

    process = _process()
    process.nodes[1].cycle_time["results"]["extra"] = evidence
    with pytest.raises(ValidationError, match="E1301"):
        validate_ir(process)
    with pytest.raises(ContractError):
        CanonicalIRContract.model_validate(ir_to_schema_dict(process))


@pytest.mark.parametrize("value", [{1: "one"}, {"nested": (1, 2)}, {"x": b"bytes"}])
def test_parameters_reject_lossy_python_json_coercions(value):
    with pytest.raises(ContractError):
        MeasurementResult.model_validate(
            {"method": "mode", "value": [1], "unit": "min", "parameters": value}
        )


def _reject_constant(value):
    raise ValueError(f"Nonstandard JSON constant: {value}")


def test_structured_unselected_evidence_round_trips_without_coercion():
    source = model()
    evidence = {
        "method": "mode",
        "value": [0, False, None, "révision", {"nested": [1.25, -2]}],
        "unit": "min",
        "parameters": {"include": [True, None, {"label": "one"}]},
    }
    source["steps"][1]["cycle_time"]["results"]["extra"] = deepcopy(evidence)
    exported = api.export(yaml.safe_dump(source))
    assert exported.ok, exported.diagnostics
    payload = json.loads(exported.value, parse_constant=_reject_constant)
    assert payload["nodes"][1]["cycle_time"]["results"]["extra"] == evidence
    CanonicalIRContract.model_validate(payload)


@pytest.mark.parametrize("indent", [None, 2])
def test_json_encoder_defends_against_nonfinite_unvalidated_ir(indent):
    process = _process()
    process.nodes[1].cycle_time["results"]["extra"] = {
        "method": "mode",
        "value": [float("nan")],
        "unit": "min",
    }
    with pytest.raises(ValueError, match="Out of range float"):
        ir_to_schema_json(process, indent=indent)
