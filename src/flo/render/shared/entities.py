"""Resolve canonical entity identities for presentation without rewriting references."""

from typing import Any


def entity_names(process: Any, collection: str) -> dict[str, str]:
    """Index names in a canonical process collection, including nested groups."""
    if isinstance(process, dict):
        value = process.get("process", {}).get(collection)
    else:
        value = getattr(process, collection, None)

    def entries(value):
        if isinstance(value, list):
            yield from (entry for entry in value if isinstance(entry, dict))
        elif isinstance(value, dict):
            for key, nested in value.items():
                if key != "name":
                    yield from entries(nested)

    return {
        entry["id"]: entry["name"]
        for entry in entries(value)
        if isinstance(entry.get("id"), str) and isinstance(entry.get("name"), str)
    }


def project_entity_names(
    nodes: list[dict[str, Any]], process: Any
) -> list[dict[str, Any]]:
    """Give task content resolved performer names on detached presentation nodes."""
    names = entity_names(process, "resources")
    return [
        {
            **node,
            "performed_by": [
                names.get(value, value) for value in node.get("performed_by", [])
            ],
        }
        for node in nodes
    ]
