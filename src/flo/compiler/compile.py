"""Compiler stub: adapter -> IR conversion.

The real compiler will convert adapter models into the canonical
FlowProcess IR (instances of `flo.ir.models.FlowProcess`). This stub
is a placeholder that will be implemented as part of v0.1.
"""
from typing import Any, Dict

from flo.ir import IR, Node


def compile_adapter(adapter_model: Dict[str, Any]) -> IR:
    """Compile an adapter model into a minimal canonical `IR` instance.

    This is a tiny, pragmatic implementation used by the test harness
    to validate wiring; real compilation logic will replace this.
    """
    name = adapter_model.get("name", "compiled")
    content = adapter_model.get("content")
    node = Node(id="n1", type="task", attrs={"source": content})
    return IR(name=name, nodes=[node])
