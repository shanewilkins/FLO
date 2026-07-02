from click.testing import CliRunner

from flo.core.cli import cli


def test_cli_run_cmd_using_click(tmp_flo_file):
    runner = CliRunner()
    # Click normalized command name (underscores/hyphens) may vary; use
    # the shorter 'run' command (current mapping) to invoke the runner.
    result = runner.invoke(cli, ["run", str(tmp_flo_file)])
    # debug output when failing
    print("DEBUG OUTPUT:\n", result.output)
    print("DEBUG EXC:\n", repr(result.exception))
    assert result.exit_code == 0
    assert "<svg" in result.output


def test_cli_run_help_marks_svg_as_primary_render_output():
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "--help"])

    assert result.exit_code == 0
    assert "Render a FLO diagram as SVG by default" in result.output
    assert "svg for diagrams" in result.output
