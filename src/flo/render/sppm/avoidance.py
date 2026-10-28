"""Conservative rectangular covers for nonrectangular SPPM node shapes."""

from ..layout_core.models import LayoutBounds


def node_avoid_bounds(bounds: LayoutBounds, kind: str) -> tuple[LayoutBounds, ...]:
    """Reserve polygon interiors while retaining usable space beside their tips."""
    if kind not in {"queue", "wait", "decision"}:
        return (bounds,)
    bands = []
    for index in range(16):
        low, high = index / 16, (index + 1) / 16
        if kind in {"queue", "wait"}:
            fraction = 1 - low
        else:
            fraction = 1 - min(abs(low - 0.5), abs(high - 0.5)) * 2
        width = bounds.width_px * fraction
        bands.append(
            LayoutBounds(
                x_px=bounds.x_px + (bounds.width_px - width) / 2,
                y_px=bounds.y_px + bounds.height_px * low,
                width_px=width,
                height_px=bounds.height_px / 16,
            )
        )
    return tuple(bands)
