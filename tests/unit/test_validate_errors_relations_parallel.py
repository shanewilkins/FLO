import pytest

from flo.compiler.ir.models import Edge, IR, Node
from flo.compiler.ir.validate import validate_ir
from flo.services.errors import ValidationError


def test_validate_ir_accepts_consumes_produces_when_items_declared():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(
                id="mix",
                type="task",
                attrs={
                    "consumes": ["flour", "water"],
                    "produces": ["dough"],
                },
            ),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="mix"),
            Edge(source="mix", target="end"),
        ],
        process_metadata={
            "items": [
                {"id": "flour", "kind": "material"},
                {"id": "water", "kind": "material"},
                {"id": "dough", "kind": "material"},
            ]
        },
    )

    validate_ir(ir)


def test_validate_ir_rejects_consumes_with_undeclared_item():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="mix", type="task", attrs={"consumes": ["flour"]}),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="mix"),
            Edge(source="mix", target="end"),
        ],
        process_metadata={
            "items": [
                {"id": "water", "kind": "material"},
            ]
        },
    )

    with pytest.raises(ValidationError, match="E1312"):
        validate_ir(ir)


def test_validate_ir_accepts_canonical_item_and_resource_kinds():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="end", handoff=True),
        ],
        process_metadata={
            "items": [
                {"id": "order", "name": "Order", "kind": "information"},
                {"id": "dough", "name": "Dough", "kind": "material"},
            ],
            "resources": [
                {"id": "baker", "name": "Baker", "kind": "person"},
                {"id": "mixer", "name": "Mixer", "kind": "equipment"},
            ],
        },
    )

    validate_ir(ir)


def test_validate_ir_rejects_invalid_item_kind():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="end"),
        ],
        process_metadata={
            "items": [
                {"id": "order", "name": "Order", "kind": "unknown"},
            ],
        },
    )

    with pytest.raises(ValidationError, match="E1217"):
        validate_ir(ir)


def test_validate_ir_rejects_invalid_resource_kind():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="end"),
        ],
        process_metadata={
            "resources": [
                {"id": "operator", "name": "Operator", "kind": "team"},
            ],
        },
    )

    with pytest.raises(ValidationError, match="E1218"):
        validate_ir(ir)


def test_validate_ir_rejects_non_boolean_handoff():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="end", handoff="yes"),
        ],
    )

    with pytest.raises(ValidationError, match="E1410"):
        validate_ir(ir)


def test_validate_ir_accepts_resource_relations_with_matching_kinds():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(
                id="mix",
                type="task",
                attrs={
                    "performed_by": ["baker"],
                    "uses": ["mixer"],
                },
            ),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="mix"),
            Edge(source="mix", target="end"),
        ],
        process_metadata={
            "resources": [
                {"id": "baker", "kind": "person"},
                {"id": "mixer", "kind": "equipment"},
            ]
        },
    )

    validate_ir(ir)


def test_validate_ir_rejects_resource_relations_with_unknown_resource():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="mix", type="task", attrs={"performed_by": ["baker"]}),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="mix"),
            Edge(source="mix", target="end"),
        ],
        process_metadata={
            "resources": [
                {"id": "mixer", "kind": "equipment"},
            ]
        },
    )

    with pytest.raises(ValidationError, match="E1313"):
        validate_ir(ir)


def test_validate_ir_rejects_resource_relations_with_wrong_kind():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="mix", type="task", attrs={"uses": ["baker"]}),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="mix"),
            Edge(source="mix", target="end"),
        ],
        process_metadata={
            "resources": [
                {"id": "baker", "kind": "person"},
            ]
        },
    )

    with pytest.raises(ValidationError, match="E1314"):
        validate_ir(ir)


def test_validate_ir_accepts_parallel_split_join_structure():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="split", type="parallel_split"),
            Node(id="a", type="task"),
            Node(id="b", type="task"),
            Node(id="join", type="parallel_join"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="split"),
            Edge(source="split", target="a"),
            Edge(source="split", target="b"),
            Edge(source="a", target="join"),
            Edge(source="b", target="join"),
            Edge(source="join", target="end"),
        ],
    )

    validate_ir(ir)


def test_validate_ir_rejects_parallel_split_with_single_outgoing():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="split", type="parallel_split"),
            Node(id="join", type="parallel_join"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="split"),
            Edge(source="split", target="join"),
            Edge(source="join", target="end"),
            Edge(source="start", target="join"),
        ],
    )

    with pytest.raises(ValidationError, match="E1011"):
        validate_ir(ir)


def test_validate_ir_rejects_parallel_join_without_parallel_split_upstream():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="a", type="task"),
            Node(id="b", type="task"),
            Node(id="join", type="parallel_join"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="a"),
            Edge(source="start", target="b"),
            Edge(source="a", target="join"),
            Edge(source="b", target="join"),
            Edge(source="join", target="end"),
        ],
    )

    with pytest.raises(ValidationError, match="E1014"):
        validate_ir(ir)
