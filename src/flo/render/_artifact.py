"""Backend-neutral render artifact contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RenderArtifact:
    """Rendered artifact produced by a backend-neutral render entrypoint."""

    kind: str
    content: str
    backend: str
    metadata: dict[str, Any] = field(default_factory=dict)
