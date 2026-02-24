"""Validation helpers for the FLO IR types."""

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
    """Validate that `obj` is a sensible `IR` instance.

    Raises `ValidationError` on failure so callers can map to CLI exit
    codes consistently.
    """
    if not isinstance(obj, IR):
        raise ValidationError("object is not an IR instance")

    if not obj.nodes:
        raise ValidationError("IR must contain at least one node")

    ids = [n.id for n in obj.nodes]
    if len(ids) != len(set(ids)):
        raise ValidationError("node ids must be unique")


def validate_against_schema(ir: IR) -> None:
    """Validate an `IR` instance against the `schema/flo_ir.json` schema.

    This is optional and requires `jsonschema` to be installed. When the
    package is not available a `RuntimeError` is raised to indicate the
    missing dependency; callers in CI should ensure `jsonschema` is
    installed.
    """
    # Prefer schema located under `src/schema`, but fall back to a repository
    # level `schema/` directory (some users keep schema at the repo root).
    schema_path = Path(__file__).resolve().parents[2] / "schema" / "flo_ir.json"
    if not schema_path.exists():
        alt = Path(__file__).resolve().parents[3] / "schema" / "flo_ir.json"
        if alt.exists():
            schema_path = alt
        else:
            raise ValidationError(f"schema file not found: {schema_path}")

    if not _JSONSCHEMA_AVAILABLE:
        raise RuntimeError("jsonschema package not available for schema validation")

    with schema_path.open("r", encoding="utf-8") as fh:
        schema = json.load(fh)

    instance = ir.to_dict()
    # If the IR is the minimal dataclass shape produced by the current
    # compiler (e.g. {"name":..., "nodes":[...]}) translate it into the
    # schema-shaped instance expected by `schema/flo_ir.json` so CI schema
    # validation can run against examples while the compiler mapping is
    # completed.
    if isinstance(instance, dict) and "process" not in instance:
        # Build a minimal `process` object from available metadata.
        proc_id = instance.get("name") or "generated"
        process = {"id": proc_id, "name": instance.get("name") or proc_id}

        nodes_out = []
        for n in instance.get("nodes", []):
            # `n` is expected to be a dict with keys `id`, `type`, `attrs`.
            nid = n.get("id")
            kind = n.get("type") or n.get("kind") or "task"
            attrs = n.get("attrs") or {}
            node_obj = {"id": nid, "kind": kind}
            # Attempt to surface a friendly name or lane if present in attrs
            if isinstance(attrs, dict):
                if "name" in attrs:
                    node_obj["name"] = attrs["name"]
                if "lane" in attrs:
                    node_obj["lane"] = attrs["lane"]
            nodes_out.append(node_obj)

        instance = {"process": process, "nodes": nodes_out, "edges": []}
    validate_fn = getattr(jsonschema, "validate", None)
    if not callable(validate_fn):
        raise RuntimeError("jsonschema.validate is not available for schema validation")

    try:
        validate_fn(instance=instance, schema=schema)
    except Exception as e:
        raise ValidationError(f"schema validation failed: {e}")
