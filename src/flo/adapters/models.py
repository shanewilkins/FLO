"""Adapter models for FLO inputs.

Prefer Pydantic v2 models for runtime validation and parsing. If
Pydantic isn't available the module will still import but some helper
callers may choose a dict-based fallback.
"""

from __future__ import annotations

from pydantic import BaseModel


class AdapterModel(BaseModel):
    """Pydantic-backed AdapterModel used for adapter inputs."""

    name: str
    content: str

    # Pydantic v2 provides `model_validate` and `model_dump` so callers
    # can use the same API as before without needing a runtime fallback.
