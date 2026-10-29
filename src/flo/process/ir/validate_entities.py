"""Entity identity, spatial units and dimensional quantity equivalence."""

from typing import Any

from flo.process.contract_validation import validate_collection_shape
from flo.process.units import SPATIAL_UNITS

from ._boundary_validation import validate_process_identity
from .models import IR
from .validate_quantities import _validate_measure_quantity
from .validation_errors import _LocatedValidationError, _QuantityValidationError


def _validate_process_resources(obj: IR) -> None:
    validate_process_identity(obj.process_metadata)
    collections = {
        key: getattr(obj, key, None) for key in ("items", "resources", "locations")
    }
    for resource_key, resources in collections.items():
        if resources is None:
            continue
        _validate_resource_collection(
            resource_key=resource_key,
            collection=resources,
            path=resource_key,
            seen_ids=set(),
            location=(resource_key,),
        )


def _validate_resource_collection(
    resource_key: str,
    collection: Any,
    path: str,
    seen_ids: set[str],
    location: tuple[str | int, ...],
) -> None:
    validate_collection_shape(resource_key, collection)
    for entry_location, resource in _entity_entries(collection, location):
        resource_id = resource["id"]
        if resource_id in seen_ids:
            raise _LocatedValidationError(
                f"E1221: {path}.id duplicates declared {resource_key} id '{resource_id}'",
                entry_location,
            )
        seen_ids.add(resource_id)
        spatial = resource.get("spatial")
        if spatial is not None:
            unit = spatial.get("unit")
            if unit is not None and unit.strip().lower() not in SPATIAL_UNITS:
                raise _LocatedValidationError(
                    f"E1216: {path}.spatial.unit must be one of {sorted(SPATIAL_UNITS)}",
                    (*entry_location, "spatial", "unit"),
                )
        quantity = resource.get("quantity")
        if quantity is not None and quantity["kind"] == "measure":
            try:
                _validate_measure_quantity(path=path, quantity=quantity)
            except _QuantityValidationError as exc:
                exc.location = (*entry_location, "quantity", *exc.location)
                raise


def _entity_entries(collection: Any, location: tuple):
    if isinstance(collection, list):
        for index, entry in enumerate(collection):
            yield (*location, index), entry
    else:
        for key, child in collection.items():
            if key != "name":
                yield from _entity_entries(child, (*location, key))
