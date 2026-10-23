"""SPPM-owned conversion of requested width into a deterministic wrap budget."""

from dataclasses import replace

from ..options import Dimension, RenderOptions

_SPPM_HORIZONTAL_PADDING_PX = 56


def prepare_sppm_layout(options: RenderOptions) -> RenderOptions:
    """Use requested SPPM geometry as a deterministic reflow constraint."""
    if (
        options.diagram != "sppm"
        or options.orientation != "lr"
        or options.layout_width_px is None
    ):
        return options
    layout_budget = max(200, options.layout_width_px - _SPPM_HORIZONTAL_PADDING_PX)
    if options.layout_max_width_px is not None:
        layout_budget = min(layout_budget, options.layout_max_width_px)
    return replace(
        options,
        layout_wrap="auto",
        layout_max_width=Dimension(value=float(layout_budget), unit="px"),
        layout_max_width_px=layout_budget,
    )
