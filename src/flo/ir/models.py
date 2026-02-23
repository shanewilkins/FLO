from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class Node:
    id: str
    type: str
    attrs: Dict[str, Any] | None = None


@dataclass
class IR:
    """A minimal canonical IR data structure used by render/analysis.

    This is intentionally tiny and will be expanded as the project
    progresses. Kept as dataclasses to avoid extra runtime deps.
    """
    name: str
    nodes: List[Node]
