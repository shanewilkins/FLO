from click.testing import CliRunner
import yaml

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
    assert "Continued from p1 [decision]" in result.output
    assert "Continue to p2 [rework]" in result.output