import pytest

from flo.compiler.ir.models import Edge, IR, Node
from flo.compiler.ir.validate import validate_ir
from flo.services.errors import ValidationError


def test_validate_ir_rejects_unknown_subprocess_parent():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="child", type="task", attrs={"subprocess_parent": "missing"}),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="child"),
            Edge(source="child", target="end"),
        ],
    )

    with pytest.raises(ValidationError, match="E1330"):
        validate_ir(ir)


def test_validate_ir_rejects_non_subprocess_parent_reference():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="task", type="task"),
            Node(id="child", type="task", attrs={"subprocess_parent": "task"}),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="task"),
            Edge(source="task", target="child"),
            Edge(source="child", target="end"),
        ],
    )

    with pytest.raises(ValidationError, match="E1331"):
        validate_ir(ir)


def test_validate_ir_rejects_self_referential_subprocess_parent():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="prep", type="subprocess", attrs={"subprocess_parent": "prep"}),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="prep"),
            Edge(source="prep", target="end"),
        ],
    )

    with pytest.raises(ValidationError, match="E1332"):
        validate_ir(ir)


def test_validate_ir_rejects_circular_subprocess_parent_chain():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="outer", type="subprocess", attrs={"subprocess_parent": "inner"}),
            Node(id="inner", type="subprocess", attrs={"subprocess_parent": "outer"}),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="outer"),
            Edge(source="outer", target="inner"),
            Edge(source="inner", target="end"),
        ],
    )

    with pytest.raises(ValidationError, match="E1334"):
        validate_ir(ir)


def test_validate_ir_rejects_blank_subprocess_detail_map_reference():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(
                id="prep",
                type="subprocess",
                attrs={"metadata": {"detail_map_ref": "   "}},
            ),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="prep"),
            Edge(source="prep", target="end"),
        ],
    )

    with pytest.raises(ValidationError, match="E1333"):
        validate_ir(ir)


def test_validate_ir_accepts_subprocess_detail_map_reference_and_valid_parent_chain():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="prep", type="subprocess", attrs={"metadata": {"detail_map_ref": "SP-01"}}),
            Node(id="mix", type="task", attrs={"subprocess_parent": "prep"}),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="prep"),
            Edge(source="prep", target="mix"),
            Edge(source="mix", target="end"),
        ],
    )

    validate_ir(ir)