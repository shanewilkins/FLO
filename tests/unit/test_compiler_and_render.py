from flo.adapters import parse_adapter
from flo.compiler import compile_adapter
from flo.compiler.ir import validate_ir
from flo.render import render_artifact
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
        artifact = render_artifact(ir)
        assert artifact.kind == "svg"
        assert "<svg" in artifact.content


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

    rework_edge = next(
        edge
        for edge in ir.edges
        if edge.source == "decision" and edge.target == "rework"
    )
    assert rework_edge.outcome == "no"
    assert rework_edge.edge_type == "rework"
    assert rework_edge.rework is True

    artifact = render_artifact(ir, options={"diagram": "sppm"})
    assert artifact.kind == "svg"
    assert 'data-edge-source="decision"' in artifact.content
    assert 'data-edge-target="rework"' in artifact.content
    assert 'data-edge-kind="rework"' in artifact.content


def test_compile_and_render_canonical_examples_with_direct_svg_backend():
    cases = [
        (
            repo_root() / "examples" / "reference" / "new_semantics.flo",
            [
                "Canonical Semantics Reference",
                "Split Preparation",
                "Join Preparation",
            ],
        ),
        (
            repo_root() / "examples" / "reference" / "semantic_controls_showcase.flo",
            ["Semantic Controls Showcase", "Split Prep", "Quality OK?"],
        ),
    ]

    for example_path, expected_labels in cases:
        content = example_path.read_text()
        adapter = parse_adapter(content, source_path=str(example_path))
        ir = compile_adapter(adapter)
        validate_ir(ir)

        artifact = render_artifact(
            ir,
            options={
                "diagram": "sppm",
                "render_backend": "svg",
            },
        )

        assert artifact.kind == "svg"
        assert artifact.backend == "svg"
        assert "<svg" in artifact.content
        for label in expected_labels:
            assert label in artifact.content
