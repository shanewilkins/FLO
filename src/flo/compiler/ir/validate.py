"""Validation helpers for the FLO IR types (now under compiler.ir)."""
from __future__ import annotations

from typing import Any

from .models import IR
from flo.services.errors import ValidationError
from pathlib import Path
import json

try:
    import jsonschema  # type: ignore
    _JSONSCHEMA_AVAILABLE = True
except Exception:  # pragma: no cover - optional
    jsonschema = None  # type: ignore
    _JSONSCHEMA_AVAILABLE = False


def validate_ir(obj: Any) -> None:
    """Validate a basic IR instance for structural correctness.

    Raises `ValidationError` on failure.
    """
    if not isinstance(obj, IR):
        raise ValidationError("object is not an IR instance")

    if not obj.nodes:
        raise ValidationError("IR must contain at least one node")

    ids = [n.id for n in obj.nodes]
    if len(ids) != len(set(ids)):
        raise ValidationError("node ids must be unique")


def validate_against_schema(ir: IR) -> None:
    """Validate an `IR` instance against the JSON schema file.

    Raises `ValidationError` on schema validation failure.
    """
    schema_path = _locate_schema("flo_ir.json")

    if not _JSONSCHEMA_AVAILABLE:
        raise RuntimeError("jsonschema package not available for schema validation")

    with schema_path.open("r", encoding="utf-8") as fh:
        schema = json.load(fh)

    instance = ir.to_dict()
    validate_fn = getattr(jsonschema, "validate", None)
    if not callable(validate_fn):
        raise RuntimeError("jsonschema.validate is not available for schema validation")

    try:
        validate_fn(instance=instance, schema=schema)
    except Exception as e:
        raise ValidationError(f"schema validation failed: {e}")


def ensure_schema_aligned(ir: object) -> None:
    """Ensure the given IR is schema_aligned and valid against the schema."""
    if not isinstance(ir, IR):
        raise ValidationError("compiled output is not an IR instance")

    if not getattr(ir, "schema_aligned", False):
        raise ValidationError("compiled IR is not schema_aligned; compiler must emit schema-shaped IR")

    validate_against_schema(ir)


def _locate_schema(name: str) -> Path:
    candidate = Path(__file__).resolve().parents[3] / "schema" / name
    if candidate.exists():
        return candidate
    alt = Path(__file__).resolve().parents[4] / "schema" / name
    if alt.exists():
        return alt
    raise ValidationError(f"schema file not found: {candidate}")
