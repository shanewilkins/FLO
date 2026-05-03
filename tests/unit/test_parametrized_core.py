import pytest

from pathlib import Path

from flo.core import run_content
from flo.services.errors import EXIT_SUCCESS
from tests.fixtures.sample_fixtures import repo_root


def _reference_files() -> list[Path]:
    return sorted((repo_root() / "examples" / "reference").glob("*.flo"))


@pytest.mark.parametrize("example_file", _reference_files(), ids=lambda p: p.stem)
def test_run_content_with_example_file(example_file: Path):
    content = example_file.read_text()
    rc, out, err = run_content(content, options={"source_path": str(example_file)})

    assert rc == EXIT_SUCCESS
    assert "digraph" in out
    assert err == ""


def test_run_content_empty_returns_placeholder():
    rc, out, err = run_content("")
    assert rc == EXIT_SUCCESS
    assert out == ""
    assert err == ""
