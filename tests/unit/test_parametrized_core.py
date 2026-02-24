import pytest

from pathlib import Path

from flo.core import run_content
from flo.services.errors import EXIT_SUCCESS


def _repo_root(start: Path | None = None) -> Path:
    start = start or Path(__file__).resolve()
    cur = start
    while cur != cur.parent:
        if (cur / "examples").is_dir():
            return cur
        cur = cur.parent
    raise RuntimeError("repo root with examples/ not found")


def test_run_content_with_example_files():
    """Run the core pipeline on each example file to exercise real behavior.

    This ensures tests operate on real data and avoid unnecessary mocking
    of the pipeline steps.
    """
    examples = sorted((_repo_root() / "examples").glob("*.flo"))
    if not examples:
        pytest.skip("no example files available")

    for example_file in examples:
        content = example_file.read_text()
        rc, out, err = run_content(content)

        assert rc == EXIT_SUCCESS
        assert "digraph" in out
        assert err == ""


def test_run_content_empty_returns_placeholder():
    rc, out, err = run_content("")
    assert rc == EXIT_SUCCESS
    assert out == ""
    assert err == ""
