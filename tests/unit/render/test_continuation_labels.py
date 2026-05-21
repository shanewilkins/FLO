from flo.render._autoformat_wrap import OverflowPolicy, WrapPlan
from flo.render._continuation_labels import (
    build_continuation_label_attrs,
    format_continuation_html_label,
)


def _wrap_plan() -> WrapPlan:
    return WrapPlan(
        active=True,
        chunk_size=2,
        chunks=[["a", "b"], ["c", "d"]],
        display_chunks=[["a", "b"], ["c", "d"]],
        boundary_edges={("b", "c")},
        node_chunk_index={"a": 0, "b": 0, "c": 1, "d": 1},
        node_display_index={"a": 0, "b": 1, "c": 0, "d": 1},
        placement_plan=None,
        overflow_policy=OverflowPolicy(
            planner="chunked",
            wrap_mode="auto",
            fit_mode="fit-preferred",
            max_major_px=None,
            margin_px=48,
            min_chunk_size=3,
            break_preference="sequence-boundary",
            continuation_mode="boundary-corridor",
            strict=False,
        ),
    )


def test_build_continuation_label_attrs_uses_reference_formatter_and_page_numbers():
    outgoing, incoming = build_continuation_label_attrs(
        source="b",
        target="c",
        wrap_plan=_wrap_plan(),
        is_secondary=False,
        reference_formatter=lambda node_id: f"[{node_id}]",
    )

    assert outgoing == (
        'headlabel=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#455A64" BGCOLOR="#FFFFFF"><TR><TD ALIGN="LEFT"><FONT POINT-SIZE="10" COLOR="#455A64"><B>Continue to p2 [c]</B></FONT></TD></TR></TABLE>>',
    )
    assert incoming == (
        'taillabel=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#455A64" BGCOLOR="#FFFFFF"><TR><TD ALIGN="LEFT"><FONT POINT-SIZE="10" COLOR="#455A64"><B>Continued from p1 [b]</B></FONT></TD></TR></TABLE>>',
    )


def test_format_continuation_html_label_uses_lighter_secondary_emphasis():
    primary = format_continuation_html_label(
        text="Continue to p2 [c]", is_secondary=False
    )
    secondary = format_continuation_html_label(
        text="Continue to p2 [rework]", is_secondary=True
    )

    assert "<B>Continue to p2 [c]</B>" in primary
    assert 'COLOR="#455A64"' in primary
    assert "<B>" not in secondary
    assert 'COLOR="#90A4AE"' in secondary
