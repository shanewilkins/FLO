from __future__ import annotations

from typing import Any, Dict


def parse_adapter(content: str) -> Dict[str, Any]:
    """Minimal adapter parser stub.

    Returns a simple dict so downstream compiler stubs can operate.
    """
    return {"name": "parsed", "content": content}
"""Adapters package: YAML/other input adapters for FLO."""
from .yaml_loader import load_adapter_from_yaml

__all__ = ["load_adapter_from_yaml"]
