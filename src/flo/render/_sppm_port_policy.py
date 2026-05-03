"""SPPM port-policy resolution and edge-ID utilities.

Separates the port assignment logic from the route-building orchestration
in _sppm_routing.py so that neither file exceeds the 750-line limit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._autoformat_wrap import WrapPlan
from .options import RenderOptions


@dataclass(frozen=True)
class SppmPortPolicy:
    """Node-level ingress/egress policy for SPPM routing."""

    secondary_line_targets: frozenset[str]


def _sppm_rework_ports(
    *,
    wrap_ports: tuple[str, str],
    is_branch_out: bool,
    source: str,
    target: str,
    source_kind: str,
    target_kind: str,
    core_route: Any | None,
    port_policy: SppmPortPolicy,
) -> tuple[str, str]:
    """Return rework ports that reduce crossings around the mainline.

        For LR layouts:
                - decision branch-out edges leave the diamond south tip and enter
                    rework at the top edge (south -> north)
                - return edges leave rework from the west side and re-enter mainline
                    from the west side

    For TB layouts:
    - branch-out edges leave rightward and enter from left (e -> w)
    - return edges leave leftward and re-enter from right (w -> e)
    """
    source_port, target_port = wrap_ports
    if source_port == "tailport=e" and target_port == "headport=w":
        # LR layout visual contract:
        # - decision branch-to-rework exits south and enters rework north
        # - other branch-to-rework edges enter rework from west
        # - rework-return leaves rework west and re-enters mainline west
        if is_branch_out:
            if source_kind == "decision":
                return ("tailport=s", "headport=n")
            return ("tailport=e", "headport=w")

        return ("tailport=w", "headport=s")
    if source_port == "tailport=s" and target_port == "headport=n":
        if is_branch_out:
            return ("tailport=e", "headport=w")
        return ("tailport=w", "headport=e")
    return (source_port, target_port)


def _build_sppm_port_policy(*, edges: list[dict[str, Any]], node_kinds: dict[str, str]) -> SppmPortPolicy:
    secondary_line_targets: set[str] = set()
    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if not source or not target:
            continue
        if not _edge_is_explicit_branch_out(edge=edge, source_kind=node_kinds.get(source, "task")):
            continue
        secondary_line_targets.add(target)
    return SppmPortPolicy(secondary_line_targets=frozenset(secondary_line_targets))


def _edge_is_explicit_branch_out(*, edge: dict[str, Any], source_kind: str) -> bool:
    if str(edge.get("edge_type") or "").strip().lower() != "rework" and edge.get("rework") is not True:
        return False
    return source_kind == "decision" or edge.get("outcome") is not None or edge.get("label") is not None


def _preferred_tailport(
    *,
    node_id: str,
    kind: str,
    core_route: Any | None,
    slot_role: str,
    fallback_side: str,
    port_policy: SppmPortPolicy,
) -> str:
    _ = slot_role
    if node_id in port_policy.secondary_line_targets and core_route is not None:
        return _graphviz_tailport_for_side(
            slot_index=core_route.source_port.slot_index,
            side=fallback_side,
            kind=kind,
        )
    return f"tailport={fallback_side}"


def _preferred_headport(
    *,
    node_id: str,
    kind: str,
    core_route: Any | None,
    slot_role: str,
    fallback_side: str,
    port_policy: SppmPortPolicy,
) -> str:
    _ = slot_role
    if node_id in port_policy.secondary_line_targets and core_route is not None:
        return _graphviz_headport_for_side(
            slot_index=core_route.target_port.slot_index,
            side=fallback_side,
            kind=kind,
        )
    if core_route is not None and _supports_named_ports(kind) and fallback_side in {"w", "e"}:
        return _graphviz_headport_for_side(
            slot_index=core_route.target_port.slot_index,
            side=fallback_side,
            kind=kind,
        )
    return f"headport={fallback_side}"


def _preferred_return_headport(
    *,
    node_id: str,
    kind: str,
    core_route: Any | None,
    fallback_side: str,
) -> str:
    _ = node_id
    if core_route is not None and _supports_named_ports(kind):
        return f'headport="rin_{core_route.target_port.slot_index}:e"'
    return f"headport={fallback_side}"


def _graphviz_tailport_for_side(*, slot_index: int, side: str, kind: str) -> str:
    if _supports_named_ports(kind):
        if side == "w":
            return f'tailport="in_{slot_index}:w"'
        return f'tailport="out_{slot_index}:{side}"'
    return f"tailport={side}"


def _graphviz_headport_for_side(*, slot_index: int, side: str, kind: str) -> str:
    if _supports_named_ports(kind):
        return f'headport="in_{slot_index}:{side}"'
    return f"headport={side}"


def _build_boundary_lane_map(*, wrap_plan: WrapPlan) -> dict[tuple[str, str], str]:
    if not wrap_plan.active:
        return {}
    lane_map: dict[tuple[str, str], str] = {}
    for idx in range(max(0, len(wrap_plan.chunks) - 1)):
        source = wrap_plan.chunks[idx][-1]
        target = wrap_plan.chunks[idx + 1][0]
        lane_map[(source, target)] = f"wrap_lane_{idx}"
    return lane_map


def _resolved_ports(
    *,
    core_route: Any | None,
    options: RenderOptions,
    wrap_ports: tuple[str, str] | None,
    source_kind: str,
    target_kind: str,
) -> tuple[str, str]:
    if core_route is not None:
        return (
            f"tailport={core_route.source_port.side}",
            f"headport={core_route.target_port.side}",
        )
    if wrap_ports is not None:
        return wrap_ports
    return _sppm_wrap_ports(options=options)


def _graphviz_tailport_for_spec(port_spec: Any, *, kind: str) -> str:
    if _supports_named_ports(kind):
        return f'tailport="out_{port_spec.slot_index}:{port_spec.side}"'
    return f"tailport={port_spec.side}"


def _graphviz_headport_for_spec(port_spec: Any, *, kind: str) -> str:
    if _supports_named_ports(kind):
        return f'headport="in_{port_spec.slot_index}:{port_spec.side}"'
    return f"headport={port_spec.side}"


def _supports_named_ports(kind: str) -> bool:
    return kind not in {"start", "end", "decision"}


def _resolved_boundary_ports(
    *,
    core_route: Any | None,
    options: RenderOptions,
    source_kind: str,
    target_kind: str,
) -> tuple[str, str]:
    if options.orientation == "lr":
        source_port = (
            _graphviz_tailport_for_spec(core_route.source_port, kind=source_kind)
            if core_route is not None
            else "tailport=e"
        )
        if _supports_named_ports(target_kind):
            return (source_port, 'headport="boundary_in:s"')
        return (source_port, "headport=n")

    if core_route is not None:
        return (
            f"tailport={core_route.source_port.side}",
            f"headport={core_route.target_port.side}",
        )
    return _sppm_wrap_ports(options=options)


def _sppm_wrap_ports(*, options: RenderOptions) -> tuple[str, str]:
    if options.orientation == "tb":
        return ("tailport=s", "headport=n")
    return ("tailport=e", "headport=w")


def sppm_rework_anchor_id(*, source: str, target: str) -> str:
    """Return a stable anchor id for a rework edge between two nodes."""
    source_part = _safe_sppm_edge_id_part(source)
    target_part = _safe_sppm_edge_id_part(target)
    return f"__sppm_rework_corridor_{source_part}_{target_part}"


def sppm_boundary_anchor_id(*, source: str, target: str) -> str:
    """Return a stable anchor id for a wrapped boundary edge bend point."""
    source_part = _safe_sppm_edge_id_part(source)
    target_part = _safe_sppm_edge_id_part(target)
    return f"__sppm_boundary_corridor_{source_part}_{target_part}"


def _safe_sppm_edge_id_part(value: str) -> str:
    cleaned = []
    for ch in value:
        if ch.isalnum() or ch == "_":
            cleaned.append(ch)
        else:
            cleaned.append("_")
    return "".join(cleaned) or "edge"


def is_sppm_rework_edge(
    *,
    edge: dict[str, Any],
    step_numbering: dict[str, int],
    source: str,
    target: str,
) -> bool:
    """Return whether an SPPM edge should be rendered as rework."""
    explicit = edge.get("rework")
    if explicit is not None:
        return bool(explicit)
    if str(edge.get("edge_type") or "").strip().lower() == "rework":
        return True

    src_num = step_numbering.get(source)
    dst_num = step_numbering.get(target)
    if src_num is None or dst_num is None:
        return False
    return src_num > dst_num