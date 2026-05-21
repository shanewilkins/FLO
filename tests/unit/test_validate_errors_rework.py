import pytest

from flo.compiler.ir.models import Edge, IR, Node
from flo.compiler.ir.validate import validate_ir
from flo.services.errors import ValidationError


def test_validate_ir_accepts_valid_rework_edge_metadata():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="gate", type="decision"),
            Node(id="rework", type="task"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="gate"),
            Edge(source="gate", target="end", outcome="yes"),
            Edge(
                source="gate",
                target="rework",
                outcome="no",
                edge_type="rework",
                rework=True,
                metadata={
                    "rate": 0.08,
                    "reason": "Missing approvals",
                    "count": "3 per 40 cases",
                },
            ),
            Edge(source="rework", target="gate", edge_type="rework", rework=True),
        ],
    )

    validate_ir(ir)


def test_validate_ir_rejects_invalid_rework_rate():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="gate", type="decision"),
            Node(id="rework", type="task"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="gate"),
            Edge(source="gate", target="end", outcome="yes"),
            Edge(
                source="gate",
                target="rework",
                outcome="no",
                edge_type="rework",
                rework=True,
                metadata={"rate": 1.5},
            ),
            Edge(source="rework", target="gate", edge_type="rework", rework=True),
        ],
    )

    with pytest.raises(ValidationError, match="E1401"):
        validate_ir(ir)


def test_validate_ir_rejects_blank_rework_reason():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="gate", type="decision"),
            Node(id="rework", type="task"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="gate"),
            Edge(source="gate", target="end", outcome="yes"),
            Edge(
                source="gate",
                target="rework",
                outcome="no",
                edge_type="rework",
                rework=True,
                metadata={"reason": "   "},
            ),
            Edge(source="rework", target="gate", edge_type="rework", rework=True),
        ],
    )

    with pytest.raises(ValidationError, match="E1402"):
        validate_ir(ir)
