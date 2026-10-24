"""Release acceptance for physical dimensions through the actual CLI."""

import xml.etree.ElementTree as ET
from pathlib import Path

from click.testing import CliRunner

from flo.app.cli import cli
from flo.errors import EXIT_RENDER_ERROR

SOURCE = (
    Path(__file__).resolve().parents[2]
    / "examples/conformance/valid/valid_basic_linear.flo"
)


def test_physical_units_produce_identical_exact_canvas_and_repeatable_svg(tmp_path):
    units = [
        ("816px", "1056px"),
        ("8.5in", "11in"),
        ("21.59cm", "27.94cm"),
        ("215.9mm", "279.4mm"),
    ]
    artifacts = []
    runner = CliRunner()
    for width, height in units:
        output = tmp_path / f"render-{width}.svg"
        command = [
            "render",
            str(SOURCE),
            "--layout-width",
            width,
            "--layout-height",
            height,
            "--render-to",
            str(output),
        ]
        first = runner.invoke(cli, command)
        assert first.exit_code == 0, first.output
        content = output.read_bytes()
        root = ET.fromstring(content)
        assert (root.get("width"), root.get("height")) == ("816", "1056")
        second = runner.invoke(cli, command)
        assert second.exit_code == 0, second.output
        assert output.read_bytes() == content
        artifacts.append(content)
    assert all(artifact == artifacts[0] for artifact in artifacts)


def test_unreadable_exact_canvas_fails_and_expand_preserves_full_diagram(tmp_path):
    runner = CliRunner()
    output = tmp_path / "diagram.svg"
    command = [
        "render",
        str(SOURCE),
        "--layout-width",
        "4in",
        "--layout-height",
        "1mm",
        "--render-to",
        str(output),
    ]
    failed = runner.invoke(cli, command)
    assert failed.exit_code == EXIT_RENDER_ERROR, failed.output
    assert not output.exists()
    expanded = runner.invoke(cli, [*command, "--layout-overflow", "expand"])
    assert expanded.exit_code == 0, expanded.output
    root = ET.fromstring(output.read_bytes())
    assert float(root.get("width")) >= 384
    assert float(root.get("height")) > 4
    viewbox = list(map(float, root.get("viewBox").split()))
    assert viewbox[2:] == [float(root.get("width")), float(root.get("height"))]


def test_book_golden_matches_public_cli_geometry_pipeline(tmp_path):
    root = Path(__file__).resolve().parents[2]
    output = tmp_path / "book.svg"
    result = CliRunner().invoke(
        cli,
        [
            "render",
            str(root / "examples/reference/book_washnfold.flo"),
            "--diagram",
            "sppm",
            "--sppm-theme",
            "mpi-lms",
            "--sppm-output-profile",
            "book",
            "--background-color",
            "transparent",
            "--no-header",
            "--no-footer",
            "--layout-width",
            "1200px",
            "--layout-wrap",
            "auto",
            "--layout-max-width-px",
            "1200",
            "--render-to",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (
        output.read_bytes()
        == (
            root / "tests/golden/sppm/book_washnfold_local_rework/render.svg"
        ).read_bytes()
    )
