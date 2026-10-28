"""Complete relation evidence validation at source and canonical boundaries."""

from copy import deepcopy

import pytest
import yaml

from flo import api
from flo.errors import ValidationError
from flo.process.ir import validate_ir
from flo.source import compile_adapter, parse_adapter
from tests.integration.test_phase3_evidence import model

INVALID = [
    ("handoff", "type", "unknown"),
    ("handoff", "extensions", []),
    ("handoff", "extensions", {"example:value": float("nan")}),
    ("rework", "reason", " "),
    ("rework", "note", []),
    ("rework", "extensions", {"example:nested": [float("inf")]}),
    ("rework", "extensions", []),
    ("frequency", "basis", "unknown"),
    ("frequency", "numerator", True),
    ("frequency", "numerator", -1),
    ("frequency", "numerator", float("nan")),
    ("frequency", "numerator", 10**400),
    ("frequency", "numerator", 11),
    ("frequency", "denominator", 0),
    ("frequency", "denominator", True),
    ("frequency", "denominator", 2.5),
    ("frequency", "denominator", 10**400),
    ("frequency", "observation_unit", " "),
    ("frequency", "evidence_ref", " "),
    ("frequency", "evidence_ref", []),
]


def patch(data, section, field, value):
    edge = data["transitions"][1]
    target = edge["rework"]["frequency"] if section == "frequency" else edge[section]
    target[field] = value


@pytest.mark.parametrize("section,field,value", INVALID)
def test_invalid_relation_evidence_stops_every_source_consumer(section, field, value):
    data = model()
    patch(data, section, field, value)
    source = yaml.safe_dump(data)
    expected = api.validate(source)
    assert not expected.ok
    assert expected.diagnostics[0].code in {"E0222", "E0209"}
    for operation in (api.inspect, api.export):
        result = operation(source)
        assert not result.ok and result.value is None
        assert result.report == expected.report


@pytest.mark.parametrize("section,field,value", INVALID)
def test_invalid_relation_evidence_survives_construction_and_fails_ir_validation(
    section, field, value
):
    data = model()
    process = compile_adapter(parse_adapter(yaml.safe_dump(data)))
    invalid = deepcopy(data)
    patch(invalid, section, field, value)
    relation_field = "rework" if section == "frequency" else section
    setattr(process.edges[1], relation_field, invalid["transitions"][1][relation_field])
    with pytest.raises(ValidationError, match="E1401"):
        validate_ir(process)


@pytest.mark.parametrize(
    "basis", ["observed", "simulated", "estimated", "planned", "target"]
)
@pytest.mark.parametrize("numerator", [0, 2.5, 10])
def test_valid_frequency_retains_basis_population_and_extensions(basis, numerator):
    data = model()
    frequency = data["transitions"][1]["rework"]["frequency"]
    frequency.update(basis=basis, numerator=numerator)
    result = api.validate(yaml.safe_dump(data))
    assert result.ok, result.diagnostics
    assert result.value.edges[1].rework == data["transitions"][1]["rework"]
