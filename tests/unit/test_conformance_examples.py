from pathlib import Path

import pytest

from flo.adapters import parse_adapter
from flo.compiler import compile_adapter
from flo.compiler.ir import validate_ir
from flo.services.errors import ValidationError


def _repo_root(start: Path | None = None) -> Path:
    start = start or Path(__file__).resolve()
    cur = start
    while cur != cur.parent:
        if (cur / "examples").is_dir():
            return cur
        cur = cur.parent
    raise RuntimeError("repo root with examples/ not found")


def _conformance_files(kind: str) -> list[Path]:
    return sorted((_repo_root() / "examples" / "conformance" / kind).glob("*.flo"))


@pytest.mark.parametrize("example_file", _conformance_files("valid"))
def test_conformance_valid_examples_pass_validation(example_file: Path):
    content = example_file.read_text(encoding="utf-8")
    adapter = parse_adapter(content)
    ir = compile_adapter(adapter)
    validate_ir(ir)


@pytest.mark.parametrize("example_file", _conformance_files("invalid"))
def test_conformance_invalid_examples_fail_validation(example_file: Path):
    content = example_file.read_text(encoding="utf-8")
    adapter = parse_adapter(content)
    ir = compile_adapter(adapter)
    with pytest.raises(ValidationError):
        validate_ir(ir)
