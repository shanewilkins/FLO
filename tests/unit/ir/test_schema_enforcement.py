import pytest

from flo.compiler.ir.validate import ensure_schema_aligned
from flo.compiler.ir.models import IR, Node
from flo.services.errors import ValidationError
from flo.core import run_content


def test_ensure_schema_aligned_non_ir_raises():
    with pytest.raises(ValidationError):
        ensure_schema_aligned(object())


def test_ensure_schema_aligned_not_schema_aligned_raises():
    ir = IR(name="x", nodes=[Node(id="n", type="task")], schema_aligned=False)
    with pytest.raises(ValidationError):
        ensure_schema_aligned(ir)


def test_ensure_schema_aligned_schema_invalid_raises():
    # Use a node kind that is not allowed by the JSON Schema to trigger
    # schema validation failure even when `schema_aligned=True`.
    ir = IR(name="p", nodes=[Node(id="n", type="process")], schema_aligned=True)
    with pytest.raises(ValidationError):
        ensure_schema_aligned(ir)


def test_run_content_compiled_not_schema_aligned_raises(monkeypatch):
    # parse returns a valid IR; compile returns a non-schema-aligned IR
    monkeypatch.setattr("flo.core.parse_adapter", lambda c: IR(name="t", nodes=[Node(id="n", type="task")], schema_aligned=True))
    monkeypatch.setattr("flo.core.compile_adapter", lambda a: IR(name="t", nodes=[Node(id="n", type="task")], schema_aligned=False))
    monkeypatch.setattr("flo.core.validate_ir", lambda i: None)
    with pytest.raises(ValidationError):
        run_content("some content")
