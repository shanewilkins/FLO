"""Responsibility-lane contracts shared by ELK-backed renderers."""

from __future__ import annotations

from typing import Any

from .elk_contracts import ElkLayoutLane


def lane_specs(
    *,
    process: dict[str, Any] | Any,
    nodes: list[dict[str, Any]],
    separate_process_boundaries: bool = True,
) -> tuple[ElkLayoutLane, ...]:
    """Build ordered ELK lane specs from declarations and node membership."""
    lane_labels = _declared_lane_labels(process)
    ordered_lane_ids = _ordered_lane_ids(nodes=nodes, lane_labels=lane_labels)
    if not ordered_lane_ids:
        return _single_unassigned_lane(nodes)

    lanes = _boundary_lanes(nodes, kind="start", enabled=separate_process_boundaries)
    lanes.extend(
        _assigned_lanes(
            nodes=nodes,
            ordered_lane_ids=ordered_lane_ids,
            lane_labels=lane_labels,
        )
    )
    lanes.extend(
        _unassigned_work_lanes(
            nodes,
            separate_process_boundaries=separate_process_boundaries,
        )
    )
    lanes.extend(
        _boundary_lanes(nodes, kind="end", enabled=separate_process_boundaries)
    )
    return tuple(lanes)


def _single_unassigned_lane(nodes: list[dict[str, Any]]) -> tuple[ElkLayoutLane, ...]:
    all_ids = tuple(
        str(node.get("id") or "") for node in nodes if str(node.get("id") or "")
    )
    return (ElkLayoutLane(id="unassigned", label="unassigned", node_ids=all_ids),)


def _boundary_lanes(
    nodes: list[dict[str, Any]], *, kind: str, enabled: bool
) -> list[ElkLayoutLane]:
    node_ids = _unassigned_kind_ids(nodes, kind=kind)
    if not enabled or not node_ids:
        return []
    return [
        ElkLayoutLane(
            id=f"unassigned_{kind}",
            label=f"Process {kind}",
            node_ids=node_ids,
        )
    ]


def _unassigned_work_lanes(
    nodes: list[dict[str, Any]], *, separate_process_boundaries: bool
) -> list[ElkLayoutLane]:
    node_ids = tuple(
        str(node.get("id") or "")
        for node in nodes
        if not str(node.get("lane") or "").strip()
        and (
            not separate_process_boundaries
            or str(node.get("kind") or "").lower() not in {"start", "end"}
        )
        and str(node.get("id") or "")
    )
    if not node_ids:
        return []
    return [ElkLayoutLane(id="unassigned", label="unassigned", node_ids=node_ids)]


def _unassigned_kind_ids(nodes: list[dict[str, Any]], *, kind: str) -> tuple[str, ...]:
    return tuple(
        str(node.get("id") or "")
        for node in nodes
        if not str(node.get("lane") or "").strip()
        and str(node.get("kind") or "").lower() == kind
        and str(node.get("id") or "")
    )


def _ordered_lane_ids(
    *, nodes: list[dict[str, Any]], lane_labels: dict[str, str]
) -> list[str]:
    ordered_lane_ids = list(lane_labels.keys())
    seen = set(ordered_lane_ids)
    for node in nodes:
        lane_id = str(node.get("lane") or "").strip()
        if not lane_id or lane_id in seen:
            continue
        seen.add(lane_id)
        ordered_lane_ids.append(lane_id)
        lane_labels[lane_id] = _humanize_lane_id(lane_id)
    return ordered_lane_ids


def _humanize_lane_id(lane_id: str) -> str:
    return lane_id.replace("_", " ").replace("-", " ").title()


def _assigned_lanes(
    *,
    nodes: list[dict[str, Any]],
    ordered_lane_ids: list[str],
    lane_labels: dict[str, str],
) -> list[ElkLayoutLane]:
    lanes: list[ElkLayoutLane] = []
    for lane_id in ordered_lane_ids:
        node_ids = tuple(
            str(node.get("id") or "")
            for node in nodes
            if str(node.get("lane") or "").strip() == lane_id
            and str(node.get("id") or "")
        )
        if node_ids:
            lanes.append(
                ElkLayoutLane(
                    id=lane_id,
                    label=str(lane_labels.get(lane_id) or lane_id),
                    node_ids=node_ids,
                )
            )
    return lanes


def _declared_lane_labels(process: dict[str, Any] | Any) -> dict[str, str]:
    if not isinstance(process, dict):
        return {}
    raw_lanes = process.get("lanes")
    if not isinstance(raw_lanes, list):
        process_block = process.get("process")
        if isinstance(process_block, dict):
            raw_lanes = process_block.get("lanes")
    if not isinstance(raw_lanes, list):
        return {}

    labels: dict[str, str] = {}
    for raw_lane in raw_lanes:
        if not isinstance(raw_lane, dict):
            continue
        lane_id = str(raw_lane.get("id") or "").strip()
        if lane_id:
            labels[lane_id] = str(raw_lane.get("name") or lane_id).strip() or lane_id
    return labels
