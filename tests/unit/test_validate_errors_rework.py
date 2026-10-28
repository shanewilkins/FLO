import pytest

from flo.errors import ValidationError
from flo.process.ir.models import IR, Edge, Node
from flo.process.ir.validate import validate_ir


def _process(rework):
    return IR(
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
            Edge(source="gate", target="rework", outcome="no", rework=rework),
            Edge(source="rework", target="gate", rework={}),
        ],
    )


def test_validate_ir_accepts_valid_rework_edge_metadata():
    process = _process(
        {
            "reason": "Missing approvals",
            "frequency": {
                "basis": "observed",
                "numerator": 3,
                "denominator": 40,
                "observation_unit": "cases",
            },
        }
    )
    validate_ir(process)
    assert process.edges[2].rework["frequency"]["numerator"] == 3


def test_validate_ir_rejects_invalid_rework_rate():
    process = _process(
        {
            "frequency": {
                "basis": "observed",
                "numerator": 15,
                "denominator": 10,
                "observation_unit": "cases",
            },
        }
    )
    with pytest.raises(ValidationError, match=r"E1401.*rework"):
        validate_ir(process)


def test_validate_ir_rejects_blank_rework_reason():
    with pytest.raises(ValidationError, match=r"E1401.*rework"):
        validate_ir(_process({"reason": "   "}))


@pytest.mark.parametrize(
    ("edge_type", "rework"),
    [("rework", False), ("sequence", True)],
)
def test_validate_ir_rejects_conflicting_rework_declarations(edge_type, rework):
    # Retired duplicate flags now fail at construction, before graph validation.
    with pytest.raises(TypeError, match="edge_type"):
        Edge(source="start", target="end", edge_type=edge_type, rework=rework)
