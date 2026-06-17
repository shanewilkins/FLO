"""Runtime SPPM layout strategy toggles for matrix evaluation and tuning."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Literal

SppmPartitionMode = Literal["branch_aligned", "chain_progressive"]
SppmPortConstraintsMode = Literal["fixed_side", "fixed_order"]
SppmHelperAnchorMode = Literal["off", "conditional", "always"]
SppmSpacingProfile = Literal["compact", "balanced", "roomy"]

_ENV_PARTITION_MODE = "FLO_SPPM_PARTITION_MODE"
_ENV_PORT_CONSTRAINTS = "FLO_SPPM_PORT_CONSTRAINTS"
_ENV_HELPER_ANCHORS = "FLO_SPPM_HELPER_ANCHORS"
_ENV_SPACING_PROFILE = "FLO_SPPM_SPACING_PROFILE"


@dataclass(frozen=True)
class SppmLayoutStrategy:
    """Resolved strategy controls for SPPM ELK request shaping."""

    partition_mode: SppmPartitionMode = "branch_aligned"
    port_constraints: SppmPortConstraintsMode = "fixed_order"
    helper_anchors: SppmHelperAnchorMode = "always"
    spacing_profile: SppmSpacingProfile = "balanced"


def current_sppm_layout_strategy() -> SppmLayoutStrategy:
    """Read strategy controls from environment variables."""
    return SppmLayoutStrategy(
        partition_mode=_read_partition_mode(),
        port_constraints=_read_port_constraints_mode(),
        helper_anchors=_read_helper_anchor_mode(),
        spacing_profile=_read_spacing_profile(),
    )


def sppm_port_constraints_value() -> str:
    """Return ELK port constraint value for SPPM node serialization."""
    mode = _read_port_constraints_mode()
    if mode == "fixed_order":
        return "FIXED_ORDER"
    return "FIXED_SIDE"


def should_emit_sppm_branch_anchors(*, has_lanes: bool) -> bool:
    """Return whether synthetic helper anchors should be serialized."""
    mode = _read_helper_anchor_mode()
    if mode == "off":
        return False
    if mode == "conditional":
        return not has_lanes
    return True


def sppm_spacing_values() -> tuple[str, str]:
    """Return (node spacing, layer spacing) pair in pixels as strings."""
    profile = _read_spacing_profile()
    if profile == "compact":
        return "96", "104"
    if profile == "roomy":
        return "200", "80"
    return "160", "56"


def _read_partition_mode() -> SppmPartitionMode:
    value = os.getenv(_ENV_PARTITION_MODE, "branch_aligned").strip().lower()
    if value == "chain_progressive":
        return "chain_progressive"
    return "branch_aligned"


def _read_port_constraints_mode() -> SppmPortConstraintsMode:
    value = os.getenv(_ENV_PORT_CONSTRAINTS, "fixed_order").strip().lower()
    if value == "fixed_order":
        return "fixed_order"
    return "fixed_side"


def _read_helper_anchor_mode() -> SppmHelperAnchorMode:
    value = os.getenv(_ENV_HELPER_ANCHORS, "always").strip().lower()
    if value == "off":
        return "off"
    if value == "conditional":
        return "conditional"
    return "always"


def _read_spacing_profile() -> SppmSpacingProfile:
    value = os.getenv(_ENV_SPACING_PROFILE, "balanced").strip().lower()
    if value == "compact":
        return "compact"
    if value == "roomy":
        return "roomy"
    return "balanced"
