"""Configuration-file validation through the public CLI boundary."""

from click.testing import CliRunner

from flo.app.cli import cli
from flo.errors import EXIT_USAGE

_MODEL = """spec_version: '0.1'
process:
  id: config_demo
  name: Config demo
steps:
  - {id: start, kind: start}
  - {id: work, kind: task}
  - {id: end, kind: end}
transitions:
  - {source: start, target: work}
  - {source: work, target: end}
"""


def test_invalid_toml_config_emits_usage_error_and_no_payload(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    model = tmp_path / "demo.flo"
    model.write_text(_MODEL, encoding="utf-8")
    (tmp_path / "diagrams.toml").write_text(
        "[sppm.text.max_label]\nworkers = true", encoding="utf-8"
    )

    result = CliRunner().invoke(cli, ["render", str(model)])

    assert result.exit_code == EXIT_USAGE
    assert result.stdout == ""
    assert "sppm.text.max_label.workers" in result.stderr
    assert "expected a positive integer" in result.stderr
    assert "Traceback" not in result.stderr


def test_valid_toml_shared_style_reaches_rendered_svg(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    model = tmp_path / "demo.flo"
    model.write_text(_MODEL, encoding="utf-8")
    (tmp_path / "diagrams.toml").write_text(
        "[render]\ntheme = 'mono'\n[render.style.typography]\nscale = 1.1",
        encoding="utf-8",
    )

    result = CliRunner().invoke(cli, ["render", str(model)])

    assert result.exit_code == 0, result.output
    assert "<svg" in result.stdout
    assert 'data-flo-theme="monochrome"' in result.stdout
