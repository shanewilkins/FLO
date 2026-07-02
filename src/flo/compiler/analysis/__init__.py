"""Analysis package nested under the compiler layer."""

from .scc import scc_condense
from .movement import (
    infer_material_movements,
    aggregate_material_movements,
    infer_people_movements,
    aggregate_people_movements,
    aggregate_people_movements_by_worker,
    extract_location_spatial_index,
)
from .process_metadata import extract_process_metadata

__all__ = [
    "scc_condense",
    "infer_material_movements",
    "aggregate_material_movements",
    "infer_people_movements",
    "aggregate_people_movements",
    "aggregate_people_movements_by_worker",
    "extract_location_spatial_index",
    "extract_process_metadata",
]
