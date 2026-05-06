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
    assert "[intake]" in result.output
    assert "[triage]" in result.output
    assert "[process_queue]" in result.output
    assert "[process]" in result.output