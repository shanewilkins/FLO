"""Compatibility shim for subprocess detail-map reference helpers.

The canonical helpers now live in flo.schema.subprocess_refs so both renderer
and compiler validation code can depend on a shared, renderer-safe seam.
"""

from flo.schema.subprocess_refs import (
    SUBPROCESS_DETAIL_MAP_REFERENCE_KEYS,
    iter_subprocess_detail_map_reference_values,
    resolve_subprocess_detail_map_reference,
)

__all__ = [
    "SUBPROCESS_DETAIL_MAP_REFERENCE_KEYS",
    "iter_subprocess_detail_map_reference_values",
    "resolve_subprocess_detail_map_reference",
]
