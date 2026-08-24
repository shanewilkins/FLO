from click.testing import CliRunner
from pathlib import Path

from flo.core.cli import cli


def test_cli_new_creates_valid_starter_model():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["new", "purchase-request", "--name", "Purchase Request"],
        )

        assert result.exit_code == 0
        target = Path("purchase-request.flo")
        assert target.is_file()
        assert "id: purchase_request" in target.read_text(encoding="utf-8")


def test_cli_new_refuses_to_overwrite_existing_file():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("existing.flo").write_text("keep me", encoding="utf-8")
        result = runner.invoke(cli, ["new", "existing.flo"])

        assert result.exit_code == 1
        assert "already exists" in result.output
        assert Path("existing.flo").read_text(encoding="utf-8") == "keep me"


def test_cli_render_cmd_using_click(tmp_flo_file):
    runner = CliRunner()
    result = runner.invoke(cli, ["render", str(tmp_flo_file)])
    # debug output when failing
    print("DEBUG OUTPUT:\n", result.output)
    print("DEBUG EXC:\n", repr(result.exception))
    assert result.exit_code == 0
    assert "<svg" in result.output


def test_cli_render_help_marks_svg_as_primary_render_output():
    runner = CliRunner()
    result = runner.invoke(cli, ["render", "--help"])

    assert result.exit_code == 0
    assert "Render a FLO diagram as SVG by default" in result.output
    assert "svg for diagrams" in result.output


def test_cli_export_help_marks_json_as_default_output_format():
    runner = CliRunner()
    result = runner.invoke(cli, ["export", "--help"])

    assert result.exit_code == 0
    assert "[default: json]" in result.output
