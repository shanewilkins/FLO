"""Backend-neutral render artifact contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RenderArtifact:
    """Rendered artifact produced by a backend-neutral render entrypoint."""

    kind: str
    content: str
    backend: str
