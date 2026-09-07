import yaml
from click.testing import CliRunner

from flo.app.cli import cli


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


def _write_partial_spaghetti_svg_model(tmp_path):
    model = tmp_path / "partial_spaghetti.flo"
    payload = {
        "spec_version": "0.1",
        "process": {
            "id": "partial_spaghetti",
            "name": "Partial Spaghetti",
            "metadata": {
                "locations": [
                    {
                        "id": "pantry",
                        "name": "Pantry",
                        "metadata": {"spatial": {"x": 0, "y": 0}},
                    },
                    {
                        "id": "oven",
                        "name": "Oven",
                        "metadata": {"spatial": {"x": 2, "y": 1}},
                    },
                    {"id": "bench", "name": "Bench"},
                ]
            },
        },
        "steps": [
            {"id": "start", "kind": "start", "location": "pantry"},
            {"id": "cook", "kind": "task", "location": "oven"},
            {"id": "mix", "kind": "task", "location": "bench"},
            {"id": "end", "kind": "end"},
        ],
        "transitions": [
            {"source": "start", "target": "cook"},
            {"source": "start", "target": "mix"},
            {"source": "cook", "target": "end"},
            {"source": "mix", "target": "end"},
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
            "render",
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


def test_run_spaghetti_partial_mode_warns_and_marks_artifact(tmp_path):
    model = _write_partial_spaghetti_svg_model(tmp_path)

    result = CliRunner().invoke(
        cli,
        [
            "render",
            str(model),
            "--export",
            "svg",
            "--diagram",
            "spaghetti",
            "--spaghetti-channel",
            "material",
        ],
    )

    assert result.exit_code == 0
    assert 'data-flo-notice="partial-map"' in result.output
    assert "spaghetti-missing-spatial" in result.stderr
    assert "bench" in result.stderr


def test_run_spaghetti_strict_spatial_rejects_partial_artifact(tmp_path):
    model = _write_partial_spaghetti_svg_model(tmp_path)

    result = CliRunner().invoke(
        cli,
        [
            "render",
            str(model),
            "--export",
            "svg",
            "--diagram",
            "spaghetti",
            "--spaghetti-channel",
            "material",
            "--spaghetti-strict-spatial",
        ],
    )

    assert result.exit_code != 0
    assert "spaghetti-missing-spatial" in result.stderr
    assert "<svg" not in result.output


def test_run_flowchart_svg_export_is_rejected(tmp_path):
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
            "render",
            str(model),
            "--export",
            "svg",
            "--diagram",
            "flowchart",
        ],
    )

    assert result.exit_code != 0
    assert "flowchart" in result.output


def test_run_sppm_typst_export_emits_publication_source(tmp_path):
    model = tmp_path / "sppm_typst.flo"
    model.write_text(
        yaml.safe_dump(
            {
                "spec_version": "0.1",
                "process": {"id": "sppm_typst_demo", "name": "SPPM Typst Demo"},
                "steps": [
                    {"id": "start", "kind": "start", "name": "Start"},
                    {"id": "finish", "kind": "end", "name": "Finish"},
                ],
                "edges": [{"source": "start", "target": "finish"}],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        ["render", str(model), "--export", "typst", "--diagram", "sppm"],
    )

    assert result.exit_code == 0, result.output
    assert "// Generated by FLO. Do not edit by hand." in result.output
    assert "// Publication: SPPM Typst Demo" in result.output
    assert '#metadata((flo_page_id: "main-p1"))' in result.output
    assert "*Process:* sppm_typst_demo" in result.output


def test_run_sppm_typst_export_paginates_with_continuation_metadata(tmp_path):
    model = tmp_path / "sppm_typst_paginated.flo"
    model.write_text(
        yaml.safe_dump(
            {
                "spec_version": "0.1",
                "process": {"id": "sppm_pages", "name": "SPPM Pages"},
                "steps": [
                    {"id": "start", "kind": "start"},
                    {"id": "first", "kind": "task"},
                    {"id": "second", "kind": "task"},
                    {"id": "finish", "kind": "end"},
                ],
                "edges": [
                    {"source": "start", "target": "first"},
                    {"source": "first", "target": "second"},
                    {"source": "second", "target": "finish"},
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        [
            "render",
            str(model),
            "--export",
            "typst",
            "--diagram",
            "sppm",
            "--layout-overflow",
            "paginate",
            "--layout-target-columns",
            "2",
        ],
    )

    assert result.exit_code == 0, result.output
    assert result.output.count("#pagebreak()") == 1
    assert '#metadata((flo_page_id: "main-p2"))' in result.output
    assert 'asset_path: "main-p2.svg"' in result.output
    assert "*Continues From:* main-p1" in result.output
    assert "*Steps:* start, first" in result.output


def test_run_sppm_typst_export_writes_page_svg_assets(tmp_path):
    model = tmp_path / "sppm_typst_assets.flo"
    output = tmp_path / "publication.typ"
    model.write_text(
        yaml.safe_dump(
            {
                "spec_version": "0.1",
                "process": {"id": "sppm_assets", "name": "SPPM Assets"},
                "steps": [
                    {"id": "start", "kind": "start"},
                    {"id": "first", "kind": "task"},
                    {"id": "second", "kind": "task"},
                    {"id": "finish", "kind": "end"},
                ],
                "edges": [
                    {"source": "start", "target": "first"},
                    {"source": "first", "target": "second"},
                    {"source": "second", "target": "finish"},
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        [
            "render",
            str(model),
            "--export",
            "typst",
            "--diagram",
            "sppm",
            "--layout-overflow",
            "paginate",
            "--layout-target-columns",
            "2",
            "--render-to",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert '#image("main-p1.svg", width: 100%' in output.read_text(encoding="utf-8")
    first_page_svg = (tmp_path / "main-p1.svg").read_text(encoding="utf-8")
    second_page_svg = (tmp_path / "main-p2.svg").read_text(encoding="utf-8")
    assert first_page_svg.startswith("<svg")
    assert second_page_svg.startswith("<svg")
    assert 'data-node-id="start"' in first_page_svg
    assert 'data-node-id="start"' not in second_page_svg
    assert 'data-node-id="second"' in second_page_svg


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
            "render",
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


def test_run_value_stream_svg_export_emits_dual_flow_surface():
    result = CliRunner().invoke(
        cli,
        [
            "render",
            "examples/reference/new_semantics.flo",
            "--export",
            "svg",
            "--diagram",
            "value_stream",
        ],
    )

    assert result.exit_code == 0
    assert 'data-flo-diagram="value_stream"' in result.output
    assert 'data-flow-kind="information"' in result.output
    assert 'data-flow-kind="material"' in result.output
    assert result.stderr == ""


def test_run_value_stream_partial_export_warns_without_inventing_material(tmp_path):
    model = tmp_path / "information_only.flo"
    payload = {
        "spec_version": "0.1",
        "process": {"id": "information_only", "name": "Information only"},
        "items": [{"id": "order", "name": "Order", "kind": "information"}],
        "steps": [
            {"id": "start", "kind": "start"},
            {
                "id": "intake",
                "kind": "task",
                "name": "Intake",
                "consumes": ["order"],
            },
            {"id": "end", "kind": "end"},
        ],
        "transitions": [
            {"source": "start", "target": "intake"},
            {"source": "intake", "target": "end"},
        ],
    }
    model.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        ["render", str(model), "--export", "svg", "--diagram", "value_stream"],
    )

    assert result.exit_code == 0
    assert 'data-flo-notice="partial-map"' in result.output
    assert 'data-flow-kind="material"' not in result.output
    assert "value-stream-material-absent" in result.stderr


def test_run_svg_export_rejects_non_svg_backend_override(tmp_path):
    model = _write_spaghetti_svg_model(tmp_path)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "render",
            str(model),
            "--export",
            "svg",
            "--diagram",
            "spaghetti",
            "--render-backend",
            "graphviz",
        ],
    )

    assert result.exit_code == 2
    assert "Invalid value for '--render-backend'" in result.output


def test_run_spaghetti_svg_export_on_reference_example_emits_stable_svg_markers():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "render",
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
