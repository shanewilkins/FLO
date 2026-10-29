"""Generated canonical exchange schema verification."""

import json
from pathlib import Path

from flo.errors import ValidationError
from flo.process.validation_errors import LocatedValidationError

from .models import IR
from .schema_projection import ir_to_schema_dict
from .validate_render_intent import validate_render_intent

try:
    import jsonschema

    _JSONSCHEMA_AVAILABLE = True
except Exception:  # pragma: no cover - optional
    jsonschema = None
    _JSONSCHEMA_AVAILABLE = False


def validate_against_schema(ir: IR) -> None:
    """Validate an `IR` instance against the JSON schema file.

    Raises `ValidationError` on schema validation failure.
    """
    schema_path = _locate_schema("flo_ir.json")

    if not _JSONSCHEMA_AVAILABLE:
        raise RuntimeError("jsonschema package not available for schema validation")

    with schema_path.open("r", encoding="utf-8") as fh:
        schema = json.load(fh)

    instance = ir_to_schema_dict(ir)
    validate_fn = getattr(jsonschema, "validate", None)
    if not callable(validate_fn):
        raise RuntimeError("jsonschema.validate is not available for schema validation")

    try:
        validate_fn(instance=instance, schema=schema)
    except Exception as exc:
        location = tuple(getattr(exc, "absolute_path", ()))
        path = (
            "".join(
                f"[{part}]"
                if isinstance(part, int)
                else ("." if index else "") + str(part)
                for index, part in enumerate(location)
            )
            or "document"
        )
        constraint = getattr(exc, "validator", None)
        if constraint not in {
            "type",
            "required",
            "additionalProperties",
            "enum",
            "const",
            "pattern",
            "minimum",
            "minItems",
            "anyOf",
            "oneOf",
        }:
            constraint = "contract"
        raise LocatedValidationError(
            f"schema validation failed: {path} violates the canonical {constraint} constraint",
            location,
        ) from exc


def ensure_schema_aligned(ir: object) -> None:
    """Ensure the given IR is valid against the schema export contract."""
    if not isinstance(ir, IR):
        raise ValidationError("compiled output is not an IR instance")

    validate_against_schema(ir)
    validate_render_intent(ir)


def _locate_schema(name: str) -> Path:
    here = Path(__file__).resolve()
    candidates = [
        # Preferred: packaged schema payload at flo/process/schema/*.json
        here.parents[1] / "schema" / name,
        # Local repo layout when running from source tree.
        here.parents[4] / "schema" / name,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise ValidationError(f"schema file not found: {candidates[0]}")
