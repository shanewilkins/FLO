import json

from click.testing import CliRunner
from pathlib import Path

from flo.app.cli import cli


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


def test_cli_inspect_reports_timing_for_file():
    runner = CliRunner()
    source = Path("examples/reference/washnfold.flo")

    result = runner.invoke(cli, ["inspect", str(source)])

    assert result.exit_code == 0
    assert "Process: Wash n' Fold (wash_n_fold)" in result.output
    assert "Cycle time: 105 min" in result.output
    assert "Wait time: 95 min" in result.output
    assert "Modeled lead time: 200 min" in result.output


def test_cli_inspect_json_from_stdin_is_pure_json():
    runner = CliRunner()
    content = Path("examples/reference/washnfold.flo").read_text(encoding="utf-8")

    result = runner.invoke(
        cli,
        ["inspect", "-", "--format", "json"],
        input=content,
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["process"]["id"] == "wash_n_fold"
    assert payload["modeled_lead_time_seconds"] == 12000.0


def test_cli_inspect_can_write_json_to_file():
    runner = CliRunner()
    source = Path("examples/reference/washnfold.flo")
    content = source.read_text(encoding="utf-8")
    with runner.isolated_filesystem():
        source_copy = Path("washnfold.flo")
        source_copy.write_text(content, encoding="utf-8")

        result = runner.invoke(
            cli,
            ["inspect", str(source_copy), "--format", "json", "-o", "timing.json"],
        )

        assert result.exit_code == 0
        assert result.output == ""
        payload = json.loads(Path("timing.json").read_text(encoding="utf-8"))
        assert payload["declared_totals"]["cycle_time_seconds"] == 6300.0


def test_cli_inspect_help_describes_defaults():
    runner = CliRunner()

    result = runner.invoke(cli, ["inspect", "--help"])

    assert result.exit_code == 0
    assert "deterministic static analysis" in result.output
    assert "[default: timing]" in result.output
    assert "[default: text]" in result.output
