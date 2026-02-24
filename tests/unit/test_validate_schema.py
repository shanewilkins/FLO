import json
import io
import pytest
from pathlib import Path

import flo.compiler.ir.validate as validate_mod
from flo.compiler.ir.models import IR
from flo.services.errors import ValidationError


def test_validate_against_schema_missing_schema(monkeypatch, node_factory):
    # force schema path to appear missing
    monkeypatch.setattr(Path, "exists", lambda self: False)
    ir = IR(name="x", nodes=[node_factory("n")])
    with pytest.raises(ValidationError):
        validate_mod.validate_against_schema(ir)


def test_validate_against_schema_jsonschema_missing(monkeypatch, node_factory):
    # ensure schema file exists but jsonschema is reported unavailable
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(validate_mod, "_JSONSCHEMA_AVAILABLE", False)
    ir = IR(name="x", nodes=[node_factory("n")])
    with pytest.raises(RuntimeError):
        validate_mod.validate_against_schema(ir)


def test_validate_against_schema_validate_raises(monkeypatch, node_factory):
    # simulate jsonschema.validate raising an error -> ValidationError
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(validate_mod, "_JSONSCHEMA_AVAILABLE", True)

    class DummyJS:
        @staticmethod
        def validate(instance=None, schema=None):
            raise Exception("boom")

    monkeypatch.setattr(validate_mod, "jsonschema", DummyJS)

    ir = IR(name="x", nodes=[node_factory("n")])
    # ensure open returns a valid JSON schema stub
    monkeypatch.setattr(Path, "open", lambda self, *a, **k: io.StringIO(json.dumps({})))
    with pytest.raises(ValidationError):
        validate_mod.validate_against_schema(ir)


def test_validate_against_schema_success(monkeypatch, tmp_path, node_factory):
    # simulate successful jsonschema.validate (no exception)
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(validate_mod, "_JSONSCHEMA_AVAILABLE", True)

    class DummyJS:
        @staticmethod
        def validate(instance=None, schema=None):
            return None

    monkeypatch.setattr(validate_mod, "jsonschema", DummyJS)

    ir = IR(name="x", nodes=[node_factory("n")])
    # should not raise
    # ensure open returns a valid JSON schema stub
    monkeypatch.setattr(Path, "open", lambda self, *a, **k: io.StringIO(json.dumps({})))
    validate_mod.validate_against_schema(ir)
