"""Shared text helpers for renderer modules."""

from __future__ import annotations


def normalize_space(value: str) -> str:
    """Collapse repeated whitespace into single spaces."""
    return " ".join(str(value or "").split())


__all__ = ["normalize_space"]
