import pytest

from flo.compiler.ir.validate import ensure_schema_aligned
from flo.compiler.ir.models import IR, Node
from flo.services.errors import ValidationError
from flo.core import run_content


def test_ensure_schema_aligned_non_ir_raises():
    with pytest.raises(ValidationError):
        ensure_schema_aligned(object())


def test_ensure_schema_aligned_schema_valid_passes():
    ir = IR(name="x", nodes=[Node(id="n", type="task")])
    ensure_schema_aligned(ir)


def test_ensure_schema_aligned_schema_invalid_raises():
    # Use a node kind that is not allowed by the JSON Schema to trigger
    # schema validation failure.
    ir = IR(name="p", nodes=[Node(id="n", type="process")])
    with pytest.raises(ValidationError):
        ensure_schema_aligned(ir)


def test_run_content_compiled_schema_invalid_raises(monkeypatch):
    # parse returns a valid IR; compile returns an IR that fails schema export validation
    monkeypatch.setattr("flo.core.parse_adapter", lambda c: IR(name="t", nodes=[Node(id="n", type="task")]))
    monkeypatch.setattr("flo.core.compile_adapter", lambda a: IR(name="t", nodes=[Node(id="n", type="process")]))
    monkeypatch.setattr("flo.core.validate_ir", lambda i: None)
    with pytest.raises(ValidationError):
        run_content("some content")
