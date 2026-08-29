"""Contract tests aligning canonical entities with ``flo_types.json``."""

from __future__ import annotations

import pytest

from flo.process.ir.models import Edge, IR, Node
from flo.process.ir.validate import validate_ir
from flo.errors import ValidationError


def _ir_with_metadata(metadata: dict[str, object]) -> IR:
    return IR(
        name="entity_contract",
        nodes=[Node(id="start", type="start"), Node(id="end", type="end")],
        edges=[Edge(source="start", target="end")],
        process_metadata=metadata,
    )


@pytest.mark.parametrize(
    ("collection", "entry", "code"),
    [
        ("items", {"name": "Order", "kind": "information"}, "E1219"),
        ("items", {"id": "order", "kind": "information"}, "E1220"),
        ("items", {"id": "order", "name": "Order"}, "E1217"),
        ("resources", {"name": "Reviewer", "kind": "person"}, "E1219"),
        ("resources", {"id": "reviewer", "kind": "person"}, "E1220"),
        ("resources", {"id": "reviewer", "name": "Reviewer"}, "E1218"),
    ],
)
def test_canonical_entity_requires_identity_name_and_kind(
    collection: str,
    entry: dict[str, str],
    code: str,
) -> None:
    with pytest.raises(ValidationError, match=code):
        validate_ir(_ir_with_metadata({collection: [entry]}))


@pytest.mark.parametrize("collection", ["items", "resources"])
def test_canonical_entity_ids_are_unique_across_nested_groups(
    collection: str,
) -> None:
    kind = "material" if collection == "items" else "person"
    metadata = {
        collection: {
            "first": [{"id": "shared", "name": "First", "kind": kind}],
            "second": [{"id": "shared", "name": "Second", "kind": kind}],
        }
    }

    with pytest.raises(ValidationError, match="E1221"):
        validate_ir(_ir_with_metadata(metadata))


def test_untyped_resource_cannot_satisfy_performed_by() -> None:
    ir = _ir_with_metadata(
        {
            "resources": [
                {"id": "reviewer", "name": "Reviewer"},
            ]
        }
    )
    ir.nodes.insert(
        1,
        Node(id="review", type="task", attrs={"performed_by": ["reviewer"]}),
    )
    ir.edges = [
        Edge(source="start", target="review"),
        Edge(source="review", target="end"),
    ]

    with pytest.raises(ValidationError, match="E1218"):
        validate_ir(ir)
