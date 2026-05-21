"""Deterministic SVG positioning for SPPM decision outcome labels."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TYPE_CHECKING

from flo.services._svg_utils import (
    _svg_edge_groups,
    _svg_node_outer_bounds,
    _write_svg_tree,
)

if TYPE_CHECKING:
    from flo.render._sppm_postprocess_contract import SppmSvgPostprocessContract


def postprocess_sppm_decision_outcome_labels_svg(
    *,
    output_path: Path,
    contract: SppmSvgPostprocessContract | None,
) -> None:
    """Apply deterministic SVG coordinates for SPPM decision outcome labels."""
    if contract is None or not contract.decision_outcome_label_edges:
        return

    tree = ET.parse(output_path)
    root = tree.getroot()
    node_bounds = _svg_node_outer_bounds(root)
    edge_groups = _svg_edge_groups(root)
    updated = False

    placements: list[
        tuple[ET.Element, str, tuple[float, float, float, float], str]
    ] = []
    for edge in contract.decision_outcome_label_edges:
        decision_id = getattr(edge, "anchor_id", None)
        if not decision_id:
            continue
        decision_bounds = node_bounds.get(decision_id)
        if decision_bounds is None:
            continue

        group, source_side = _find_edge_group_for_ids(
            edge_groups=edge_groups,
            source_id=edge.source_id,
            target_id=edge.target_id,
        )
        if group is None:
            continue

        expected_label = getattr(edge, "label_text", None)
        label_text = _extract_decision_outcome_label_text(
            group=group, expected_label=expected_label
        )
        if label_text is None:
            continue
        placements.append((group, source_side, decision_bounds, label_text))

    if not placements:
        return

    grouped: dict[
        tuple[str, str],
        list[tuple[ET.Element, str, tuple[float, float, float, float], str]],
    ] = {}
    for item in placements:
        _group, source_side, decision_bounds, _label = item
        decision_key = f"{decision_bounds[0]:.2f}:{decision_bounds[1]:.2f}:{decision_bounds[2]:.2f}:{decision_bounds[3]:.2f}"
        grouped.setdefault((decision_key, source_side), []).append(item)

    for (_decision_key, source_side), items in grouped.items():
        items.sort(key=lambda item: item[3].lower())
        for idx, (group, _side, decision_bounds, label_text) in enumerate(items):
            target_x, target_y = _decision_outcome_label_position(
                bounds=decision_bounds,
                source_side=source_side,
                tie_break_index=idx,
            )
            if _reposition_svg_edge_text_label(
                group=group,
                x=target_x,
                y=target_y,
                expected_label=label_text,
            ):
                updated = True

    if updated:
        _write_svg_tree(tree, output_path)


def _find_edge_group_for_ids(
    *,
    edge_groups: dict[str, ET.Element],
    source_id: str,
    target_id: str,
) -> tuple[ET.Element | None, str]:
    best_group: ET.Element | None = None
    best_source_side = "e"
    best_score = -1
    for title, group in edge_groups.items():
        parsed = _parse_edge_title_for_ids(
            title=title, source_id=source_id, target_id=target_id
        )
        if parsed is None:
            continue
        source_side, target_side = parsed
        score = int(source_side in {"n", "s", "e", "w"}) + int(
            target_side in {"n", "s", "e", "w"}
        )
        if score > best_score:
            best_group = group
            best_source_side = source_side
            best_score = score
            if score == 2:
                break
    return best_group, best_source_side


def _parse_edge_title_for_ids(
    *, title: str, source_id: str, target_id: str
) -> tuple[str, str] | None:
    if "->" not in title:
        return None
    left, right = title.split("->", 1)
    if not _endpoint_matches_node_id(left, source_id):
        return None
    if not _endpoint_matches_node_id(right, target_id):
        return None
    return (_endpoint_compass_side(left), _endpoint_compass_side(right))


def _endpoint_matches_node_id(endpoint: str, node_id: str) -> bool:
    return endpoint == node_id or endpoint.startswith(f"{node_id}:")


def _endpoint_compass_side(endpoint: str) -> str:
    if ":" not in endpoint:
        return "e"
    side = endpoint.rsplit(":", 1)[-1]
    if side in {"n", "s", "e", "w"}:
        return side
    return "e"


def _extract_decision_outcome_label_text(
    group: ET.Element, *, expected_label: str | None
) -> str | None:
    if expected_label is not None:
        expected = expected_label.strip()
        if not expected:
            return None
        for text in group.findall("{*}text"):
            raw = "".join(text.itertext()).strip()
            if raw == expected:
                return raw

    for text in group.findall("{*}text"):
        raw = "".join(text.itertext()).strip()
        if raw and " " not in raw:
            return raw
    return None


def _decision_outcome_label_position(
    *,
    bounds: tuple[float, float, float, float],
    source_side: str,
    tie_break_index: int,
) -> tuple[float, float]:
    left, top, right, bottom = bounds
    center_x = (left + right) / 2.0
    center_y = (top + bottom) / 2.0
    side = source_side if source_side in {"n", "s", "e", "w"} else "e"

    if side == "e":
        return right + 14.0, center_y + (tie_break_index * 12.0)
    if side == "w":
        return left - 14.0, center_y + (tie_break_index * 12.0)
    if side == "n":
        return center_x + 10.0 + (tie_break_index * 14.0), top - 10.0
    return center_x + 10.0 + (tie_break_index * 14.0), bottom + 14.0


def _reposition_svg_edge_text_label(
    *,
    group: ET.Element,
    x: float,
    y: float,
    expected_label: str | None = None,
) -> bool:
    moved = False
    for text in group.findall("{*}text"):
        raw = "".join(text.itertext()).strip()
        if not raw:
            continue
        if expected_label is not None and raw != expected_label.strip():
            continue
        if expected_label is None and " " in raw:
            continue
        previous_x = (
            float(text.attrib.get("x", "nan")) if text.attrib.get("x") else None
        )
        previous_y = (
            float(text.attrib.get("y", "nan")) if text.attrib.get("y") else None
        )
        text.attrib["x"] = f"{x:.2f}"
        text.attrib["y"] = f"{y:.2f}"
        if previous_x != x or previous_y != y:
            moved = True
        break
    return moved
