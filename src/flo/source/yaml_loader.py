"""Compatibility loader for the name/content envelope using required Pydantic."""

from __future__ import annotations

import yaml

from .models import AdapterModel


def load_adapter_from_yaml(content: str) -> AdapterModel:
    """Parse YAML content and return an `AdapterModel`.

    Expects the YAML to be a mapping containing at least `name` and
    `content` keys. Returns an `AdapterModel` instance via the
    Pydantic `model_validate` API. Process documents use the composed source
    mapping and compiler shape models instead of this envelope.
    """
    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        raise ValueError(
            "YAML content must be a mapping with keys 'name' and 'content'"
        )

    return AdapterModel.model_validate(data)
