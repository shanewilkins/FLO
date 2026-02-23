"""YAML adapter loader.

Parses YAML content and returns an `AdapterModel` instance when
Pydantic is available, otherwise returns a simple fallback model.
"""
from __future__ import annotations

import yaml

from .models import AdapterModel


def load_adapter_from_yaml(content: str) -> AdapterModel:
    """Parse YAML content and return an `AdapterModel`.

    Expects the YAML to be a mapping containing at least `name` and
    `content` keys. Returns an `AdapterModel` instance via the
    model-compatible `model_validate` API (works with Pydantic and
    our fallback model).
    """
    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        raise ValueError("YAML content must be a mapping with keys 'name' and 'content'")

    # Both the Pydantic model and our fallback implement `model_validate`.
    return AdapterModel.model_validate(data)
