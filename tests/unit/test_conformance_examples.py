from pathlib import Path

import pytest

from flo import api
from flo.errors import ValidationError
from flo.process.ir import ensure_schema_aligned, validate_ir
from flo.source import compile_adapter, parse_adapter
from tests.fixtures.sample_fixtures import repo_root


def _conformance_files(kind: str) -> list[Path]:
    return sorted((repo_root() / "examples" / "conformance" / kind).glob("*.flo"))


@pytest.mark.parametrize("example_file", _conformance_files("valid"))
def test_conformance_valid_examples_pass_validation(example_file: Path):
    content = example_file.read_text(encoding="utf-8")
    adapter = parse_adapter(content, source_path=str(example_file))
    ir = compile_adapter(adapter)
    validate_ir(ir)
    ensure_schema_aligned(ir)
    for operation in (api.validate, api.inspect, api.export):
        result = operation(content, source_path=str(example_file))
        assert result.ok, result.diagnostics
    assert api.export(content).value == api.export(content).value


@pytest.mark.parametrize("example_file", _conformance_files("invalid"))
def test_conformance_invalid_examples_fail_validation(example_file: Path):
    content = example_file.read_text(encoding="utf-8")
    adapter = parse_adapter(content, source_path=str(example_file))
    with pytest.raises((ValueError, ValidationError)):
        validate_ir(compile_adapter(adapter))


@pytest.mark.parametrize("example_file", _conformance_files("invalid"))
def test_invalid_conformance_examples_fail_public_api(example_file: Path):
    content = example_file.read_text(encoding="utf-8")
    for operation in (api.validate, api.inspect, api.export):
        result = operation(content, source_path=str(example_file))
        assert not result.ok
        assert result.value is None
        assert result.diagnostics[0].message
