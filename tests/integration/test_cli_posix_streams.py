from click.testing import CliRunner

from flo.core.cli import cli


def test_validate_writes_no_stdout_on_success():
    runner = CliRunner()
    content = """spec_version: \"0.1\"

process:
  id: p

steps:
  - id: start
    kind: start
  - id: end
    kind: end

transitions:
  - source: start
    target: end
"""

    result = runner.invoke(cli, ["validate", "-"], input=content)
    assert result.exit_code == 0
    assert result.output == ""


def test_validate_reports_errors_to_stderr_stream():
    runner = CliRunner()
    invalid = """spec_version: \"0.1\"

process:
  id: bad

steps:
  - id: only_task
    kind: task
"""

    result = runner.invoke(cli, ["validate", "-"], input=invalid)
    assert result.exit_code != 0
    assert "E1003" in result.output


def test_parse_error_class_surfaces_nonzero_and_message():
    runner = CliRunner()
    # Invalid YAML should bubble into ParseError handling.
    invalid_yaml = "spec_version: \"0.1\"\nprocess:\n\tbad: true\n"
    result = runner.invoke(cli, ["validate", "-"], input=invalid_yaml)
    assert result.exit_code != 0
    assert "found character '\\t'" in result.output or "while scanning" in result.output
