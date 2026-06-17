from click.testing import CliRunner
import yaml

from flo.core.cli import cli


def _write_spaghetti_svg_model(tmp_path, *, include_io: bool = False):
    model = tmp_path / "spaghetti_svg.flo"
    payload = {
        "spec_version": "0.1",
        "process": {
            "id": "spaghetti_svg_demo",
            "name": "Spaghetti SVG Demo",
            "metadata": {
                "locations": [
                    {
                        "id": "pantry",
                        "name": "Pantry",
                        "metadata": {"spatial": {"x": 0, "y": 0, "unit": "m"}},
                    },
                    {
                        "id": "bench",
                        "name": "Bench",
                        "metadata": {"spatial": {"x": 3, "y": 1, "unit": "m"}},
                    },
                ],
            },
        },
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {
                "id": "gather",
                "kind": "task",
                "name": "Gather",
                "location": "pantry",
                **(
                    {"outputs": ["flour"], "workers": ["assistant"]}
                    if include_io
                    else {}
                ),
            },
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "location": "bench",
                **(
                    {"inputs": ["flour"], "workers": ["assistant"]}
                    if include_io
                    else {}
                ),
            },
            {"id": "finish", "kind": "end", "name": "Done"},
        ],
        "edges": [
            {"source": "start", "target": "gather"},
            {"source": "gather", "target": "mix"},
            {"source": "mix", "target": "finish"},
        ],
    }
    model.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return model


def test_run_spaghetti_svg_export_emits_svg(tmp_path):
    model = _write_spaghetti_svg_model(tmp_path, include_io=True)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            str(model),
            "--export",
            "svg",
            "--diagram",
            "spaghetti",
        ],
    )

    assert result.exit_code == 0
    assert "<svg" in result.output
    assert 'data-flo-backend="svg"' in result.output


def test_run_flowchart_svg_export_emits_svg(tmp_path):
    model = tmp_path / "flowchart_svg.flo"
    payload = {
        "spec_version": "0.1",
        "process": {"id": "flowchart_svg_demo", "name": "Flowchart SVG Demo"},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {
                "id": "review",
                "kind": "decision",
                "name": "Approved?",
                "outcomes": {True: "finish", False: "rework"},
            },
            {"id": "rework", "kind": "task", "name": "Rework"},
            {"id": "finish", "kind": "end", "name": "Done"},
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
            "svg",
            "--diagram",
            "flowchart",
        ],
    )

    assert result.exit_code == 0
    assert "<svg" in result.output
    assert 'data-flo-diagram="flowchart"' in result.output
    assert 'data-node-kind="decision"' in result.output
    assert ">yes<" in result.output


def test_run_sppm_svg_export_emits_svg(tmp_path):
    model = tmp_path / "sppm_svg.flo"
    payload = {
        "spec_version": "0.1",
        "process": {"id": "sppm_svg_demo", "name": "SPPM SVG Demo"},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {
                "id": "intake",
                "kind": "task",
                "name": "Intake",
                "workers": ["Coordinator"],
                "metadata": {
                    "value_class": "RNVA",
                    "cycle_time": {"value": 4, "unit": "min"},
                    "description": "Capture request details and context.",
                },
            },
            {"id": "finish", "kind": "end", "name": "Done"},
        ],
        "edges": [
            {"source": "start", "target": "intake"},
            {"source": "intake", "target": "finish"},
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
            "svg",
            "--diagram",
            "sppm",
        ],
    )

    assert result.exit_code == 0
    assert "<svg" in result.output
    assert "SPPM SVG Demo" in result.output
    assert "Coordinator" in result.output
    assert "CT: 4 min" in result.output
    assert 'data-node-port-rail="in"' not in result.output


def test_run_svg_export_rejects_graphviz_backend_override(tmp_path, caplog):
    model = _write_spaghetti_svg_model(tmp_path)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            str(model),
            "--export",
            "svg",
            "--diagram",
            "spaghetti",
            "--render-backend",
            "graphviz",
        ],
    )

    assert result.exit_code == 1
    assert "SVG export currently requires" in result.output or any(
        "SVG export currently requires" in record.getMessage()
        for record in caplog.records
    )


def test_run_spaghetti_svg_export_on_reference_example_emits_stable_svg_markers():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/chocolate_chip_cookies.flo",
            "--export",
            "svg",
            "--diagram",
            "spaghetti",
        ],
    )

    assert result.exit_code == 0
    assert "<svg" in result.output
    assert 'data-flo-backend="svg"' in result.output
    assert 'data-route-channel="material"' in result.output
    assert 'data-route-channel="people"' in result.output
    assert "Pantry" in result.output
    assert "Prep Bench" in result.output
    assert "Oven Station" in result.output
