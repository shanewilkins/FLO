"""YAML adapter loader (stub).

This module will provide functions to parse `.flo` authoring files and
produce adapter model instances (pydantic/dataclass). For now this is a
lightweight stub to be implemented.
"""
from typing import Any, Dict


def load_adapter_from_yaml(content: str) -> Dict[str, Any]:
    """Parse YAML content and return an adapter-model-like dict.

    Replace this stub with a Pydantic-based adapter model in future.
    """
    # TODO: implement YAML parsing and adapter model coercion
    raise NotImplementedError("YAML adapter loader is not implemented yet")
