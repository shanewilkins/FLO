from pathlib import Path

import pytest

from flo.app import run_content
from flo.errors import EXIT_SUCCESS, ParseError
from tests.fixtures.sample_fixtures import repo_root


def _reference_files() -> list[Path]:
    return sorted((repo_root() / "examples" / "reference").glob("*.flo"))


@pytest.mark.parametrize("example_file", _reference_files(), ids=lambda p: p.stem)
def test_run_content_with_example_file(example_file: Path):
    content = example_file.read_text()
    rc, out, err = run_content(content, options={"source_path": str(example_file)})

    assert rc == EXIT_SUCCESS
    assert "<svg" in out
    assert all(line.startswith("timing-") for line in err.splitlines())


def test_run_content_empty_is_rejected():
    with pytest.raises(ParseError, match="YAML mapping"):
        run_content("")
