from flo.render._autoformat_wrap import OverflowPolicy, WrapPlan
from flo.render._sppm_continuation_labels import (
    build_sppm_continuation_label_attrs,
    format_sppm_continuation_html_label,
    resolve_explicit_sppm_continuation_tokens,
    resolve_sppm_continuation_anchor_tokens,
)


def test_build_sppm_continuation_label_attrs_uses_step_refs_and_page_numbers():
    wrap_plan = WrapPlan(
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

    outgoing, incoming = build_sppm_continuation_label_attrs(
        source="b",
        target="c",
        wrap_plan=wrap_plan,
        is_secondary=False,
    )

    assert outgoing == (
        'headlabel=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#455A64" BGCOLOR="#FFFFFF"><TR><TD ALIGN="LEFT"><FONT POINT-SIZE="10" COLOR="#455A64"><B>Continue to p2 [c]</B></FONT></TD></TR></TABLE>>',
    )
    assert incoming == (
        'taillabel=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#455A64" BGCOLOR="#FFFFFF"><TR><TD ALIGN="LEFT"><FONT POINT-SIZE="10" COLOR="#455A64"><B>Continued from p1 [b]</B></FONT></TD></TR></TABLE>>',
    )


def test_format_sppm_continuation_html_label_uses_lighter_secondary_emphasis():
    primary = format_sppm_continuation_html_label(
        text="Continue to p2 [c]", is_secondary=False
    )
    secondary = format_sppm_continuation_html_label(
        text="Continue to p2 [rework]", is_secondary=True
    )

    assert "<B>Continue to p2 [c]</B>" in primary
    assert 'COLOR="#455A64"' in primary
    assert "<B>" not in secondary
    assert 'COLOR="#90A4AE"' in secondary


def test_resolve_sppm_continuation_anchor_tokens_prefers_explicit_metadata_aliases():
    wrap_plan = WrapPlan(
        active=False,
        chunk_size=2,
        chunks=[],
        display_chunks=[],
        boundary_edges=set(),
        node_chunk_index={},
        node_display_index={},
        placement_plan=None,
        overflow_policy=OverflowPolicy(
            planner="chunked",
            wrap_mode="off",
            fit_mode="fit-preferred",
            max_major_px=None,
            margin_px=48,
            min_chunk_size=3,
            break_preference="sequence-boundary",
            continuation_mode="boundary-corridor",
            strict=False,
        ),
    )

    outgoing, incoming = resolve_sppm_continuation_anchor_tokens(
        edge={"metadata": {"continuation_out": "P9-Z", "continuation_in": "P7-A"}},
        source="a",
        target="b",
        wrap_plan=wrap_plan,
    )

    assert outgoing == "P9-Z"
    assert incoming == "P7-A"


def test_resolve_sppm_continuation_anchor_tokens_falls_back_to_wrap_tokens():
    wrap_plan = WrapPlan(
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

    outgoing, incoming = resolve_sppm_continuation_anchor_tokens(
        edge={"metadata": {}},
        source="b",
        target="c",
        wrap_plan=wrap_plan,
    )

    assert outgoing == "P2-C"
    assert incoming == "P1-B"


def test_resolve_explicit_sppm_continuation_tokens_mirrors_single_sided_metadata():
    outgoing, incoming = resolve_explicit_sppm_continuation_tokens(
        {"metadata": {"continuation_to": "P2-OPS"}}
    )

    assert outgoing == "P2-OPS"
    assert incoming == "P2-OPS"
