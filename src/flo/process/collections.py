"""Traversal of canonical flat and recursively grouped entity collections."""

from collections.abc import Iterator
from typing import Any


def iter_collection_entries(collection: object) -> Iterator[dict[str, Any]]:
    """Yield authored entries in order without treating group names as IDs."""
    if isinstance(collection, list):
        yield from (entry for entry in collection if isinstance(entry, dict))
    elif isinstance(collection, dict):
        for key, value in collection.items():
            if key != "name":
                yield from iter_collection_entries(value)
