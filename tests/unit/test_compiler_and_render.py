from pathlib import Path

from flo.adapters import parse_adapter
from flo.compiler import compile_adapter
from flo.compiler.ir import validate_ir
from flo.render import render_dot


def _repo_root(start: Path | None = None) -> Path:
    start = start or Path(__file__).resolve()
    cur = start
    while cur != cur.parent:
        if (cur / "examples").is_dir():
            return cur
        cur = cur.parent
    raise RuntimeError("repo root with examples/ not found")


def test_compile_and_render_examples():
    examples = sorted((_repo_root() / "examples" / "reference").glob("*.flo"))
    assert examples

    for ex in examples:
        content = ex.read_text()
        adapter = parse_adapter(content, source_path=str(ex))
        ir = compile_adapter(adapter)
        # validate_ir raises on failure
        validate_ir(ir)
        dot = render_dot(ir)
        assert isinstance(dot, str)


def test_compile_and_render_preserves_rework_outcome_semantics():
    content = """
spec_version: "0.1"

process:
  id: invoice_review_v1
  name: Invoice Review (with rework)

steps:
  - id: start
    kind: start
    name: Start

  - id: review
    kind: task
    name: Review Invoice

  - id: decision
    kind: decision
    name: Valid?
    outcomes:
      yes: approve
      no:
        target: rework
        edge_type: rework
        rework: true

  - id: rework
    kind: task
    name: Request Rework

  - id: approve
    kind: end
    name: Approved
"""

    adapter = parse_adapter(content)
    ir = compile_adapter(adapter)
    validate_ir(ir)

    rework_edge = next(edge for edge in ir.edges if edge.source == "decision" and edge.target == "rework")
    assert rework_edge.outcome == "no"
    assert rework_edge.edge_type == "rework"
    assert rework_edge.rework is True

    dot = render_dot(ir)
    assert '"decision" -> "rework" [style=dashed, label="no"];' in dot
