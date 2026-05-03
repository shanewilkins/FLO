from flo.render._sppm_text import (
    _enforce_max_length,
    _initials,
    _wrap_text,
    abbreviate_workers,
    apply_density_filter,
    format_text_field,
)


def test_abbreviate_workers_empty_and_overflow_cases():
    assert abbreviate_workers([]) == ""

    out = abbreviate_workers(["alice baker", "bob", "carol crew", "dora"])
    assert out == "AB, bob, CC, +1"


def test_initials_handles_single_token_lengths_and_multiword_names():
    assert _initials("qa") == "qa"
    assert _initials("operator") == "ope"
    assert _initials("lead_baker") == "LB"
    assert _initials("") == ""


def test_format_text_field_wraps_and_applies_html_breaks():
    out = format_text_field(
        "  alpha   beta   gamma  ",
        max_len=10,
        wrap_strategy="balanced",
        truncation_policy="none",
        html_break="<br/>",
    )
    assert out == "alpha<br/>beta gamma"


def test_format_text_field_empty_input_returns_empty():
    out = format_text_field(
        "   ",
        max_len=10,
        wrap_strategy="word",
        truncation_policy="ellipsis",
        html_break="<br/>",
    )
    assert out == ""


def test_apply_density_filter_for_teaching_compact_and_full():
    teaching = apply_density_filter(
        density="teaching",
        description="desc",
        ct_line="CT: 10 min",
        wt_line="WT: 2 min",
        workers_line="Ops",
        notes_line="note",
    )
    assert teaching == ["CT: 10 min", "note"]

    compact = apply_density_filter(
        density="compact",
        description="desc",
        ct_line="CT: 10 min",
        wt_line="WT: 2 min",
        workers_line="Ops",
        notes_line="note",
    )
    assert compact == ["CT: 10 min | WT: 2 min", "Ops", "note"]

    full = apply_density_filter(
        density="full",
        description="desc",
        ct_line="CT: 10 min",
        wt_line="WT: 2 min",
        workers_line="Ops",
        notes_line="note",
    )
    assert full == ["desc", "Ops", "CT: 10 min", "WT: 2 min", "note"]


def test_wrap_text_strategies_cover_hard_balanced_and_word_wrap():
    assert _wrap_text("abcdef", width=3, strategy="hard") == "abc\ndef"
    assert _wrap_text("alpha beta gamma", width=11, strategy="balanced") == "alpha\nbeta gamma"
    assert _wrap_text("alpha-beta-gamma", width=6, strategy="word") == "alpha-beta-gamma"
    assert _wrap_text("singleword", width=20, strategy="balanced") == "singleword"


def test_enforce_max_length_policy_variants():
    text = "alpha beta gamma"
    assert _enforce_max_length(text, max_len=None, policy="ellipsis") == text
    assert _enforce_max_length(text, max_len=100, policy="ellipsis") == text
    assert _enforce_max_length(text, max_len=8, policy="none") == text
    assert _enforce_max_length(text, max_len=8, policy="clip") == "alpha be"
    assert _enforce_max_length(text, max_len=3, policy="ellipsis") == "..."
    assert _enforce_max_length(text, max_len=8, policy="ellipsis") == "alpha..."
