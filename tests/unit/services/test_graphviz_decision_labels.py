"""Unit tests for deterministic SPPM decision outcome label SVG postprocessing."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from flo.services._graphviz_decision_labels import postprocess_sppm_decision_outcome_labels_svg


def test_postprocess_sppm_decision_outcome_labels_svg_applies_deterministic_offsets(tmp_path: Path):
    contract = SimpleNamespace(
        decision_outcome_label_edges=[
            SimpleNamespace(source_id="decision", target_id="approve", anchor_id="decision"),
            SimpleNamespace(source_id="decision", target_id="rework", anchor_id="decision"),
        ]
    )
    svg_path = tmp_path / "decision_labels.svg"
    svg_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
    <g class="node"><title>decision</title><polygon points="200,100 260,100 260,140 200,140" /></g>
    <g class="edge"><title>decision:e-&gt;approve:w</title><path d="M 0,0 L 1,1" /><text x="10" y="10">yes</text></g>
    <g class="edge"><title>decision:e-&gt;rework:w</title><path d="M 0,0 L 1,1" /><text x="12" y="12">no</text></g>
</svg>
""",
        encoding="utf-8",
    )

    postprocess_sppm_decision_outcome_labels_svg(output_path=svg_path, contract=contract)
    svg = svg_path.read_text(encoding="utf-8")

    assert '<text x="274.00" y="120.00">no</text>' in svg
    assert '<text x="274.00" y="132.00">yes</text>' in svg


def test_postprocess_sppm_decision_outcome_labels_svg_places_south_exit_labels_with_stable_tiebreak(tmp_path: Path):
    contract = SimpleNamespace(
        decision_outcome_label_edges=[
            SimpleNamespace(source_id="decision", target_id="__anchor_a", anchor_id="decision", label_text="yes"),
            SimpleNamespace(source_id="decision", target_id="__anchor_b", anchor_id="decision", label_text="no"),
        ]
    )
    svg_path = tmp_path / "decision_labels_south.svg"
    svg_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
    <g class="node"><title>decision</title><polygon points="200,100 260,100 260,140 200,140" /></g>
    <g class="edge"><title>decision:s-&gt;__anchor_a</title><path d="M 0,0 L 1,1" /><text x="10" y="10">yes</text></g>
    <g class="edge"><title>decision:s-&gt;__anchor_b</title><path d="M 0,0 L 1,1" /><text x="12" y="12">no</text></g>
</svg>
""",
        encoding="utf-8",
    )

    postprocess_sppm_decision_outcome_labels_svg(output_path=svg_path, contract=contract)
    svg = svg_path.read_text(encoding="utf-8")

    assert '<text x="240.00" y="154.00">no</text>' in svg
    assert '<text x="254.00" y="154.00">yes</text>' in svg


def test_postprocess_sppm_decision_outcome_labels_svg_places_west_exit_labels_with_stable_tiebreak(tmp_path: Path):
    contract = SimpleNamespace(
        decision_outcome_label_edges=[
            SimpleNamespace(source_id="decision", target_id="__anchor_a", anchor_id="decision", label_text="yes"),
            SimpleNamespace(source_id="decision", target_id="__anchor_b", anchor_id="decision", label_text="no"),
        ]
    )
    svg_path = tmp_path / "decision_labels_west.svg"
    svg_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
    <g class="node"><title>decision</title><polygon points="200,100 260,100 260,140 200,140" /></g>
    <g class="edge"><title>decision:w-&gt;__anchor_a</title><path d="M 0,0 L 1,1" /><text x="10" y="10">yes</text></g>
    <g class="edge"><title>decision:w-&gt;__anchor_b</title><path d="M 0,0 L 1,1" /><text x="12" y="12">no</text></g>
</svg>
""",
        encoding="utf-8",
    )

    postprocess_sppm_decision_outcome_labels_svg(output_path=svg_path, contract=contract)
    svg = svg_path.read_text(encoding="utf-8")

    assert '<text x="186.00" y="120.00">no</text>' in svg
    assert '<text x="186.00" y="132.00">yes</text>' in svg


def test_postprocess_sppm_decision_outcome_labels_svg_places_north_exit_labels_with_stable_tiebreak(tmp_path: Path):
    contract = SimpleNamespace(
        decision_outcome_label_edges=[
            SimpleNamespace(source_id="decision", target_id="__anchor_a", anchor_id="decision", label_text="yes"),
            SimpleNamespace(source_id="decision", target_id="__anchor_b", anchor_id="decision", label_text="no"),
        ]
    )
    svg_path = tmp_path / "decision_labels_north.svg"
    svg_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
    <g class="node"><title>decision</title><polygon points="200,100 260,100 260,140 200,140" /></g>
    <g class="edge"><title>decision:n-&gt;__anchor_a</title><path d="M 0,0 L 1,1" /><text x="10" y="10">yes</text></g>
    <g class="edge"><title>decision:n-&gt;__anchor_b</title><path d="M 0,0 L 1,1" /><text x="12" y="12">no</text></g>
</svg>
""",
        encoding="utf-8",
    )

    postprocess_sppm_decision_outcome_labels_svg(output_path=svg_path, contract=contract)
    svg = svg_path.read_text(encoding="utf-8")

    assert '<text x="240.00" y="90.00">no</text>' in svg
    assert '<text x="254.00" y="90.00">yes</text>' in svg


def test_postprocess_sppm_decision_outcome_labels_svg_does_not_move_non_decision_labels(tmp_path: Path):
    contract = SimpleNamespace(
        decision_outcome_label_edges=[
            SimpleNamespace(source_id="decision", target_id="approve", anchor_id="decision", label_text="yes"),
        ]
    )
    svg_path = tmp_path / "decision_labels_no_bleed.svg"
    svg_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
    <g class="node"><title>decision</title><polygon points="200,100 260,100 260,140 200,140" /></g>
    <g class="edge"><title>decision:e-&gt;approve:w</title><path d="M 0,0 L 1,1" /><text x="10" y="10">yes</text></g>
    <g class="edge"><title>task:e-&gt;done:w</title><path d="M 0,0 L 1,1" /><text x="50" y="60">1-&gt;2</text></g>
</svg>
""",
        encoding="utf-8",
    )

    postprocess_sppm_decision_outcome_labels_svg(output_path=svg_path, contract=contract)
    svg = svg_path.read_text(encoding="utf-8")

    assert '<text x="274.00" y="120.00">yes</text>' in svg
    assert '<text x="50" y="60">1-&gt;2</text>' in svg
