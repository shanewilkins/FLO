from __future__ import annotations

from flo.render._sppm_task_card import build_sppm_task_card_layout
from flo.render.layout_core.sppm_strategy import current_sppm_layout_strategy


def test_current_sppm_layout_strategy_exposes_all_strategy_fields():
    strategy = current_sppm_layout_strategy()

    assert strategy.partition_mode in {"branch_aligned", "chain_progressive"}
    assert strategy.port_constraints in {"fixed_side", "fixed_order"}
    assert strategy.helper_anchors in {"off", "conditional", "always"}
    assert strategy.spacing_profile in {"compact", "balanced", "roomy"}


def test_task_card_layout_exposes_padding_metrics():
    content = type(
        "_Content",
        (),
        {
            "title": "Task",
            "info_lines": ["line one", "line two"],
        },
    )()

    layout = build_sppm_task_card_layout(content)

    assert layout.header_padding_px > 0
    assert layout.body_padding_px > 0
    assert layout.body_text_offset_px > 0
