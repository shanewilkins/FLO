import pytest

from flo.process.ir import validate_ir
from flo.process.ir.schema_projection import ir_to_schema_dict
from flo.render import render_artifact
from flo.source import compile_adapter, parse_adapter
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


def test_mpi_lms_reference_specimen_renders_complete_theme_contract():
    source = repo_root() / "examples" / "reference" / "mpi_lms_theme_specimen.flo"
    ir = compile_adapter(parse_adapter(source.read_text(), source_path=str(source)))
    validate_ir(ir)

    artifact = render_artifact(ir, options={"diagram": "sppm", "theme": "mpi-lms"})

    assert 'data-flo-theme="mpi-lms"' in artifact.content
    assert '"background":"#F6F7F5"' in artifact.content
    assert 'font-family="Source Sans 3, system-ui, sans-serif"' in artifact.content
    assert 'fill="#0B5D5A"' in artifact.content
    assert 'fill="#8A5A00"' in artifact.content
    assert 'fill="#A43232"' in artifact.content
    assert 'fill="#1D5D88"' in artifact.content
    assert 'fill="#F1F4F3"' in artifact.content
    assert 'stroke="#5B6870"' in artifact.content
    assert 'stroke="#A43232"' in artifact.content
    assert 'marker-end="url(#flo-sppm-rework-arrow)"' in artifact.content


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


def test_compile_preserves_generic_branch_routes_without_rendering_contract():
    content = """
spec_version: "0.1"
process: {id: leveling, name: Workload Leveling}
steps:
  - {id: start, kind: start}
  - id: assign
    kind: branch
    branch:
      mode: dispatch
      policy: least_loaded
    routes:
      worker_a: task_a
      worker_b: task_b
  - {id: task_a, kind: task}
  - {id: task_b, kind: task}
  - {id: end, kind: end}
"""

    ir = compile_adapter(parse_adapter(content))
    validate_ir(ir)
    branch = next(node for node in ir.nodes if node.id == "assign")
    routes = {edge.route: edge.target for edge in ir.edges if edge.source == "assign"}

    assert branch.attrs["branch"] == {
        "mode": "dispatch",
        "policy": "least_loaded",
    }
    assert routes == {"worker_a": "task_a", "worker_b": "task_b"}
    payload = ir_to_schema_dict(ir)
    assert {edge["route"] for edge in payload["edges"] if "route" in edge} == {
        "worker_a",
        "worker_b",
    }


@pytest.mark.parametrize(
    ("invalid_fragment", "error_code"),
    [
        ('rework: "yes"', "E0209"),
        ("metadata: discarded", "E0210"),
    ],
)
def test_compile_rejects_transition_fields_that_would_be_discarded(
    invalid_fragment, error_code
):
    content = f"""
spec_version: "0.1"
process: {{id: invalid_transition, name: Invalid Transition}}
steps:
  - {{id: start, kind: start}}
  - {{id: end, kind: end}}
transitions:
  - source: start
    target: end
    {invalid_fragment}
"""

    adapter = parse_adapter(content)
    with pytest.raises(ValueError, match=error_code):
        compile_adapter(adapter)


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
