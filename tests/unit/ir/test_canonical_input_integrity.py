"""Malformed canonical data must survive construction until explicit rejection."""

import json
from copy import deepcopy

import pytest

from flo.errors import ValidationError
from flo.process.ir._internal_shape import ir_from_internal_dict, ir_to_internal_json
from flo.process.ir.models import IR, Edge, Node
from flo.process.ir.schema_projection import ir_to_schema_dict
from flo.process.ir.validate import validate_ir

RELATION_CASES = [
    pytest.param(
        field,
        value,
        "E1310" if not isinstance(value, list) else "E1311",
        id=f"{field}-{label}",
    )
    for field in ("consumes", "produces", "performed_by", "uses")
    for label, value in (
        ("scalar", "item"),
        ("false", False),
        ("empty-object", {}),
        ("null", None),
        ("number-member", [1]),
        ("blank-member", [""]),
    )
]
MEASUREMENT_CASES = [
    pytest.param(field, value, "E1301", id=f"{field}-{label}")
    for field in ("cycle_time", "wait_time", "changeover_time")
    for label, value in (
        ("scalar", 3),
        ("false", False),
        ("empty-list", []),
        ("empty-object", {}),
    )
]
EDGE_CASES = [
    pytest.param(field, value, "E1401", id=f"{field}-{label}")
    for field in ("handoff", "rework")
    for label, value in (
        ("true", True),
        ("false", False),
        ("zero", 0),
        ("scalar", "yes"),
        ("empty-list", []),
        ("unknown-field", {"unsupported": True}),
    )
]


def _process(field, value):
    node = Node(
        id="work",
        type="task",
        **({field: value} if field not in {"handoff", "rework", "lead_time"} else {}),
    )
    edge = Edge(
        source="start",
        target="work",
        **({field: value} if field in {"handoff", "rework"} else {}),
    )
    return IR(
        name="Input integrity",
        nodes=[Node(id="start", type="start"), node, Node(id="end", type="end")],
        edges=[edge, Edge(source="work", target="end")],
        **({"lead_time": value} if field == "lead_time" else {}),
    )


def _value(process, field):
    owner = (
        process.edges[0]
        if field in {"handoff", "rework"}
        else process
        if field == "lead_time"
        else process.nodes[1]
    )
    return getattr(owner, field)


@pytest.mark.parametrize(
    "field,value,code", [*RELATION_CASES, *MEASUREMENT_CASES, *EDGE_CASES]
)
def test_invalid_canonical_values_survive_constructor_and_roundtrip_then_fail_validation(
    field, value, code
):
    process = _process(field, value)
    assert _value(process, field) == value
    assert type(_value(process, field)) is type(value)
    restored = ir_from_internal_dict(json.loads(ir_to_internal_json(process)))
    assert _value(restored, field) == value
    assert type(_value(restored, field)) is type(value)
    for candidate in (process, restored):
        with pytest.raises(ValidationError, match=code):
            validate_ir(candidate)
    # Exchange projection also must not conceal false/empty malformed lists.
    projected = ir_to_schema_dict(process)
    owner = (
        projected["edges"][0]
        if field in {"handoff", "rework"}
        else projected["nodes"][1]
    )
    assert owner[field] == value
    assert type(owner[field]) is type(value)


@pytest.mark.parametrize("value", [False, "invalid", [], {}])
def test_invalid_process_measurement_is_preserved_and_rejected(value):
    process = _process("lead_time", value)
    assert _value(process, "lead_time") == value
    restored = ir_from_internal_dict(json.loads(ir_to_internal_json(process)))
    assert _value(restored, "lead_time") == value
    for candidate in (process, restored):
        with pytest.raises(ValidationError, match="E1301"):
            validate_ir(candidate)


def test_constructor_detaches_valid_and_invalid_mutable_fields_from_caller():
    raw = {"consumes": ["item", 2], "cycle_time": {"invalid": []}}
    before = deepcopy(raw)
    node = Node(id="work", type="task", **raw)
    raw["consumes"].clear()
    raw["cycle_time"]["invalid"].append("changed")
    assert node.consumes == before["consumes"]
    assert node.cycle_time == before["cycle_time"]
    relation = {"reason": "Correct output", "extensions": {"evidence": []}}
    edge = Edge(source="start", target="work", rework=relation)
    relation["extensions"]["evidence"].append("changed")
    assert edge.rework == {"reason": "Correct output", "extensions": {"evidence": []}}


@pytest.mark.parametrize("zero", [0, 0.0])
def test_valid_semantics_and_measured_zero_roundtrip_without_coercion(zero):
    profile = {
        "basis": "observed",
        "results": {"mean": {"method": "mean", "value": zero, "unit": "min"}},
        "primary": "mean",
        "analysis_input": "mean",
    }
    process = IR(
        name="Valid canonical data",
        nodes=[
            Node(id="start", type="start"),
            Node(
                id="work",
                type="task",
                consumes=["item"],
                produces=["item"],
                performed_by=["person"],
                uses=["equipment"],
                cycle_time=profile,
                wait_time=profile,
                changeover_time=profile,
            ),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="work", handoff={}),
            Edge(
                source="work",
                target="end",
                rework={
                    "reason": "Correct output",
                    "frequency": {
                        "basis": "observed",
                        "numerator": 0,
                        "denominator": 10,
                        "observation_unit": "cases",
                    },
                },
            ),
        ],
        lead_time=profile,
        items=[{"id": "item", "name": "Item", "kind": "information"}],
        resources=[
            {"id": "person", "name": "Person", "kind": "person"},
            {"id": "equipment", "name": "Equipment", "kind": "equipment"},
        ],
    )
    restored = ir_from_internal_dict(json.loads(ir_to_internal_json(process)))
    assert restored == process
    for candidate in (process, restored):
        validate_ir(candidate)
        for field in ("cycle_time", "wait_time", "changeover_time"):
            assert type(
                getattr(candidate.nodes[1], field)["results"]["mean"]["value"]
            ) is type(zero)
        assert type(candidate.lead_time["results"]["mean"]["value"]) is type(zero)
    assert ir_to_schema_dict(restored) == ir_to_schema_dict(process)


def test_omitted_semantics_remain_omitted_and_empty_relations_remain_valid():
    process = _process("cycle_time", None)
    restored = ir_from_internal_dict(json.loads(ir_to_internal_json(process)))
    assert restored.nodes[1].cycle_time is None
    assert restored.nodes[1].wait_time is None
    assert restored.lead_time is None
    assert restored.nodes[1].consumes == []
    assert restored.edges[0].handoff is None
    assert restored.edges[0].rework is None
    validate_ir(restored)
