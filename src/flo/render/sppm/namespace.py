"""SPPM reserved namespaces and generated row identification."""

from ..layout_core.elk_contracts import ElkLayoutRequest
from ..layout_core.elk_validation import validate_elk_request_namespaces
from ..layout_core.lane_support import GENERATED_LANE_IDS, generated_lane_ids


def validate_sppm_namespaces(request: ElkLayoutRequest) -> None:
    """Validate generic namespaces with SPPM-owned reserved IDs and prefixes."""
    synthetic = generated_lane_ids(request) | {
        lane.id for lane in request.lanes if lane.id.startswith("__sppm_row_wrap_")
    }
    validate_elk_request_namespaces(
        request,
        reserved_ids=GENERATED_LANE_IDS | {"__sppm_row_mainline", "__sppm_row_rework"},
        reserved_prefixes=("__sppm_",),
        synthetic_lane_ids=synthetic,
    )


def is_synthetic_sppm_lane(lane_id: str) -> bool:
    """Identify layout-only row containers that are not visible responsibility lanes."""
    return str(lane_id).startswith("__sppm_row_")
