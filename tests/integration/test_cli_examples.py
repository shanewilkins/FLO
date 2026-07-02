from click.testing import CliRunner
import json

from flo.core.cli import cli
from tests.fixtures.sample_fixtures import repo_root


def test_cli_run_all_examples():
    runner = CliRunner()
    examples = sorted((repo_root() / "examples" / "reference").glob("*.flo"))
    assert examples, "No example files found for integration test"

    for ex in examples:
        result = runner.invoke(cli, ["run", str(ex)])
        # basic sanity: CLI returns success and prints rendered SVG
        assert result.exit_code == 0
        assert "<svg" in result.output


def test_cli_compile_canonical_reference_examples_emit_expected_json():
    runner = CliRunner()
    cases = [
        (
            repo_root() / "examples" / "reference" / "new_semantics.flo",
            "canonical_semantics_reference",
            {"parallel_split", "parallel_join"},
        ),
        (
            repo_root() / "examples" / "reference" / "semantic_controls_showcase.flo",
            "semantic_controls_showcase",
            {"parallel_split", "parallel_join", "decision"},
        ),
    ]

    for example_path, expected_process_id, expected_kinds in cases:
        result = runner.invoke(cli, ["compile", str(example_path)])

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["process"]["id"] == expected_process_id
        node_kinds = {node["kind"] for node in payload["nodes"]}
        assert expected_kinds.issubset(node_kinds)
