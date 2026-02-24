"""Layer mapping and allowed-imports used by policy tests.

This file defines which paths belong to which logical layer and the
allowed import directions between layers. It is intentionally small
so the mappings are easy to update as the architecture evolves.
"""
from __future__ import annotations

from typing import Dict, List, Set

# Map logical layer name -> list of path prefixes (workspace-relative)
LAYER_PATHS: Dict[str, List[str]] = {
    "services": ["src/flo/services/", "src/flo/io/"],
    "adapters": ["src/flo/adapters/"],
    "compiler": ["src/flo/compiler/", "src/flo/ir/", "src/flo/analysis/"],
    "render": ["src/flo/render/"],
    "core": ["src/flo/core.py", "src/flo/main.py", "src/flo/cli.py"],
}

# Allowed import graph: layer -> set(of layers it may import from)
ALLOWED_IMPORTS: Dict[str, Set[str]] = {
    "services": set(),
    "adapters": {"services"},
    "compiler": {"adapters", "services"},
    "render": {"compiler", "services"},
    "core": {"services", "adapters", "compiler", "render"},
}

__all__ = ["LAYER_PATHS", "ALLOWED_IMPORTS"]
