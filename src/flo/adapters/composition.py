"""Composition helpers for include-based FLO source documents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_RESOURCE_KEYS = ("materials", "equipment", "locations", "workers")
_LIST_KEYS = ("steps", "transitions", "edges", "lanes")


def resolve_includes(document: dict[str, Any], source_path: str | None = None) -> dict[str, Any]:
    """Resolve include directives and return a composed mapping.

    Include syntax:

    includes:
      - relative/or/absolute/path.yaml
    """
    root_path = Path(source_path).resolve() if source_path else None
    return _compose_document(document=document, current_path=root_path, include_stack=[])


def _compose_document(
    document: dict[str, Any],
    current_path: Path | None,
    include_stack: list[Path],
) -> dict[str, Any]:
    include_paths = _normalize_include_entries(document)
    composed: dict[str, Any] = {}

    for include_ref in include_paths:
        include_path = _resolve_include_path(include_ref=include_ref, current_path=current_path)
        include_doc = _load_include_mapping(include_path=include_path, include_stack=include_stack)
        nested = _compose_document(
            document=include_doc,
            current_path=include_path,
            include_stack=[*include_stack, include_path],
        )
        composed = _merge_documents(base=composed, incoming=nested)

    local = dict(document)
    local.pop("include", None)
    local.pop("includes", None)
    composed = _merge_documents(base=composed, incoming=local)

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


def _resolve_include_path(include_ref: str, current_path: Path | None) -> Path:
    raw = Path(include_ref)
    if raw.is_absolute():
        return raw.resolve()

    base_dir = current_path.parent if current_path is not None else Path.cwd()
    return (base_dir / raw).resolve()


def _load_include_mapping(include_path: Path, include_stack: list[Path]) -> dict[str, Any]:
    if include_path in include_stack:
        chain = " -> ".join(str(path) for path in [*include_stack, include_path])
        raise ValueError(f"include cycle detected: {chain}")

    if not include_path.exists():
        raise ValueError(f"include file not found: {include_path}")

    try:
        content = include_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"unable to read include file '{include_path}': {exc}") from exc

    parsed = yaml.safe_load(content)
    if not isinstance(parsed, dict):
        raise ValueError(f"include file '{include_path}' must contain a YAML mapping")

    return parsed


def _merge_documents(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)

    for key, value in incoming.items():
        if key in _LIST_KEYS:
            merged[key] = _merge_list_values(key=key, base_value=merged.get(key), incoming_value=value)
            continue

        if key in _RESOURCE_KEYS:
            merged[key] = _merge_resource_values(key=key, base_value=merged.get(key), incoming_value=value)
            continue

        if key == "process":
            merged[key] = _merge_process(base_value=merged.get(key), incoming_value=value)
            continue

        if key == "spec_version":
            merged.setdefault(key, value)
            continue

        merged[key] = value

    return merged


def _merge_list_values(key: str, base_value: Any, incoming_value: Any) -> list[Any]:
    if incoming_value is None:
        return list(base_value) if isinstance(base_value, list) else []
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

    raise ValueError(f"{key} include merge type mismatch: expected list/list or dict/dict")


def _merge_process(base_value: Any, incoming_value: Any) -> Any:
    if base_value is None:
        return incoming_value
    if incoming_value is None:
        return base_value
    if not isinstance(base_value, dict) or not isinstance(incoming_value, dict):
        raise ValueError("process must be an object when present")

    merged = dict(base_value)
    for key, value in incoming_value.items():
        if key == "metadata" and isinstance(merged.get("metadata"), dict) and isinstance(value, dict):
            merged["metadata"] = {**merged["metadata"], **value}
            continue
        merged[key] = value
    return merged


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
            raise ValueError(f"duplicate {key[:-1]} id '{item_id_text}' detected at {key}[{idx}]")
        seen.add(item_id_text)
