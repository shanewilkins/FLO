from pathlib import Path
from click.testing import CliRunner

from flo.core.cli import cli
from tests.fixtures.sample_fixtures import repo_root


def test_cli_writes_dot_file(tmp_path: Path):
    runner = CliRunner()
    examples = sorted((repo_root() / "examples" / "reference").glob("*.flo"))
    assert examples, "no example files found"
    example = examples[0]

    out = tmp_path / "out.dot"
    result = runner.invoke(cli, ["run", str(example), "-o", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    # assert DOT header and a minimal content snippet
    assert content.strip().startswith("digraph")
    assert "{" in content and "}" in content
