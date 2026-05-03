from flo.adapters import parse_adapter
from flo.compiler import compile_adapter
from flo.compiler.ir import validate_ir
from flo.render import render_dot
from tests.fixtures.sample_fixtures import repo_root


def test_compile_and_render_examples():
    examples = sorted((repo_root() / "examples" / "reference").glob("*.flo"))
    assert examples

    for ex in examples:
        content = ex.read_text()
        adapter = parse_adapter(content, source_path=str(ex))
        ir = compile_adapter(adapter)
        # validate_ir raises on failure
        validate_ir(ir)
        dot = render_dot(ir)
        assert "digraph" in dot


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
    assert '"__rework_corridor_decision_rework_1" [shape=point, width=0.01, height=0.01, label="", style=invis];' in dot
    assert '"decision" -> "__rework_corridor_decision_rework_1" [tailport=e, constraint=false, weight=0, style=dashed, arrowhead=none];' in dot
    assert '"__rework_corridor_decision_rework_1" -> "rework" [headport=w, constraint=false, minlen=3, weight=0, style=dashed, label="no"];' in dot
