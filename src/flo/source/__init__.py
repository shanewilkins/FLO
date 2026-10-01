"""Adapters package: YAML/other input adapters for FLO."""

from __future__ import annotations

from typing import Any

import yaml

from .compile import compile_adapter
from .composition import (
    MAX_SOURCE_BYTES,
    SourceComposition,
    pop_source_composition,
    resolve_includes,
)
from .yaml_loader import load_adapter_from_yaml


def parse_adapter(content: str, source_path: str | None = None) -> dict[str, Any]:
    """Parse adapter content and return a validated mapping.

    This dispatcher currently supports YAML input via
    `load_adapter_from_yaml`. The loader returns an `AdapterModel`
    which we convert to a plain dict (`model_dump`) so downstream
    compiler code can continue to operate on mappings.
    """
    source_bytes = len(content.encode("utf-8"))
    if source_bytes > MAX_SOURCE_BYTES:
        raise ValueError(f"FLO source exceeds {MAX_SOURCE_BYTES} byte limit")

    try:
        model = load_adapter_from_yaml(content)
    except ValueError:
        # If the content is YAML mapping-shaped FLO, normalize it to the
        # compiler-facing contract keys.
        # Otherwise preserve the previous permissive text fallback.
        parsed = yaml.safe_load(content)
        if isinstance(parsed, dict):
            resolved = resolve_includes(
                parsed,
                source_path=source_path,
                root_source_bytes=source_bytes,
                capture_composition=True,
            )
            return _normalize_compiler_contract_payload(resolved)
        return {"name": "parsed", "content": content}

    # `model` supports `model_dump()` for Pydantic compatibility
    try:
        payload = model.model_dump()
        return _normalize_compiler_contract_payload(payload)
    except Exception:
        # Fallback: if the model does not implement `model_dump`, try
        # converting via `dict()` for compatibility with lightweight
        # fallback models.
        payload = dict(model)
        return _normalize_compiler_contract_payload(payload)


def _normalize_compiler_contract_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize parser output to strict compiler contract keys."""
    normalized: dict[str, Any] = dict(payload)
    if "transitions" not in normalized and "edges" in normalized:
        normalized["transitions"] = normalized.pop("edges")
    return normalized


__all__ = [
    "SourceComposition",
    "compile_adapter",
    "load_adapter_from_yaml",
    "parse_adapter",
    "pop_source_composition",
]
