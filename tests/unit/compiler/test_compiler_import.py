from flo.compiler import compile_adapter
from flo.compiler.ir import IR


def test_compile_adapter_stub():
    parsed = {"name": "x", "content": "c"}
    ir = compile_adapter(parsed)
    assert isinstance(ir, IR)
    assert ir.name == "x"
