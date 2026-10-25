"""Private authored locations retained across include composition."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SourceOrigin:
    """Original source and path of an authored mapping or sequence."""

    source: str | None
    content: str
    location: tuple[str | int, ...]
    include_chain: tuple[str, ...] = ()


def record_origins(
    value: Any,
    *,
    source: str | None,
    content: str,
    include_chain: tuple[str, ...] = (),
) -> dict[int, SourceOrigin]:
    """Index authored containers by identity without copying their contents."""
    return {
        id(container): SourceOrigin(source, content, path, include_chain)
        for path, container in _containers(value)
    }


def composed_origins(
    value: Any, origins: dict[int, SourceOrigin]
) -> dict[tuple[str | int, ...], SourceOrigin]:
    """Resolve composed container paths back to their authored containers."""
    return {
        path: origins[id(container)]
        for path, container in _containers(value)
        if id(container) in origins
    }


def _containers(value: Any, path: tuple = (), ancestors: frozenset[int] = frozenset()):
    if not isinstance(value, (dict, list)) or id(value) in ancestors:
        return
    yield path, value
    children = value.items() if isinstance(value, dict) else enumerate(value)
    for key, child in children:
        yield from _containers(child, (*path, key), ancestors | {id(value)})
