import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from flo.app.cli import cli


def test_validate_writes_no_stdout_on_success():
    runner = CliRunner()
    content = """spec_version: \"0.1\"

process:
  id: p
  name: Process

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
  name: Bad Process

steps:
  - id: only_task
    kind: task
"""

    result = runner.invoke(cli, ["validate", "-"], input=invalid)
    assert result.exit_code != 0
    assert "E1003" in result.output


def test_validate_json_serializes_source_diagnostic():
    runner = CliRunner()
    invalid = """spec_version: "0.1"

process:
  id: bad
  name: Bad Process

steps:
  - id: start
    kind: start
  - id: only_task
    kind: task
    metadata:
      wait_time: {value: 30, unit: min}
  - id: end
    kind: end

transitions:
  - source: start
    target: only_task
  - source: only_task
    target: end
"""

    result = runner.invoke(cli, ["validate", "-", "--format", "json"], input=invalid)

    assert result.exit_code == 4
    diagnostic = json.loads(result.output)
    assert diagnostic["code"] == "E1503"
    assert diagnostic["severity"] == "error"
    assert diagnostic["source"] == "<stdin>"
    assert diagnostic["field_path"] == "steps.only_task.metadata.wait_time"
    assert diagnostic["suggestion"] == "Move wait_time to a queue step."


def test_validate_json_includes_composition_chain():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("process.flo").write_text(
            'includes: ["parts/missing.flo"]\n', encoding="utf-8"
        )

        result = runner.invoke(
            cli,
            ["validate", "process.flo", "--format", "json"],
        )

    assert result.exit_code == 2
    diagnostic = json.loads(result.output)
    assert diagnostic["code"] == "E0002"
    assert diagnostic["source"] == "process.flo"
    assert diagnostic["include_chain"][0].endswith("process.flo")
    assert diagnostic["include_chain"][1].endswith("parts/missing.flo")


def test_parse_error_class_surfaces_nonzero_and_message():
    runner = CliRunner()
    # Invalid YAML should bubble into ParseError handling.
    invalid_yaml = 'spec_version: "0.1"\nprocess:\n\tbad: true\n'
    result = runner.invoke(cli, ["validate", "-"], input=invalid_yaml)
    assert result.exit_code != 0
    assert "found character '\\t'" in result.output or "while scanning" in result.output


@pytest.mark.parametrize(
    ("steps_yaml", "message"),
    [
        ("[]", "steps must contain at least one step"),
        ("[not-an-object]", "steps[0] must be an object"),
        ("[{kind: task}]", "steps[0].id must be a non-empty string"),
        ("[{id: '' , kind: task}]", "steps[0].id must be a non-empty string"),
        ("[{id: work}]", "steps[0].kind must be a non-empty string"),
        ("[{id: work, kind: unknown}]", "steps[0].kind must be one of"),
        (
            "[{id: work, kind: task}, {id: work, kind: task}]",
            "duplicate step id 'work'",
        ),
    ],
)
def test_validate_rejects_malformed_authored_step_shape(
    steps_yaml: str, message: str
) -> None:
    content = f"""spec_version: "0.1"

process:
  id: malformed
  name: Malformed

steps: {steps_yaml}
"""

    result = CliRunner().invoke(cli, ["validate", "-"], input=content)

    assert result.exit_code != 0
    assert message in result.output
