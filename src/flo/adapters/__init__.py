"""Adapters package: YAML/other input adapters for FLO."""

from __future__ import annotations

from typing import Any, Dict


from .yaml_loader import load_adapter_from_yaml


def parse_adapter(content: str) -> Dict[str, Any]:
	"""Parse adapter content and return a validated mapping.

	This dispatcher currently supports YAML input via
	`load_adapter_from_yaml`. The loader returns an `AdapterModel`
	which we convert to a plain dict (`model_dump`) so downstream
	compiler code can continue to operate on mappings.
	"""
	try:
		model = load_adapter_from_yaml(content)
	except ValueError:
		# Fall back to the previous permissive behaviour for plain strings
		# while YAML-based adapters are the preferred path.
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
