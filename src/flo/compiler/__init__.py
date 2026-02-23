from __future__ import annotations

from typing import Dict, Any

from flo.ir import IR, Node


def compile_adapter(parsed: Dict[str, Any]) -> IR:
    """Minimal compiler stub converting parsed adapter dict -> IR.

    Produces a single-node IR so render/analysis stubs can consume it.
    """
    name = parsed.get("name", "compiled")
    content = parsed.get("content")
    node = Node(id="n1", type="task", attrs={"source": content})
    return IR(name=name, nodes=[node])
"""Compiler package: transforms adapter models to canonical IR."""
from .compile import compile_adapter

__all__ = ["compile_adapter"]
