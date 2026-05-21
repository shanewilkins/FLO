from flo.render._callout_layout import (
    build_edge_callout_attrs,
    build_edge_text_callout_attrs,
    format_callout_table_html,
    format_callout_text_row,
    resolve_callout_near_source,
)


def test_build_edge_callout_attrs_near_source_uses_taillabel_and_offsets():
    attrs = build_edge_callout_attrs(
        table_html="<TABLE><TR><TD>A</TD></TR></TABLE>", near_source=True
    )

    assert attrs == (
        "taillabel=<<TABLE><TR><TD>A</TD></TR></TABLE>>",
        'labeldistance="0.7"',
        'labelangle="20"',
    )


def test_build_edge_callout_attrs_centered_uses_xlabel_only():
    attrs = build_edge_callout_attrs(
        table_html="<TABLE><TR><TD>A</TD></TR></TABLE>", near_source=False
    )

    assert attrs == ("xlabel=<<TABLE><TR><TD>A</TD></TR></TABLE>>",)


def test_format_callout_text_row_escapes_and_supports_bold_and_balign():
    row = format_callout_text_row(
        text="A < B",
        point_size="9",
        text_color="#123456",
        bold=True,
        balign="LEFT",
    )

    assert row == (
        '<TR><TD ALIGN="LEFT" BALIGN="LEFT"><FONT POINT-SIZE="9" COLOR="#123456"><B>A &lt; B</B></FONT></TD></TR>'
    )


def test_format_callout_table_html_wraps_rows_with_standard_table_shell():
    table = format_callout_table_html(
        row_html='<TR><TD ALIGN="LEFT">Row</TD></TR>',
        border_color="#666666",
        background_color="#FAFAFA",
        cell_padding="4",
    )

    assert table == (
        '<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" COLOR="#666666" BGCOLOR="#FAFAFA"><TR><TD ALIGN="LEFT">Row</TD></TR></TABLE>'
    )


def test_resolve_callout_near_source_prefers_source_when_requested():
    assert resolve_callout_near_source(prefer_near_source=True, edge_attrs=()) is True


def test_resolve_callout_near_source_avoids_center_overlap_with_existing_xlabel():
    assert (
        resolve_callout_near_source(
            prefer_near_source=False,
            edge_attrs=('xlabel="decision"',),
        )
        is True
    )


def test_resolve_callout_near_source_allows_center_when_no_overlap_signal():
    assert (
        resolve_callout_near_source(
            prefer_near_source=False,
            edge_attrs=("constraint=false",),
        )
        is False
    )


def test_build_edge_text_callout_attrs_near_source_adds_offsets():
    attrs = build_edge_text_callout_attrs(
        text="workers: assistant_baker", near_source=True
    )

    assert attrs == (
        'taillabel="workers: assistant_baker"',
        'labeldistance="0.7"',
        'labelangle="20"',
    )


def test_build_edge_text_callout_attrs_center_uses_xlabel_only():
    attrs = build_edge_text_callout_attrs(
        text="workers: assistant_baker", near_source=False
    )

    assert attrs == ('xlabel="workers: assistant_baker"',)
