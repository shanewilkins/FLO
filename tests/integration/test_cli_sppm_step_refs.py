from click.testing import CliRunner

from flo.core.cli import cli


def test_run_sppm_shows_stable_step_reference_tokens():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/sppm_feature_showcase.flo",
            "--export",
            "dot",
            "--diagram",
            "sppm",
        ],
    )

    assert result.exit_code == 0
    assert "[intake]" not in result.output
    assert '"triage" [label="Information Complete?", shape=diamond' in result.output
    assert "[process_queue]" not in result.output
    assert '"process_queue" [label=<<TABLE' in result.output
    assert 'shape=triangle' in result.output
    assert "\ntriage\"" not in result.output
    assert "\nprocess_queue\"" not in result.output
    assert "[process]" not in result.output