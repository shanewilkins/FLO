from click.testing import CliRunner
import yaml
import xml.etree.ElementTree as ET

from flo.core.cli import cli


def test_run_sppm_wrap_outputs_continuation_labels(tmp_path):
    model = tmp_path / "continuations.flo"
    payload = {
        "spec_version": "0.1",
        "process": {"id": "continuations_demo", "name": "Continuations Demo"},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "prep", "kind": "task", "name": "Prep"},
            {"id": "decision", "kind": "decision", "name": "Approved?"},
            {"id": "rework", "kind": "task", "name": "Rework", "metadata": {"value_class": "NVA"}},
            {"id": "finish", "kind": "task", "name": "Finish", "metadata": {"value_class": "VA"}},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "transitions": [
            {"source": "start", "target": "prep"},
            {"source": "prep", "target": "decision"},
            {"source": "decision", "target": "finish", "outcome": "yes"},
            {"source": "decision", "target": "rework", "outcome": "no", "edge_type": "rework", "rework": True},
            {"source": "rework", "target": "finish", "edge_type": "rework", "rework": True},
            {"source": "finish", "target": "end"},
        ],
    }
    model.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            str(model),
            "--export",
            "dot",
            "--diagram",
            "sppm",
            "--layout-wrap",
            "auto",
            "--layout-target-columns",
            "3",
        ],
    )

    assert result.exit_code == 0
    assert '"__sppm_rework_corridor_decision_rework" [shape=circle' in result.output
    assert 'label="P1-D"' in result.output


def test_run_sppm_explicit_continuation_anchor_metadata_outputs_deterministic_tokens(tmp_path):
    model = tmp_path / "continuations_explicit.flo"
    payload = {
        "spec_version": "0.1",
        "process": {"id": "continuations_explicit", "name": "Continuations Explicit"},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "handoff", "kind": "task", "name": "Handoff"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "transitions": [
            {"source": "start", "target": "handoff"},
            {
                "source": "handoff",
                "target": "end",
                "metadata": {
                    "continuation_to": "P2-OPS",
                    "continuation_from": "P1-H",
                },
            },
        ],
    }
    model.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            str(model),
            "--export",
            "dot",
            "--diagram",
            "sppm",
        ],
    )

    assert result.exit_code == 0
    assert '"__sppm_boundary_corridor_handoff_end_out" [shape=circle' in result.output
    assert '"__sppm_boundary_corridor_handoff_end_in" [shape=circle' in result.output
    assert 'label="P2-OPS"' in result.output
    assert 'label="P1-H"' in result.output


def test_rendered_svg_preserves_explicit_continuation_anchor_tokens(tmp_path):
    model = tmp_path / "continuations_svg.flo"
    payload = {
        "spec_version": "0.1",
        "process": {"id": "continuations_svg", "name": "Continuations SVG"},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "handoff", "kind": "task", "name": "Handoff"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "transitions": [
            {"source": "start", "target": "handoff"},
            {
                "source": "handoff",
                "target": "end",
                "metadata": {
                    "continuation_to": "P2-OPS",
                    "continuation_from": "P1-H",
                },
            },
        ],
    }
    model.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    svg_output = tmp_path / "continuations.svg"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            str(model),
            "--diagram",
            "sppm",
            "--render-to",
            str(svg_output),
        ],
    )

    assert result.exit_code == 0
    svg_text = svg_output.read_text(encoding="utf-8")
    assert "P2-OPS" in svg_text
    assert "P1-H" in svg_text


def test_run_wrapped_showcase_uses_explicit_continuation_override_tokens():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/sppm_feature_showcase_wrapped.flo",
            "--export",
            "dot",
            "--diagram",
            "sppm",
            "--orientation",
            "lr",
            "--layout-wrap",
            "auto",
            "--layout-target-columns",
            "3",
            "--publication-page-format",
            "letter",
        ],
    )

    assert result.exit_code == 0
    assert "// Autoformat wrapped layout: orientation=lr" in result.output
    assert "subgraph wrap_rank_lr_0" in result.output
    assert 'label="P2-QA"' in result.output
    assert 'label="P1-SVC"' in result.output


def test_wrapped_showcase_svg_preserves_explicit_continuation_override_tokens(tmp_path):
    svg_output = tmp_path / "wrapped_showcase.svg"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/sppm_feature_showcase_wrapped.flo",
            "--diagram",
            "sppm",
            "--orientation",
            "lr",
            "--layout-wrap",
            "auto",
            "--layout-target-columns",
            "3",
            "--publication-page-format",
            "letter",
            "--render-to",
            str(svg_output),
        ],
    )

    assert result.exit_code == 0
    svg_text = svg_output.read_text(encoding="utf-8")
    assert "P2-QA" in svg_text
    assert "P1-SVC" in svg_text


def test_sppm_decision_outcome_label_positions_are_stable_across_repeated_svg_renders(tmp_path):
    model = tmp_path / "decision_labels_stable.flo"
    payload = {
        "spec_version": "0.1",
        "process": {"id": "decision_labels_stable", "name": "Decision Labels Stable"},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "decision", "kind": "decision", "name": "Approved?"},
            {"id": "approve", "kind": "task", "name": "Approve"},
            {"id": "rework", "kind": "task", "name": "Rework"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "transitions": [
            {"source": "start", "target": "decision"},
            {"source": "decision", "target": "approve", "outcome": "yes"},
            {"source": "decision", "target": "rework", "outcome": "no", "edge_type": "rework", "rework": True},
            {"source": "approve", "target": "end"},
            {"source": "rework", "target": "end"},
        ],
    }
    model.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    svg_one = tmp_path / "decision_labels_1.svg"
    svg_two = tmp_path / "decision_labels_2.svg"
    runner = CliRunner()

    result_one = runner.invoke(
        cli,
        [
            "run",
            str(model),
            "--diagram",
            "sppm",
            "--orientation",
            "lr",
            "--render-to",
            str(svg_one),
        ],
    )
    result_two = runner.invoke(
        cli,
        [
            "run",
            str(model),
            "--diagram",
            "sppm",
            "--orientation",
            "lr",
            "--render-to",
            str(svg_two),
        ],
    )

    assert result_one.exit_code == 0
    assert result_two.exit_code == 0
    assert _decision_label_positions(svg_one) == _decision_label_positions(svg_two)


def _decision_label_positions(svg_path) -> dict[str, tuple[str, str]]:
    root = ET.parse(svg_path).getroot()
    positions: dict[str, tuple[str, str]] = {}
    for text in root.findall(".//{*}text"):
        label = "".join(text.itertext()).strip()
        if label not in {"yes", "no"}:
            continue
        x = text.attrib.get("x")
        y = text.attrib.get("y")
        if x is None or y is None:
            continue
        positions[label] = (x, y)
    return positions