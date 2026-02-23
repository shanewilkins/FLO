import pytest

from flo.ir import IR, Node, validate_ir
from flo.services.errors import ValidationError


def test_validate_valid_ir():
    ir = IR(name="test", nodes=[Node(id="n1", type="task")])
    # should not raise
    validate_ir(ir)


def test_validate_empty_nodes_raises():
    ir = IR(name="empty", nodes=[])
    with pytest.raises(ValidationError):
        validate_ir(ir)


def test_validate_duplicate_ids_raises():
    ir = IR(name="dup", nodes=[Node(id="a", type="t"), Node(id="a", type="t")])
    with pytest.raises(ValidationError):
        validate_ir(ir)
