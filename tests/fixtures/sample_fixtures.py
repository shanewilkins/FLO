"""Test fixtures providing temporary files used in integration tests."""

import tempfile
import pathlib
from pathlib import Path

import pytest

from flo.adapters.models import AdapterModel


def _repo_root(start: Path | None = None) -> Path:
    start = start or Path(__file__).resolve()
    cur = start
    while cur != cur.parent:
        if (cur / "examples").is_dir():
            return cur
        cur = cur.parent
    raise RuntimeError("repo root with examples/ not found")


@pytest.fixture
def tmp_flo_file():
    """Create a temporary .flo file seeded with a real example and yield its Path.

    This uses the first example from the `examples/` directory so integration
    tests exercise the real parsing/compilation pipeline instead of a stub.
    """
    examples_dir = _repo_root() / "examples"
    example = sorted(examples_dir.glob("*.flo"))[0]
    content = example.read_text()

    with tempfile.NamedTemporaryFile("w+", suffix=".flo", delete=False) as fh:
        fh.write(content)
        fh.flush()
        yield pathlib.Path(fh.name)

    try:
        pathlib.Path(fh.name).unlink()
    except Exception:
        pass


@pytest.fixture
def adapter_model_from_example():
    """Yield a real `AdapterModel` instance constructed from an example file.

    Tests can use this fixture to get a validated model rather than building
    one manually or mocking the parsing step.
    """
    examples_dir = _repo_root() / "examples"
    example = sorted(examples_dir.glob("*.flo"))[0]
    content = example.read_text()
    model = AdapterModel.model_validate({"name": example.stem, "content": content})
    return model
