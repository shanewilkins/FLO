from __future__ import annotations

from typing import Any

from .models import IR
from flo.services.errors import ValidationError


def validate_ir(obj: Any) -> None:
    """Validate that `obj` is a sensible `IR` instance.

    Raises `ValidationError` on failure so callers can map to CLI exit
    codes consistently.
    """
    if not isinstance(obj, IR):
        raise ValidationError("object is not an IR instance")

    if not obj.nodes:
        raise ValidationError("IR must contain at least one node")

    ids = [n.id for n in obj.nodes]
    if len(ids) != len(set(ids)):
        raise ValidationError("node ids must be unique")
