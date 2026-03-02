from click.testing import CliRunner

from flo.core.cli import cli


def test_run_swimlane_diagram_emits_clusters():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "examples/reference/linear.flo", "--export", "dot", "--diagram", "swimlane"],
    )
    assert result.exit_code == 0
    assert "subgraph cluster_sales" in result.output
    assert "subgraph cluster_ops" in result.output


def test_run_summary_detail_omits_outcome_edge_labels():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/conformance/valid/valid_decision_with_outcomes.flo",
            "--export",
            "dot",
            "--detail",
            "summary",
        ],
    )
    assert result.exit_code == 0
    assert 'label="yes"' not in result.output
    assert 'label="no"' not in result.output


def test_run_json_export_rejects_render_only_flags():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "examples/reference/linear.flo", "--export", "json", "--diagram", "swimlane"],
    )
    assert result.exit_code == 1
    assert "require DOT output" in result.output
