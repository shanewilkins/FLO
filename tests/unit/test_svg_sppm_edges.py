from __future__ import annotations

from types import SimpleNamespace

import pytest

from flo.render._diagnostics import RenderDiagnostic
from flo.render._svg_sppm_edges import (
    _attachment_miss_warn_px,
    _clip_edge_points_to_node_bounds,
    _edge_stroke,
    _edge_svg,
    _edge_token_svg,
    _is_synthetic_sppm_lane,
    _lane_header_avoid_bounds,
    _label_placement,
    _normalize_rework_edge_points,
    _placement_overlaps_bounds,
)
from flo.render.layout_core.models import LayoutBounds, LayoutPoint


@pytest.mark.parametrize(
    ("is_rework", "variant", "as_rework", "expected"),
    [
        (False, None, False, ("#475569", None, 2.5)),
        (True, "branch", False, ("#b91c1c", "2 6", 2.6)),
        (True, "return", False, ("#c2410c", "2 6", 2.4)),
        (False, None, True, ("#b91c1c", "2 6", 2.5)),
    ],
)
def test_edge_stroke_styles(
    is_rework: bool,
    variant: str | None,
    as_rework: bool,
    expected: tuple[str, str | None, float],
) -> None:
    edge = SimpleNamespace(is_rework=is_rework, rework_variant=variant)

    actual = _edge_stroke(edge, render_as_rework_style=as_rework)

    assert actual == expected


def test_normalize_rework_edge_points_dedupes_and_collapses_short_span() -> None:
    points = (
        LayoutPoint(0.0, 0.0),
        LayoutPoint(0.0, 0.0),
        LayoutPoint(40.0, 80.0),
        LayoutPoint(20.0, 80.0),
    )

    normalized = _normalize_rework_edge_points(
        points,
        is_rework=True,
        rework_variant="branch",
    )

    assert normalized == (LayoutPoint(0.0, 0.0), LayoutPoint(20.0, 80.0))


def test_normalize_rework_edge_points_keeps_non_axis_aligned_path() -> None:
    points = (
        LayoutPoint(0.0, 0.0),
        LayoutPoint(0.0, 0.0),
        LayoutPoint(80.0, 40.0),
        LayoutPoint(110.0, 85.0),
    )

    normalized = _normalize_rework_edge_points(
        points,
        is_rework=True,
        rework_variant="return",
    )

    assert normalized == (
        LayoutPoint(0.0, 0.0),
        LayoutPoint(80.0, 40.0),
        LayoutPoint(110.0, 85.0),
    )


def test_attachment_warn_threshold_accounts_for_queue_geometry() -> None:
    queue_bounds = LayoutBounds(10.0, 20.0, 200.0, 120.0)
    task_bounds = LayoutBounds(10.0, 20.0, 200.0, 120.0)

    queue_threshold = _attachment_miss_warn_px(
        node_kind="queue",
        node_bounds=queue_bounds,
    )
    task_threshold = _attachment_miss_warn_px(
        node_kind="task",
        node_bounds=task_bounds,
    )

    assert queue_threshold == 50.0
    assert task_threshold == 24.0


def test_clip_edge_points_records_large_attachment_correction_diagnostic() -> None:
    diagnostics: list[RenderDiagnostic] = []
    points = (
        LayoutPoint(1000.0, 1000.0),
        LayoutPoint(200.0, 25.0),
    )

    clipped = _clip_edge_points_to_node_bounds(
        points,
        source_bounds=LayoutBounds(0.0, 0.0, 120.0, 50.0),
        source_kind="task",
        target_bounds=None,
        target_kind="task",
        diagnostics=diagnostics,
        edge_id="a->b",
    )

    assert len(clipped) == 2
    assert diagnostics
    diagnostic = diagnostics[0]
    assert diagnostic.code == "sppm-attachment-miss-distance"
    assert diagnostic.severity == "warning"
    assert diagnostic.metadata["edge"] == "a->b"
    assert diagnostic.metadata["endpoint_role"] == "source"


def test_edge_svg_emits_rework_variant_markup_and_label_bounds() -> None:
    edge_path = SimpleNamespace(
        edge=("decision", "rework"),
        points=(LayoutPoint(0.0, 0.0), LayoutPoint(200.0, 40.0)),
        label="retry",
        label_point=None,
        is_rework=True,
        rework_variant="branch",
        callout_lines=(),
        callout_near_source=False,
        outgoing_token=None,
        incoming_token=None,
    )

    parts, annotation_bounds = _edge_svg(edge_path)
    svg = "".join(parts)

    assert 'data-edge-kind="rework"' in svg
    assert 'data-edge-rework-variant="branch"' in svg
    assert 'stroke="#b91c1c"' in svg
    assert 'stroke-dasharray="2 6"' in svg
    assert 'data-edge-source="decision"' in svg
    assert 'data-edge-target="rework"' in svg
    assert len(annotation_bounds) == 1


def test_label_placement_shifts_to_avoid_overlapping_bounds() -> None:
    points = (
        LayoutPoint(0.0, 0.0),
        LayoutPoint(120.0, 0.0),
    )
    overlapping_bounds = (
        LayoutBounds(x_px=40.0, y_px=-25.0, width_px=40.0, height_px=30.0),
    )

    placement = _label_placement(
        points,
        avoid_bounds=overlapping_bounds,
        box_width=28.0,
        box_height=18.0,
    )

    assert placement.y != -8.0
    assert not _placement_overlaps_bounds(
        placement,
        box_width=28.0,
        box_height=18.0,
        avoid_bounds=overlapping_bounds,
    )


def test_lane_header_avoid_bounds_caps_height() -> None:
    lanes = (
        SimpleNamespace(
            id="lane_a",
            bounds=LayoutBounds(x_px=0.0, y_px=0.0, width_px=500.0, height_px=120.0),
        ),
        SimpleNamespace(
            id="lane_b",
            bounds=LayoutBounds(x_px=0.0, y_px=0.0, width_px=500.0, height_px=20.0),
        ),
    )

    clipped = _lane_header_avoid_bounds(lanes)

    assert clipped[0].height_px == 34.0
    assert clipped[1].height_px == 20.0


def test_edge_token_svg_marks_source_and_target_positions() -> None:
    points = (
        LayoutPoint(0.0, 0.0),
        LayoutPoint(100.0, 0.0),
    )

    source_svg = "".join(_edge_token_svg(points=points, token="WIP", near_source=True))
    target_svg = "".join(
        _edge_token_svg(points=points, token="DONE", near_source=False)
    )

    assert 'data-edge-token="WIP"' in source_svg
    assert 'data-edge-token-position="source"' in source_svg
    assert 'data-edge-token="DONE"' in target_svg
    assert 'data-edge-token-position="target"' in target_svg


@pytest.mark.parametrize(
    ("lane_id", "expected"),
    [
        ("__sppm_row_0", True),
        ("operations", False),
    ],
)
def test_is_synthetic_sppm_lane(lane_id: str, expected: bool) -> None:
    assert _is_synthetic_sppm_lane(lane_id) is expected


def test_edge_svg_returns_empty_for_single_point_path() -> None:
    edge_path = SimpleNamespace(
        edge=("a", "b"),
        points=(LayoutPoint(0.0, 0.0),),
        label=None,
        label_point=None,
        is_rework=False,
        rework_variant=None,
        callout_lines=(),
        callout_near_source=False,
        outgoing_token=None,
        incoming_token=None,
    )

    parts, annotation_bounds = _edge_svg(edge_path)

    assert parts == []
    assert annotation_bounds == ()


def test_edge_svg_uses_explicit_label_point_when_present() -> None:
    edge_path = SimpleNamespace(
        edge=("a", "b"),
        points=(LayoutPoint(0.0, 0.0), LayoutPoint(120.0, 0.0)),
        label="ok",
        label_point=LayoutPoint(60.0, 20.0),
        is_rework=False,
        rework_variant=None,
        callout_lines=(),
        callout_near_source=False,
        outgoing_token=None,
        incoming_token=None,
    )

    parts, annotation_bounds = _edge_svg(edge_path)
    svg = "".join(parts)

    assert '<text x="60.0" y="21.0" text-anchor="middle"' in svg
    assert len(annotation_bounds) == 1


def test_edge_svg_renders_callout_and_edge_tokens() -> None:
    edge_path = SimpleNamespace(
        edge=("qa", "rework"),
        points=(
            LayoutPoint(0.0, 0.0),
            LayoutPoint(100.0, 0.0),
            LayoutPoint(180.0, 60.0),
        ),
        label="review",
        label_point=None,
        is_rework=False,
        rework_variant=None,
        callout_lines=("handoff", "owner: QA"),
        callout_near_source=True,
        outgoing_token="WIP",
        incoming_token="DONE",
    )

    parts, annotation_bounds = _edge_svg(edge_path)
    svg = "".join(parts)

    assert 'data-edge-token="WIP"' in svg
    assert 'data-edge-token="DONE"' in svg
    assert "owner: QA" in svg
    assert len(annotation_bounds) >= 2


@pytest.mark.parametrize(
    ("is_rework", "variant", "expected_len"),
    [
        (False, "branch", 3),
        (True, "unknown", 3),
    ],
)
def test_normalize_rework_edge_points_passthrough_cases(
    is_rework: bool,
    variant: str,
    expected_len: int,
) -> None:
    points = (
        LayoutPoint(0.0, 0.0),
        LayoutPoint(50.0, 50.0),
        LayoutPoint(100.0, 30.0),
    )

    normalized = _normalize_rework_edge_points(
        points,
        is_rework=is_rework,
        rework_variant=variant,
    )

    assert len(normalized) == expected_len
    assert normalized == points


def test_label_placement_records_overlap_fallback_diagnostic_when_unavoidable() -> None:
    diagnostics: list[RenderDiagnostic] = []
    points = (
        LayoutPoint(0.0, 0.0),
        LayoutPoint(120.0, 0.0),
    )
    unavoidable_bounds = (
        LayoutBounds(x_px=-500.0, y_px=-500.0, width_px=1000.0, height_px=1000.0),
    )

    _label_placement(
        points,
        avoid_bounds=unavoidable_bounds,
        box_width=28.0,
        box_height=18.0,
        diagnostics=diagnostics,
        diagnostic_context={"edge": "a->b"},
    )

    assert diagnostics
    assert diagnostics[0].code == "sppm-annotation-overlap-fallback"
    assert diagnostics[0].metadata["edge"] == "a->b"
