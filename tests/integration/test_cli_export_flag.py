from click.testing import CliRunner

from flo.core.cli import cli


def test_default_path_accepts_export_json_flag():
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "examples/reference/linear.flo", "--export", "json"])
    assert result.exit_code == 0
    assert '"process"' in result.output
    assert '"nodes"' in result.output


def test_default_path_exports_json_to_file(tmp_path):
    runner = CliRunner()
    out = tmp_path / "linear.json"
    result = runner.invoke(
        cli,
        ["run", "examples/reference/linear.flo", "--export", "json", "-o", str(out)],
    )
    assert result.exit_code == 0
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert '"process"' in content
    assert '"nodes"' in content


def test_default_path_accepts_export_ingredients_flag():
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "examples/reference/chocolate_chip_cookies.flo", "--export", "ingredients"])
    assert result.exit_code == 0
    assert "Materials and Equipment" in result.output


def test_default_path_accepts_export_movement_flag():
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "examples/reference/chocolate_chip_cookies.flo", "--export", "movement"])
    assert result.exit_code == 0
    assert "Inferred Material Movement" in result.output
