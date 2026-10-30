"""Schema/runtime parity for the local shapes audited at final acceptance."""

from copy import deepcopy

import pytest
import yaml
from jsonschema import Draft202012Validator
from pydantic import ValidationError as ContractError

from flo import api
from flo.errors import ValidationError
from flo.process.contracts import CanonicalIRContract
from flo.process.ir.models import IR, Edge, Node
from flo.process.ir.schema_projection import ir_to_schema_dict
from flo.process.ir.validate import validate_ir
from flo.source.models import SourceDocument


def document():
    return {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process"},
        "steps": [
            {"id": "start", "kind": "start"},
            {"id": "work", "kind": "task"},
            {"id": "end", "kind": "end"},
        ],
    }


@pytest.mark.parametrize(
    "collection,kind",
    [("items", "material"), ("resources", "person"), ("locations", None)],
)
@pytest.mark.parametrize("grouped", [False, True])
@pytest.mark.parametrize("defect", ["unknown", "quantity", "null"])
def test_authored_schema_and_compiler_reject_malformed_entities(
    collection, kind, grouped, defect
):
    data = document()
    entry = {"id": "a", "name": "A", **({"kind": kind} if kind else {})}
    if defect == "unknown":
        entry["unsupported"] = True
    elif defect == "quantity":
        entry["quantity"] = {"kind": "count", "value": True}
    value = {"group": {"entries": [entry]}} if grouped else [entry]
    data["process"][collection] = None if defect == "null" else value
    before = deepcopy(data)
    assert not Draft202012Validator(SourceDocument.model_json_schema()).is_valid(data)
    result = api.compile(yaml.safe_dump(data, sort_keys=False))
    assert not result.ok
    assert result.diagnostics[0].stage == "compile"
    assert result.diagnostics[0].field_path.startswith(f"process.{collection}")
    assert not any(
        token in result.diagnostics[0].field_path
        for token in ("function-", "EntityGroup", "list[", "ItemContract")
    )
    assert data == before


@pytest.mark.parametrize("field", ["cycle_time", "changeover_time", "lead_time"])
def test_only_waiting_fields_accept_references_at_source_and_canonical_boundaries(
    field,
):
    data = document()
    target = data["process"] if field == "lead_time" else data["steps"][1]
    target[field] = {"ref": "work.wait_time"}
    assert not Draft202012Validator(SourceDocument.model_json_schema()).is_valid(data)
    assert not api.compile(yaml.safe_dump(data)).ok
    work = Node(
        id="work",
        type="task",
        **({field: target[field]} if field != "lead_time" else {}),
    )
    process = IR(
        name="p",
        nodes=[Node(id="start", type="start"), work, Node(id="end", type="end")],
        edges=[Edge(source="start", target="work"), Edge(source="work", target="end")],
        **({field: target[field]} if field == "lead_time" else {}),
    )
    with pytest.raises(ValidationError, match="E1301"):
        validate_ir(process)
    with pytest.raises(ContractError):
        CanonicalIRContract.model_validate(ir_to_schema_dict(process))


@pytest.mark.parametrize(
    "field,value",
    [
        ("branch", {"mode": "invalid"}),
        ("outcomes", {"yes": {"to": "end"}, "no": "work"}),
        ("routes", "invalid"),
        ("cycle_time", None),
        ("consumes", None),
    ],
)
def test_generated_source_schema_does_not_leave_control_or_authored_fields_unconstrained(
    field, value
):
    data = document()
    data["steps"][1][field] = value
    if field in {"branch", "routes"}:
        data["steps"][1]["kind"] = "branch"
    elif field == "outcomes":
        data["steps"][1]["kind"] = "decision"
    assert not Draft202012Validator(SourceDocument.model_json_schema()).is_valid(data)
    assert not api.compile(yaml.safe_dump(data)).ok


@pytest.mark.parametrize("field", ["owner", "business_units"])
def test_named_context_has_the_same_strict_shape_in_source_and_exchange(field):
    data = document()
    entry = {"id": "ops", "name": "Operations", "type": "unsupported"}
    data["process"][field] = entry if field == "owner" else [entry]
    assert not Draft202012Validator(SourceDocument.model_json_schema()).is_valid(data)
    assert not api.compile(yaml.safe_dump(data)).ok
    exchange = {
        "process": data["process"],
        "nodes": [{"id": "start", "kind": "start"}, {"id": "end", "kind": "end"}],
        "edges": [{"source": "start", "target": "end"}],
    }
    with pytest.raises(ContractError):
        CanonicalIRContract.model_validate(exchange)


def test_valid_grouped_profiles_remain_lossless_under_the_typed_source_contract():
    data = document()
    data["process"]["items"] = {
        "group": [
            {
                "id": "a",
                "name": "A",
                "kind": "material",
                "quantity": {"kind": "count", "value": 2},
            }
        ]
    }
    data["steps"][1]["cycle_time"] = {
        "basis": "observed",
        "primary": "mean",
        "analysis_input": "mean",
        "results": {"mean": {"method": "mean", "value": 0, "unit": "min"}},
    }
    before = deepcopy(data)
    assert Draft202012Validator(SourceDocument.model_json_schema()).is_valid(data)
    result = api.validate(yaml.safe_dump(data))
    assert result.ok
    assert result.value.items == data["process"]["items"]
    assert result.value.nodes[1].cycle_time == data["steps"][1]["cycle_time"]
    assert data == before


@pytest.mark.parametrize("case", ["scalar_entity", "scalar_branch"])
def test_source_diagnostics_do_not_expose_model_types_or_union_paths(case):
    data = document()
    if case == "scalar_entity":
        data["process"]["items"] = [42]
    else:
        data["steps"][1].update(kind="branch", branch="invalid")
    result = api.compile(yaml.safe_dump(data))
    assert not result.ok
    message = result.diagnostics[0].message
    path = result.diagnostics[0].field_path
    assert result.diagnostics[0].code == (
        "E1202" if case == "scalar_entity" else "E0215"
    )
    assert path == (
        "process.items[0]" if case == "scalar_entity" else "steps[1].branch"
    )
    assert not any(
        token in message + path
        for token in (
            "ItemContract",
            "BranchConfig",
            "function-",
            "input_value",
            "Pydantic",
        )
    )


def test_canonical_schema_failure_does_not_dump_schema_or_input_values():
    from flo.process.ir.validate import validate_against_schema

    process = IR(
        name="p",
        nodes=[Node(id="work", type="task")],
        process_owner="internal-invalid-context",
    )
    with pytest.raises(ValidationError, match="schema validation failed") as error:
        validate_against_schema(process)
    assert error.value.location == ("process", "owner")
    assert "internal-invalid-context" not in str(error.value)
    assert "$defs" not in str(error.value)
    assert "CanonicalNamedIdentityContract" not in str(error.value)


@pytest.mark.parametrize("annotated", [False, True])
def test_named_target_shorthand_and_objects_are_both_valid_in_schema_and_compiler(
    annotated,
):
    data = document()
    data["steps"][1].update(
        kind="decision",
        outcomes={
            "accepted": "end",
            "retry": {"target": "end", "handoff": {"type": "responsibility"}}
            if annotated
            else "work",
        },
    )
    assert Draft202012Validator(SourceDocument.model_json_schema()).is_valid(data)
    result = api.validate(yaml.safe_dump(data))
    assert result.ok, result.diagnostics
    assert any(edge.outcome == "accepted" for edge in result.value.edges)


@pytest.mark.parametrize("declaration", ["outcomes", "routes"])
@pytest.mark.parametrize("override", ["outcome", "route"])
def test_named_target_rejects_selection_fields_that_would_be_ignored(
    declaration, override
):
    data = document()
    node = data["steps"][1]
    node["kind"] = "decision" if declaration == "outcomes" else "branch"
    if declaration == "routes":
        node["branch"] = {"mode": "dispatch"}
    node[declaration] = {
        "accepted": {"target": "end", override: "ignored"},
        "retry": "work",
    }
    assert not Draft202012Validator(SourceDocument.model_json_schema()).is_valid(data)
    result = api.compile(yaml.safe_dump(data))
    assert not result.ok
    assert result.diagnostics[0].code == "E0220"
    assert (
        result.diagnostics[0].field_path
        == f"steps[1].{declaration}.accepted.{override}"
    )
