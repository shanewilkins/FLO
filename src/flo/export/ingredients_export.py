"""Compatibility shim for historical ingredients export imports."""

from __future__ import annotations

from .materials_export import ir_to_ingredients_text, ir_to_materials_text

__all__ = ["ir_to_ingredients_text", "ir_to_materials_text"]
