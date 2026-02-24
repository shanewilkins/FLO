from pathlib import Path
from click.testing import CliRunner

from flo.cli import cli


def _repo_root(start: Path | None = None) -> Path:
    start = start or Path(__file__).resolve()
    cur = start
    while cur != cur.parent:
        if (cur / "examples").is_dir():
            return cur
        cur = cur.parent
    raise RuntimeError("repo root with examples/ not found")


def test_cli_writes_dot_file(tmp_path: Path):
    runner = CliRunner()
    examples = sorted((_repo_root() / "examples").glob("*.flo"))
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
