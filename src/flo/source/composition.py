"""Composition helpers for include-based FLO source documents."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .models import SourceShapeError, validate_source_fragment
from .provenance import SourceOrigin, composed_origins, record_origins

_RESOURCE_KEYS = (
    "items",
    "resources",
    "materials",
    "equipment",
    "locations",
    "workers",
)
_LIST_KEYS = ("steps", "transitions", "edges", "lanes")
MAX_SOURCE_BYTES = 1_000_000
MAX_INCLUDE_FILES = 256
MAX_INCLUDE_DEPTH = 32
MAX_EXPANDED_SOURCE_BYTES = 8_000_000


@dataclass
class _IncludeContext:
    root_dir: Path
    include_count: int = 0
    expanded_bytes: int = 0
    included_paths: list[Path] | None = None
    origins: dict[int, SourceOrigin] = field(default_factory=dict)
    documents: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class SourceComposition:
    """Portable source-composition context for inspection reports."""

    entry_source: str
    included_sources: tuple[str, ...] = ()
    origins: dict[tuple[str | int, ...], SourceOrigin] = field(
        default_factory=dict, repr=False, compare=False
    )


_COMPOSITION_CONTEXT_KEY = "__flo_composition_context__"


class IncludeError(ValueError):
    """Include-resolution failure with the attempted source chain."""

    def __init__(self, message: str, *, include_chain: tuple[str, ...]) -> None:
        """Create an include error with the source chain that was attempted."""
        super().__init__(f"E0002: {message}")
        self.include_chain = include_chain


class FragmentError(SourceShapeError):
    """A malformed fragment retains its originating file and include chain."""

    def __init__(
        self,
        error: SourceShapeError,
        *,
        source_path: str,
        content: str,
        include_chain: tuple[str, ...],
    ) -> None:
        """Preserve structural diagnostic evidence before composition."""
        super().__init__(str(error), error.location)
        self.source_path = source_path
        self.source_content = content
        self.include_chain = include_chain


def resolve_includes(
    document: dict[str, Any],
    source_path: str | None = None,
    *,
    root_source_bytes: int = 0,
    capture_composition: bool = False,
    root_content: str = "",
) -> dict[str, Any]:
    """Resolve include directives and return a composed mapping.

    Include syntax:

    includes:
      - relative/or/absolute/path.yaml
    """
    root_path = Path(source_path).resolve() if source_path else None
    root_dir = root_path.parent if root_path is not None else Path.cwd().resolve()
    context = _IncludeContext(
        root_dir=root_dir,
        expanded_bytes=root_source_bytes,
        included_paths=[],
        origins=record_origins(document, source=source_path, content=root_content),
        documents=[document],
    )
    _enforce_expanded_byte_limit(context)
    composed = _compose_document(
        document=document,
        current_path=root_path,
        include_stack=[root_path] if root_path is not None else [],
        context=context,
        depth=0,
    )
    if capture_composition and context.included_paths:
        composed[_COMPOSITION_CONTEXT_KEY] = {
            "included_sources": _portable_include_paths(context),
            "origins": composed_origins(composed, context.origins),
        }
    return composed


def pop_source_composition(
    document: dict[str, Any], *, source_path: str | None
) -> SourceComposition:
    """Remove and return parser-owned source composition context."""
    raw_context = document.pop(_COMPOSITION_CONTEXT_KEY, None)
    included_sources: tuple[str, ...] = ()
    if isinstance(raw_context, dict):
        raw_includes = raw_context.get("included_sources")
        if isinstance(raw_includes, list):
            included_sources = tuple(
                sorted(
                    {
                        entry.strip()
                        for entry in raw_includes
                        if isinstance(entry, str) and entry.strip()
                    }
                )
            )
    return SourceComposition(
        entry_source=_portable_entry_source(source_path),
        included_sources=included_sources,
        origins=raw_context.get("origins", {}) if isinstance(raw_context, dict) else {},
    )


def _compose_document(
    document: dict[str, Any],
    current_path: Path | None,
    include_stack: list[Path],
    context: _IncludeContext,
    depth: int,
) -> dict[str, Any]:
    include_paths = _normalize_include_entries(document)
    if include_paths or depth:
        try:
            validate_source_fragment(_fragment_payload(document))
        except SourceShapeError as exc:
            if (
                exc.location[:1] == ("transitions",)
                and "edges" in document
                and "transitions" not in document
            ):
                exc.location = ("edges", *exc.location[1:])
            origin = context.origins.get(id(document))
            if origin is None:
                raise
            raise FragmentError(
                exc,
                source_path=origin.source or "<memory>",
                content=origin.content,
                include_chain=tuple(str(path) for path in include_stack),
            ) from exc
    composed: dict[str, Any] = {}

    for include_ref in include_paths:
        include_chain = tuple(str(path) for path in include_stack)
        try:
            include_path = _resolve_include_path(
                include_ref=include_ref,
                current_path=current_path,
                root_dir=context.root_dir,
            )
        except ValueError as exc:
            raise IncludeError(
                str(exc), include_chain=(*include_chain, include_ref)
            ) from exc
        try:
            include_doc = _load_include_mapping(
                include_path=include_path,
                include_stack=include_stack,
                context=context,
                depth=depth + 1,
            )
        except ValueError as exc:
            raise IncludeError(
                str(exc), include_chain=(*include_chain, str(include_path))
            ) from exc
        nested = _compose_document(
            document=include_doc,
            current_path=include_path,
            include_stack=[*include_stack, include_path],
            context=context,
            depth=depth + 1,
        )
        composed = _merge_documents(base=composed, incoming=nested)

    local = dict(document)
    local.pop("include", None)
    local.pop("includes", None)
    composed = _merge_documents(base=composed, incoming=_fragment_payload(local))

    _validate_unique_ids(composed)
    return composed


def _normalize_include_entries(document: dict[str, Any]) -> list[str]:
    include_value = document.get("includes")
    if include_value is None:
        include_value = document.get("include")

    if include_value is None:
        return []

    if isinstance(include_value, str):
        text = include_value.strip()
        return [text] if text else []

    if not isinstance(include_value, list):
        raise ValueError("include/includes must be a string or list of strings")

    out: list[str] = []
    for idx, entry in enumerate(include_value):
        if not isinstance(entry, str) or not entry.strip():
            raise ValueError(f"includes[{idx}] must be a non-empty string path")
        out.append(entry.strip())
    return out


def _resolve_include_path(
    include_ref: str,
    current_path: Path | None,
    root_dir: Path | None = None,
) -> Path:
    raw = Path(include_ref)
    base_dir = current_path.parent if current_path is not None else Path.cwd()
    resolved = raw.resolve() if raw.is_absolute() else (base_dir / raw).resolve()
    trust_root = root_dir.resolve() if root_dir is not None else base_dir.resolve()
    try:
        resolved.relative_to(trust_root)
    except ValueError as exc:
        raise ValueError(
            f"include path escapes source root '{trust_root}': {include_ref}"
        ) from exc
    return resolved


def _load_include_mapping(
    include_path: Path,
    include_stack: list[Path],
    context: _IncludeContext | None = None,
    depth: int = 1,
) -> dict[str, Any]:
    if depth > MAX_INCLUDE_DEPTH:
        raise ValueError(f"include depth exceeds limit of {MAX_INCLUDE_DEPTH}")
    if include_path in include_stack:
        chain = " -> ".join(str(path) for path in [*include_stack, include_path])
        raise ValueError(f"include cycle detected: {chain}")

    if not include_path.exists():
        raise ValueError(f"include file not found: {include_path}")

    active_context = context or _IncludeContext(root_dir=include_path.parent)
    active_context.include_count += 1
    if active_context.included_paths is not None:
        active_context.included_paths.append(include_path)
    if active_context.include_count > MAX_INCLUDE_FILES:
        raise ValueError(f"include count exceeds limit of {MAX_INCLUDE_FILES}")

    try:
        source_bytes = include_path.stat().st_size
    except OSError as exc:
        raise ValueError(
            f"unable to inspect include file '{include_path}': {exc}"
        ) from exc
    if source_bytes > MAX_SOURCE_BYTES:
        raise ValueError(
            f"include file '{include_path}' exceeds {MAX_SOURCE_BYTES} byte limit"
        )
    active_context.expanded_bytes += source_bytes
    _enforce_expanded_byte_limit(active_context)

    try:
        content = include_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(
            f"unable to read include file '{include_path}': {exc}"
        ) from exc

    parsed = yaml.safe_load(content)
    if not isinstance(parsed, dict):
        raise ValueError(f"include file '{include_path}' must contain a YAML mapping")

    active_context.origins.update(
        record_origins(
            parsed,
            source=str(include_path),
            content=content,
            include_chain=tuple(str(path) for path in [*include_stack, include_path]),
        )
    )
    active_context.documents.append(parsed)
    return parsed


def _portable_include_paths(context: _IncludeContext) -> list[str]:
    paths = context.included_paths or []
    return sorted({path.relative_to(context.root_dir).as_posix() for path in paths})


def _portable_entry_source(source_path: str | None) -> str:
    if source_path == "-":
        return "<stdin>"
    if isinstance(source_path, str) and source_path.strip():
        return Path(source_path).name
    return "<memory>"


def _enforce_expanded_byte_limit(context: _IncludeContext) -> None:
    if context.expanded_bytes > MAX_EXPANDED_SOURCE_BYTES:
        raise ValueError(
            f"expanded FLO source exceeds {MAX_EXPANDED_SOURCE_BYTES} byte limit"
        )


def _merge_documents(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    base, incoming = _align_collection_slots(base, incoming)
    merged = dict(base)

    for key, value in incoming.items():
        if key not in merged:
            merged[key] = value
            continue

        if key in _LIST_KEYS:
            merged[key] = _merge_list_values(
                key=key, base_value=merged.get(key), incoming_value=value
            )
            continue

        if key in _RESOURCE_KEYS:
            merged[key] = _merge_resource_values(
                key=key, base_value=merged.get(key), incoming_value=value
            )
            continue

        if key == "process":
            merged[key] = _merge_process(
                base_value=merged.get(key), incoming_value=value
            )
            continue

        if key == "spec_version":
            if merged[key] != value:
                raise SourceShapeError(
                    "spec_version must agree across included documents",
                    ("spec_version",),
                )
            continue

        merged[key] = value

    return merged


def _merge_list_values(key: str, base_value: Any, incoming_value: Any) -> list[Any]:
    if not isinstance(incoming_value, list):
        raise ValueError(f"{key} must be a list")

    out: list[Any] = []
    if isinstance(base_value, list):
        out.extend(base_value)
    elif base_value is not None:
        raise ValueError(f"{key} must be a list")

    out.extend(incoming_value)
    return out


def _merge_resource_values(key: str, base_value: Any, incoming_value: Any) -> Any:
    if base_value is None:
        return incoming_value
    if incoming_value is None:
        return base_value

    if isinstance(base_value, list) and isinstance(incoming_value, list):
        return [*base_value, *incoming_value]

    if isinstance(base_value, dict) and isinstance(incoming_value, dict):
        merged = dict(base_value)
        for child_key, child_value in incoming_value.items():
            if child_key == "name":
                merged.setdefault("name", child_value)
                continue
            if child_key in merged:
                merged[child_key] = _merge_resource_values(
                    key=f"{key}.{child_key}",
                    base_value=merged[child_key],
                    incoming_value=child_value,
                )
            else:
                merged[child_key] = child_value
        return merged

    raise ValueError(
        f"{key} include merge type mismatch: expected list/list or dict/dict"
    )


def _merge_process(base_value: Any, incoming_value: Any) -> Any:
    if base_value is None:
        return incoming_value
    if incoming_value is None:
        return base_value
    if not isinstance(base_value, dict) or not isinstance(incoming_value, dict):
        raise ValueError("process must be an object when present")

    merged = dict(base_value)
    for key, value in incoming_value.items():
        if (
            key == "metadata"
            and isinstance(merged.get("metadata"), dict)
            and isinstance(value, dict)
        ):
            merged["metadata"] = _merge_metadata(merged["metadata"], value)
            continue
        if key in _RESOURCE_KEYS:
            merged[key] = _merge_resource_values(key, merged.get(key), value)
            continue
        merged[key] = value
    return merged


def _merge_metadata(base: dict, incoming: dict) -> dict:
    merged = {**base, **incoming}
    for key in _RESOURCE_KEYS:
        if key in base and key in incoming:
            merged[key] = _merge_resource_values(key, base[key], incoming[key])
    return merged


def _fragment_payload(document: dict[str, Any]) -> dict[str, Any]:
    payload = dict(document)
    if "edges" in payload and "transitions" not in payload:
        payload["transitions"] = payload.pop("edges")
    return payload


def _collection_slot(document: dict, key: str) -> tuple[str, ...] | None:
    for prefix in ((), ("process",), ("process", "metadata")):
        container = document
        for part in prefix:
            container = container.get(part, {})
            if not isinstance(container, dict):
                break
        if isinstance(container, dict) and key in container:
            return (*prefix, key)
    return None


def _replace_collection(document: dict, path: tuple[str, ...], value: Any) -> dict:
    result = dict(document)
    container = result
    for part in path[:-1]:
        container[part] = dict(container[part])
        container = container[part]
    if value is _ABSENT:
        container.pop(path[-1])
    else:
        container[path[-1]] = value
    return result


_ABSENT = object()


def _align_collection_slots(base: dict, incoming: dict) -> tuple[dict, dict]:
    for key in _RESOURCE_KEYS:
        base_path = _collection_slot(base, key)
        incoming_path = _collection_slot(incoming, key)
        if base_path is None or incoming_path is None or base_path == incoming_path:
            continue
        previous = base
        for part in base_path:
            previous = previous[part]
        current = incoming
        for part in incoming_path:
            current = current[part]
        incoming = _replace_collection(
            incoming, incoming_path, _merge_resource_values(key, previous, current)
        )
        base = _replace_collection(base, base_path, _ABSENT)
    return base, incoming


def _validate_unique_ids(document: dict[str, Any]) -> None:
    _ensure_unique_id_list(document=document, key="steps")
    _ensure_unique_id_list(document=document, key="lanes")


def _ensure_unique_id_list(document: dict[str, Any], key: str) -> None:
    value = document.get(key)
    if not isinstance(value, list):
        return

    seen: set[str] = set()
    for idx, item in enumerate(value):
        if not isinstance(item, dict):
            continue
        item_id = item.get("id")
        if item_id is None:
            continue
        item_id_text = str(item_id)
        if item_id_text in seen:
            raise ValueError(
                f"duplicate {key[:-1]} id '{item_id_text}' detected at {key}[{idx}]"
            )
        seen.add(item_id_text)
