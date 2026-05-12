from click.testing import CliRunner

from flo.core.cli import cli


def test_run_sppm_child_map_projection_with_focus_emits_context_metadata():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/chocolate_chip_cookies.flo",
            "--export",
            "dot",
            "--diagram",
            "sppm",
            "--sppm-projection",
            "child-map",
            "--sppm-focus-subprocess",
            "prep_subprocess",
        ],
    )
    assert result.exit_code == 0
    assert "Projection:" in result.output
    assert "child-map" in result.output
    assert "Focus:" in result.output
    assert "prep_subprocess" in result.output
    assert "Entry Context:" in result.output
    assert "Exit Context:" in result.output


def test_run_sppm_child_map_projection_without_focus_reports_fallback_warning():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/chocolate_chip_cookies.flo",
            "--export",
            "dot",
            "--diagram",
            "sppm",
            "--sppm-projection",
            "child-map",
        ],
    )
    assert result.exit_code == 0
    assert "Projection Fallback:" in result.output
    assert "missing focus subprocess" in result.output
    assert "Readability Warning:" in result.output


def test_run_help_surfaces_sppm_publication_controls():
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "--help"])

    assert result.exit_code == 0
    for token in (
        "--no-header",
        "--no-footer",
        "--publication-page-format",
        "--sppm-output-profile",
        "--sppm-projection",
        "--sppm-focus-subprocess",
        "SPPM publication:",
    ):
        assert token in result.output
