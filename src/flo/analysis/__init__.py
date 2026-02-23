from __future__ import annotations

from flo.ir import IR


def scc_condense(ir: IR) -> IR:
    """Minimal analysis stub that returns the IR unchanged.

    Real implementation would produce a condensed IR; stub verifies
    import wiring and type compatibility.
    """
    return ir
"""Analysis utilities: SCC condensation and heuristics."""
from .scc import condense_scc

__all__ = ["condense_scc"]
