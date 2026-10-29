"""Shared source/exchange collection boundary checks and FLO diagnostics."""

from typing import Any

from pydantic import TypeAdapter
from pydantic import ValidationError as ContractError

from .contracts import (
    EntityCollection,
    ItemContract,
    LocationContract,
    ResourceContract,
)
from .validation_errors import LocatedValidationError

_COLLECTIONS = {
    key: TypeAdapter(EntityCollection[contract])
    for key, contract in (
        ("items", ItemContract),
        ("resources", ResourceContract),
        ("locations", LocationContract),
    )
}


def validate_collection_shape(key: str, value: Any) -> None:
    """Use canonical entity contracts, retaining stable codes and authored paths."""
    try:
        _COLLECTIONS[key].validate_python(value)
    except ContractError as exc:
        # Select the branch matching the actual collection container. Pydantic's
        # union labels describe implementation paths, never authored field names.
        issues = exc.errors(include_url=False, include_input=False)
        branch = "list[" if isinstance(value, list) else "function-after["
        issue = next(
            (entry for entry in issues if str(entry["loc"][0]).startswith(branch)),
            issues[0],
        )
        path = []
        cursor = value
        for part in issue["loc"]:
            if (isinstance(cursor, dict) and part in cursor) or (
                isinstance(cursor, list) and isinstance(part, int)
            ):
                path.append(part)
                cursor = cursor[part]
            elif isinstance(part, str) and (
                part.startswith(("list[", "function-after[", "EntityGroup["))
                or part
                in {"count", "measure", "int", "float", "str", "constrained-str"}
            ):
                continue
            else:
                path.append(part)
        code = _collection_error_code(key, value, path, issue["type"])
        location = (key, *path)
        description = _collection_error_description(code, path, issue["type"])
        raise LocatedValidationError(
            f"{code}: process {key} {'/'.join(map(str, path)) or 'collection'} {description}",
            location,
        ) from exc


def _collection_error_code(key: str, value: Any, path: list, error_type: str) -> str:
    if not isinstance(value, (list, dict)):
        return "E1201"
    if error_type == "list_type" and "quantity" not in path:
        return "E1201"
    if "quantity" in path:
        offset = path.index("quantity")
        cursor = value
        for part in path[:offset]:
            cursor = cursor[part]
        quantity = cursor.get("quantity")
        field = path[-1]
        if field == "quantity":
            return (
                "E1205"
                if error_type.startswith("union_tag")
                else "E1211"
                if error_type == "value_error"
                else "E1204"
            )
        if isinstance(quantity, dict) and quantity.get("kind") == "count":
            return {"value": "E1206", "unit": "E1207", "qualifier": "E1208"}.get(
                field, "E1204"
            )
        return {
            "value": "E1209",
            "unit": "E1210",
            "canonical_value": "E1212",
            "canonical_unit": "E1213",
        }.get(field, "E1204")
    if "spatial" in path:
        return "E1216" if path[-1] == "unit" else "E1215"
    return {
        "id": "E1219",
        "name": "E1220",
        "kind": "E1217" if key == "items" else "E1218",
    }.get(path[-1] if path else None, "E1202" if isinstance(value, list) else "E1201")


def _collection_error_description(code: str, path: list, error_type: str) -> str:
    if error_type == "extra_forbidden":
        return "is not a supported field"
    if "extensions" in path:
        return "must contain finite JSON data"
    return {
        "E1201": "must be a list or non-empty grouped object",
        "E1202": "must be an entity object",
        "E1204": "must be a quantity object",
        "E1205": "must declare quantity kind count or measure",
        "E1206": "must be an integer greater than or equal to 1",
        "E1207": "must use count unit each",
        "E1208": "must be a string qualifier",
        "E1209": "must be a finite positive measured amount",
        "E1210": "must be a supported measure unit",
        "E1211": "must supply canonical_value and canonical_unit together",
        "E1212": "must be a finite positive canonical amount",
        "E1213": "must be a supported canonical measure unit",
        "E1215": "must provide finite numeric spatial x and y",
        "E1216": "must be a supported spatial unit",
        "E1217": "must declare item kind material or information",
        "E1218": "must declare resource kind person or equipment",
        "E1219": "must supply a nonblank entity id",
        "E1220": "must supply a nonblank entity name",
    }.get(code, "has an invalid value")
