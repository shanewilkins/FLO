from click.testing import CliRunner

from flo.cli import cli


def test_cli_run_cmd_using_click(tmp_flo_file):
    runner = CliRunner()
    # Click normalized command name (underscores/hyphens) may vary; use
    # the shorter 'run' command (current mapping) to invoke the runner.
    result = runner.invoke(cli, ["run", str(tmp_flo_file)])
    # debug output when failing
    print("DEBUG OUTPUT:\n", result.output)
    print("DEBUG EXC:\n", repr(result.exception))
    assert result.exit_code == 0
    assert "Hello world!" in result.output
