import pytest

from flo.ir import validate_ir
from flo.services.errors import ValidationError


def test_validate_valid_ir(ir_factory, node_factory):
    ir = ir_factory(name="test", nodes=[node_factory("n1")])
    # should not raise
    validate_ir(ir)


def test_validate_empty_nodes_raises(ir_factory):
    ir = ir_factory(name="empty", nodes=[])
    with pytest.raises(ValidationError):
        validate_ir(ir)


@pytest.mark.parametrize("ids", [["a", "a"], ["x", "x", "x"]])
def test_validate_duplicate_ids_raises(ir_factory, node_factory, ids):
    nodes = [node_factory(i) for i in ids]
    ir = ir_factory(name="dup", nodes=nodes)
    with pytest.raises(ValidationError):
        validate_ir(ir)
