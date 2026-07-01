from flo.compiler import compile_adapter
from flo.compiler.ir import IR


def test_compile_adapter_falls_back_to_single_task_when_steps_missing():
    ir = compile_adapter({"process": {"name": "Fallback Process"}})

    assert isinstance(ir, IR)
    assert ir.name == "Fallback Process"
    assert len(ir.nodes) == 1
    assert ir.nodes[0].type == "task"
    assert ir.edges == []
