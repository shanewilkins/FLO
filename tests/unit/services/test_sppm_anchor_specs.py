from flo.services._sppm_anchor_specs import (
    extract_sppm_branch_anchor_specs,
    extract_sppm_return_anchor_specs,
)


def test_extract_sppm_return_anchor_specs_matches_two_segment_loop():
    dot = "\n".join(
        [
            "digraph {",
            '  "review":w -> "__sppm_rework_corridor_review" [arrowhead=none, constraint=false];',
            '  "__sppm_rework_corridor_review" -> "approve":s [constraint=false];',
            "}",
        ]
    )

    specs = extract_sppm_return_anchor_specs(dot)

    assert len(specs) == 1
    assert specs[0].anchor_id == "__sppm_rework_corridor_review"
    assert specs[0].source_id == "review"
    assert specs[0].target_id == "approve"


def test_extract_sppm_return_anchor_specs_requires_arrowhead_none_and_first_leg():
    dot = "\n".join(
        [
            "digraph {",
            '  "review" -> "__sppm_rework_corridor_review" [constraint=false];',
            '  "__sppm_rework_corridor_review" -> "approve":s [constraint=false];',
            '  "__sppm_rework_corridor_other" -> "archive":s [constraint=false];',
            "}",
        ]
    )

    assert extract_sppm_return_anchor_specs(dot) == []


def test_extract_sppm_branch_anchor_specs_matches_two_segment_branch_drop():
    dot = "\n".join(
        [
            "digraph {",
            '  "decision":s -> "__sppm_rework_corridor_decision" [arrowhead=none, weight=0];',
            '  "__sppm_rework_corridor_decision" -> "rework":n [constraint=false];',
            "}",
        ]
    )

    specs = extract_sppm_branch_anchor_specs(dot)

    assert len(specs) == 1
    assert specs[0].anchor_id == "__sppm_rework_corridor_decision"
    assert specs[0].source_id == "decision"
    assert specs[0].target_id == "rework"


def test_extract_sppm_branch_anchor_specs_ignores_missing_first_leg():
    dot = "\n".join(
        [
            "digraph {",
            '  "decision":s -> "__sppm_rework_corridor_decision" [weight=0];',
            '  "__sppm_rework_corridor_decision" -> "rework":n [constraint=false];',
            "}",
        ]
    )

    assert extract_sppm_branch_anchor_specs(dot) == []
