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


def parse_adapter(content: str, source_path: str | None = None) -> dict[str, Any]:
    """Parse one YAML mapping and compose includes without translating aliases."""
    source_bytes = len(content.encode("utf-8"))
    if source_bytes > MAX_SOURCE_BYTES:
        raise ValueError(f"FLO source exceeds {MAX_SOURCE_BYTES} byte limit")

    parsed = yaml.safe_load(content)
    if not isinstance(parsed, dict):
        raise ValueError("FLO source must contain a YAML mapping")
    return resolve_includes(
        parsed,
        source_path=source_path,
        root_source_bytes=source_bytes,
        capture_composition=True,
        root_content=content,
    )


__all__ = [
    "SourceComposition",
    "compile_adapter",
    "parse_adapter",
    "pop_source_composition",
]
