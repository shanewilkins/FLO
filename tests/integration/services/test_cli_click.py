import json
from pathlib import Path

from click.testing import CliRunner

from flo.app.cli import cli

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_cli_reports_installed_version():
    result = CliRunner().invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert result.output.startswith("flo, version ")


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


def test_cli_new_lists_maintained_templates():
    result = CliRunner().invoke(cli, ["new", "--list-templates"])

    assert result.exit_code == 0
    assert result.output.splitlines() == [
        "simple-process",
        "linear-flow",
        "decision",
        "handoff",
        "rework",
        "value-stream",
    ]


def test_cli_new_dry_run_previews_normalized_target_without_writing():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["new", "purchase-request", "--dry-run"])

        assert result.exit_code == 0
        assert result.output == "Would create purchase-request.flo\n"
        assert not Path("purchase-request.flo").exists()


def test_cli_new_refuses_to_overwrite_existing_file():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("existing.flo").write_text("keep me", encoding="utf-8")
        result = runner.invoke(cli, ["new", "existing.flo"])

        assert result.exit_code == 1
        assert "already exists" in result.output
        assert Path("existing.flo").read_text(encoding="utf-8") == "keep me"


def test_cli_new_force_explicitly_replaces_existing_file():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("existing.flo").write_text("replace me", encoding="utf-8")
        result = runner.invoke(
            cli,
            ["new", "existing.flo", "--force", "--name", "Replacement"],
        )

        assert result.exit_code == 0
        assert "Created existing.flo" in result.output
        assert "id: replacement" in Path("existing.flo").read_text(encoding="utf-8")


def test_cli_render_cmd_using_click(tmp_flo_file):
    runner = CliRunner()
    result = runner.invoke(cli, ["render", str(tmp_flo_file)])
    # debug output when failing
    print("DEBUG OUTPUT:\n", result.output)
    print("DEBUG EXC:\n", repr(result.exception))
    assert result.exit_code == 0
    assert "<svg" in result.output
    assert 'data-flo-diagram="sppm"' in result.output


def test_cli_render_fails_when_safe_fit_would_be_unreadable(tmp_flo_file):
    result = CliRunner().invoke(
        cli,
        ["render", str(tmp_flo_file), "--layout-width", "1px"],
    )

    assert result.exit_code == 5
    assert "below the safe readability floor 0.75" in result.output


def test_cli_render_expand_writes_natural_width_when_request_is_too_narrow(
    tmp_flo_file,
    tmp_path: Path,
):
    output_path = tmp_path / "expanded.svg"

    result = CliRunner().invoke(
        cli,
        [
            "render",
            str(tmp_flo_file),
            "--layout-width",
            "1px",
            "--layout-overflow",
            "expand",
            "--render-to",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    content = output_path.read_text(encoding="utf-8")
    root = content.partition(">")[0]
    assert 'width="1"' not in root
    assert 'viewBox="0 0 1 ' not in root


def test_cli_safe_fits_white_belt_map_to_exact_letter_canvas(tmp_path):
    output_path = tmp_path / "white-belt-letter.svg"

    result = CliRunner().invoke(
        cli,
        [
            "render",
            str(REPO_ROOT / "examples" / "reference" / "washnfold.flo"),
            "--layout-width",
            "8.5in",
            "--layout-height",
            "11in",
            "--render-to",
            str(output_path),
        ],
    )

    assert result.exit_code == 0, result.output
    root = output_path.read_text(encoding="utf-8").partition(">")[0]
    assert 'width="816"' in root
    assert 'height="1056"' in root
    assert 'preserveAspectRatio="xMidYMid meet"' in root
    assert 'viewBox="0 0 774 1306"' in root


def test_cli_render_scale_writes_requested_canvas_and_natural_viewbox(
    tmp_flo_file,
    tmp_path: Path,
):
    output_path = tmp_path / "scaled.svg"

    result = CliRunner().invoke(
        cli,
        [
            "render",
            str(tmp_flo_file),
            "--layout-width",
            "1px",
            "--layout-overflow",
            "scale",
            "--render-to",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    content = output_path.read_text(encoding="utf-8")
    assert 'width="1"' in content
    assert 'preserveAspectRatio="xMidYMid meet"' in content
    assert 'viewBox="0 0 1 ' not in content


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


def test_cli_inspect_structure_json_from_stdin_is_pure_json():
    runner = CliRunner()
    content = Path("examples/reference/washnfold.flo").read_text(encoding="utf-8")

    result = runner.invoke(
        cli,
        ["inspect", "-", "--analysis", "structure", "--format", "json"],
        input=content,
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["process"]["id"] == "wash_n_fold"
    assert payload["path_summary"]["path_count"] == 1


def test_cli_inspect_model_reports_portable_composition() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("parts").mkdir()
        Path("parts/flow.flo").write_text(
            """
steps:
  - id: start
    kind: start
  - id: end
    kind: end
transitions:
  - source: start
    target: end
""".strip(),
            encoding="utf-8",
        )
        Path("process.flo").write_text(
            """
spec_version: "0.1"
process:
  id: composed
  name: Composed
includes:
  - parts/flow.flo
""".strip(),
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            ["inspect", "process.flo", "--analysis", "model", "--format", "json"],
        )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["composition"] == {
        "composed": True,
        "entry_source": "process.flo",
        "included_sources": ["parts/flow.flo"],
        "source_count": 2,
    }
    assert payload["process"]["id"] == "composed"


def test_cli_inspect_model_from_stdin_reports_portable_entry() -> None:
    runner = CliRunner()
    content = Path("examples/reference/washnfold.flo").read_text(encoding="utf-8")

    result = runner.invoke(
        cli,
        ["inspect", "-", "--analysis", "model", "--format", "json"],
        input=content,
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["composition"]["entry_source"] == "<stdin>"
    assert payload["composition"]["included_sources"] == []


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
    assert "structure" in result.output
    assert "model" in result.output
    assert "--for-analysis" in result.output
    assert "--for-diagram" in result.output
    assert "[default: timing]" in result.output
    assert "[default: text]" in result.output
