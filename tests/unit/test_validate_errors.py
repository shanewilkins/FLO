import pytest
from flo.ir.validate import validate_ir
from flo.services.errors import ValidationError


def test_validate_ir_wrong_type():
    with pytest.raises(ValidationError):
        validate_ir(object())


def test_validate_ir_empty_nodes(ir_factory):
    ir = ir_factory(name="x", nodes=[])
    with pytest.raises(ValidationError):
        validate_ir(ir)


@pytest.mark.parametrize("ids", [["dup", "dup"], ["a", "a", "a"]])
def test_validate_ir_duplicate_ids(ir_factory, node_factory, ids):
    nodes = [node_factory(i) for i in ids]
    ir = ir_factory(name="dup", nodes=nodes)
    with pytest.raises(ValidationError):
        validate_ir(ir)
