"""Adapter models for FLO inputs.

Prefer Pydantic v2 models for runtime validation and parsing. If
Pydantic isn't available the module will still import but some helper
callers may choose a dict-based fallback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic import BaseModel as _PydBaseModel  # type: ignore

try:
    from pydantic import BaseModel as _RuntimePydBaseModel
    PydanticAvailable = True
except Exception:  # pragma: no cover - optional dependency
    _RuntimePydBaseModel = object  # type: ignore
    PydanticAvailable = False


_PydBaseModel = _RuntimePydBaseModel if not TYPE_CHECKING else (_PydBaseModel)  # type: ignore

if PydanticAvailable:
    class _PydAdapterModel(_PydBaseModel):
        name: str
        content: str

    AdapterModel = _PydAdapterModel  # type: ignore
else:
    class AdapterModel:
        def __init__(self, name: str, content: str):
            self.name = name
            self.content = content

        @classmethod
        def model_validate(cls, data: Any) -> "AdapterModel":
            if isinstance(data, cls):
                return data
            # permissive fallback: coerce mapping to AdapterModel
            name = data.get("name") if isinstance(data, dict) else getattr(data, "name", "")
            content = data.get("content") if isinstance(data, dict) else getattr(data, "content", "")
            return cls(name=name or "", content=content or "")

        def model_dump(self) -> dict:
            return {"name": self.name, "content": self.content}
