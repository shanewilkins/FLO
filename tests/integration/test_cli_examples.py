from click.testing import CliRunner

from flo.core.cli import cli
from tests.fixtures.sample_fixtures import repo_root


def test_cli_run_all_examples():
    runner = CliRunner()
    examples = sorted((repo_root() / "examples" / "reference").glob("*.flo"))
    assert examples, "No example files found for integration test"

    for ex in examples:
        result = runner.invoke(cli, ["run", str(ex)])
        # basic sanity: CLI returns success and prints the rendered DOT
        assert result.exit_code == 0
        assert "digraph" in result.output
