"""Test fixtures providing temporary files used in integration tests."""

import tempfile
import pathlib

import pytest


@pytest.fixture
def tmp_flo_file():
    """Create a temporary .flo file and yield its path as a string.

    Useful for integration tests that need a sample input file.
    """
    with tempfile.NamedTemporaryFile("w+", suffix=".flo", delete=False) as fh:
        fh.write("# sample flo content\n")
        fh.flush()
        yield pathlib.Path(fh.name)

    try:
        pathlib.Path(fh.name).unlink()
    except Exception:
        pass
