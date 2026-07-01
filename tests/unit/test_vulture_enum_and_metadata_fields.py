from __future__ import annotations

from dataclasses import dataclass

from flo.render._sppm_postprocess_contract import build_svg_postprocess_contract
from flo.render._sppm_task_card import build_sppm_task_card_layout
from flo.render.layout_core.sppm_strategy import current_sppm_layout_strategy


@dataclass(frozen=True)
class _DummySegment:
    source_id: str
    target_id: str
    attrs: tuple[str, ...] = ()


@dataclass(frozen=True)
class _DummyAnchor:
    anchor_id: str


@dataclass(frozen=True)
class _DummyRoute:
    is_boundary: bool
    is_rework: bool
    segments: tuple[_DummySegment, ...]
    anchors: tuple[_DummyAnchor, ...]


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


def test_postprocess_contract_carries_expected_segment_count():
    route = _DummyRoute(
        is_boundary=True,
        is_rework=False,
        segments=(
            _DummySegment(
                source_id="start",
                target_id="__wrap_exit_lr_anchor",
                attrs=(),
            ),
            _DummySegment(source_id="__wrap_exit_lr_anchor", target_id="end"),
        ),
        anchors=(),
    )

    contract = build_svg_postprocess_contract(
        routes={("start", "end"): route},
        wrap_active=True,
        node_kinds=None,
    )

    assert len(contract.wrapped_boundary_edges) == 1
    edge = contract.wrapped_boundary_edges[0]
    assert edge.expected_segment_count == 2
