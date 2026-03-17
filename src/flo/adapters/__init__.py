"""Adapters package: YAML/other input adapters for FLO."""

from __future__ import annotations

from typing import Any, Dict
import yaml


from .yaml_loader import load_adapter_from_yaml
from .composition import resolve_includes


def parse_adapter(content: str, source_path: str | None = None) -> Dict[str, Any]:
	"""Parse adapter content and return a validated mapping.

	This dispatcher currently supports YAML input via
	`load_adapter_from_yaml`. The loader returns an `AdapterModel`
	which we convert to a plain dict (`model_dump`) so downstream
	compiler code can continue to operate on mappings.
	"""
	try:
		model = load_adapter_from_yaml(content)
	except ValueError:
		# If the content is YAML mapping-shaped FLO, return it directly.
		# Otherwise preserve the previous permissive text fallback.
		parsed = yaml.safe_load(content)
		if isinstance(parsed, dict):
			return resolve_includes(parsed, source_path=source_path)
		return {"name": "parsed", "content": content}

	# `model` supports `model_dump()` for Pydantic compatibility
	try:
		return model.model_dump()
	except Exception:
		# Fallback: if the model does not implement `model_dump`, try
		# converting via `dict()` for compatibility with lightweight
		# fallback models.
		return dict(model)


__all__ = ["load_adapter_from_yaml", "parse_adapter"]
