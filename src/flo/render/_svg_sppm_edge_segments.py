from __future__ import annotations

from typing import Any


def _candidate_segment_indexes(
    points: Any,
    *,
    avoid_near_source: bool,
    prefer_near_source: bool,
    preferred_index: int | None,
) -> range:
    segment_count = max(0, len(points) - 1)
    if preferred_index is not None and 0 <= preferred_index < segment_count:
        return range(preferred_index, preferred_index + 1)
    if prefer_near_source:
        return range(min(1, segment_count))
    if not avoid_near_source or segment_count <= 2:
        return range(segment_count)
    return range(2, segment_count)


def _first_rightward_horizontal_segment_index(points: Any) -> int | None:
    segment_count = max(0, len(points) - 1)
    for index in range(segment_count):
        start = points[index]
        end = points[index + 1]
        dx = float(end.x_px - start.x_px)
        dy = float(end.y_px - start.y_px)
        if dx <= 0.0:
            continue
        if abs(dy) > 1e-6:
            continue
        return index
    return None


def _longest_segment_index(points: Any, *, segment_indexes: Any) -> int | None:
    best_index: int | None = None
    best_length = -1.0
    for index in segment_indexes:
        start = points[index]
        end = points[index + 1]
        dx = float(end.x_px - start.x_px)
        dy = float(end.y_px - start.y_px)
        length = abs(dx) + abs(dy)
        if length <= best_length:
            continue
        best_length = length
        best_index = index
    return best_index
