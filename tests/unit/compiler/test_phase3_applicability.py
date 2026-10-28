"""Independent applicability matrix for every authored node field and kind."""

from copy import deepcopy

import pytest
from pydantic import ValidationError

from flo.process.contracts import CanonicalNodeContract
from flo.source.models import SourceStep

KINDS = (
    "start",
    "task",
    "system_task",
    "queue",
    "wait",
    "decision",
    "branch",
    "end",
    "subprocess",
    "parallel_split",
    "parallel_join",
)
COMMON = {
    "id",
    "kind",
    "name",
    "description",
    "lane",
    "subprocess_parent",
    "extensions",
    "attrs",
}
WORK = {
    "cycle_time",
    "wait_time",
    "changeover_time",
    "value_class",
    "consumes",
    "produces",
    "performed_by",
    "uses",
    "location",
}
PROFILE = {
    "basis": "observed",
    "primary": "mean",
    "results": {"mean": {"method": "mean", "value": 0, "unit": "min"}},
}
VALUES = {
    "id": "node",
    "kind": "task",
    "name": "Name",
    "description": "Description",
    "lane": "ops",
    "location": "station",
    "subprocess_parent": "parent",
    "extensions": {"example:annotation": "retained"},
    "attrs": {},
    "consumes": ["item"],
    "produces": ["item"],
    "performed_by": ["person"],
    "uses": ["machine"],
    "value_class": "unknown",
    "cycle_time": PROFILE,
    "wait_time": PROFILE,
    "changeover_time": PROFILE,
    "branch": {"mode": "dispatch"},
    "outcomes": {"yes": "done", "no": "retry"},
    "routes": {"a": "done", "b": "retry"},
    "steps": [],
    "subnodes": [],
}


def allowed(kind, field):
    if field in COMMON:
        return True
    if kind in {"task", "system_task", "subprocess"} and field in WORK:
        return True
    if kind in {"queue", "wait"} and field in {"wait_time", "location"}:
        return True
    return (
        (kind == "decision" and field == "outcomes")
        or (kind == "branch" and field in {"branch", "routes"})
        or (kind == "subprocess" and field in {"steps", "subnodes"})
    )


def test_matrix_inventories_every_source_node_field():
    assert set(VALUES) == set(SourceStep.model_fields)


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("field", sorted(VALUES))
def test_source_and_exchange_field_applicability(kind, field):
    payload = {"id": "node", "kind": kind, field: deepcopy(VALUES[field])}
    payload["kind"] = kind
    if allowed(kind, field):
        SourceStep.model_validate(payload)
    else:
        with pytest.raises(ValidationError, match=r"cannot be declared|nested steps"):
            SourceStep.model_validate(payload)
    if field not in CanonicalNodeContract.model_fields:
        return
    if allowed(kind, field):
        CanonicalNodeContract.model_validate(payload)
    else:
        with pytest.raises(ValidationError, match="cannot be declared"):
            CanonicalNodeContract.model_validate(payload)


@pytest.mark.parametrize("kind", ["start", "end", "decision", "queue", "wait"])
@pytest.mark.parametrize(
    "field", ["cycle_time", "value_class", "consumes", "performed_by"]
)
def test_attrs_cannot_bypass_applicability(kind, field):
    with pytest.raises(ValidationError, match=r"cannot be declared|Extra inputs"):
        SourceStep.model_validate(
            {"id": "node", "kind": kind, "attrs": {field: deepcopy(VALUES[field])}}
        )


@pytest.mark.parametrize("kind", ["start", "end", "decision", "queue", "wait"])
@pytest.mark.parametrize(
    "field", ["cycle_time", "changeover_time", "value_class", "consumes"]
)
def test_null_does_not_make_an_inapplicable_field_legal(kind, field):
    payload = {"id": "node", "kind": kind, field: None}
    with pytest.raises(ValidationError):
        SourceStep.model_validate(payload)
    with pytest.raises(ValidationError):
        CanonicalNodeContract.model_validate(payload)
