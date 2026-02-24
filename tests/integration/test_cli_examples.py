from pathlib import Path
from click.testing import CliRunner

from flo.core.cli import cli


def _repo_root(start: Path | None = None) -> Path:
    start = start or Path(__file__).resolve()
    cur = start
    while cur != cur.parent:
        if (cur / "examples").is_dir():
            return cur
        cur = cur.parent
    raise RuntimeError("repo root with examples/ not found")


def test_cli_run_all_examples():
    runner = CliRunner()
    examples = sorted((_repo_root() / "examples").glob("*.flo"))
    assert examples, "No example files found for integration test"

    for ex in examples:
        result = runner.invoke(cli, ["run", str(ex)])
        # basic sanity: CLI returns success and prints the rendered DOT
        assert result.exit_code == 0
        assert "digraph" in result.output
