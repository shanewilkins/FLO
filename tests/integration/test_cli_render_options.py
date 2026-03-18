from click.testing import CliRunner
import yaml

from flo.core.cli import cli


def test_run_swimlane_diagram_emits_clusters():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "examples/reference/linear.flo", "--export", "dot", "--diagram", "swimlane"],
    )
    assert result.exit_code == 0
    assert "subgraph cluster_sales" in result.output
    assert "subgraph cluster_ops" in result.output


def test_run_summary_detail_omits_outcome_edge_labels():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/conformance/valid/valid_decision_with_outcomes.flo",
            "--export",
            "dot",
            "--detail",
            "summary",
        ],
    )
    assert result.exit_code == 0
    assert 'label="yes"' not in result.output
    assert 'label="no"' not in result.output


def test_run_json_export_rejects_render_only_flags():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "examples/reference/linear.flo", "--export", "json", "--diagram", "swimlane"],
    )
    assert result.exit_code == 1
    assert "require DOT output" in result.output


def test_run_show_notes_and_orientation(tmp_path):
    model = tmp_path / "note_model.flo"
    payload = {
        "spec_version": "0.1",
        "process": {"id": "notes_demo", "name": "Notes Demo"},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {
                "id": "review",
                "kind": "task",
                "name": "Review",
                "note": "Requires manager signoff",
            },
            {"id": "finish", "kind": "end", "name": "Done"},
        ],
        "edges": [
            {"source": "start", "target": "review"},
            {"source": "review", "target": "finish"},
        ],
    }
    model.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            str(model),
            "--export",
            "dot",
            "--orientation",
            "tb",
            "--show-notes",
        ],
    )
    assert result.exit_code == 0
    assert "rankdir=TB;" in result.output
    assert "Note: Requires manager signoff" in result.output


def test_run_json_export_rejects_show_notes_flag():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "examples/reference/linear.flo", "--export", "json", "--show-notes"],
    )
    assert result.exit_code == 1
    assert "require DOT output" in result.output


def test_run_subprocess_view_parent_only_hides_subnodes():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/chocolate_chip_cookies.flo",
            "--export",
            "dot",
            "--diagram",
            "swimlane",
            "--subprocess-view",
            "parent-only",
        ],
    )
    assert result.exit_code == 0
    assert "cluster_subprocess_prep_subprocess" not in result.output
    assert '"gather_equipment" [label="Gather Equipment"' not in result.output
    assert '"prep_subprocess" [label="Prep Subprocess"' in result.output


def test_run_json_export_rejects_subprocess_view_flag():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "examples/reference/linear.flo", "--export", "json", "--subprocess-view", "parent-only"],
    )
    assert result.exit_code == 1
    assert "require DOT output" in result.output


def test_run_ingredients_export_rejects_diagram_flag():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "examples/reference/chocolate_chip_cookies.flo", "--export", "ingredients", "--diagram", "swimlane"],
    )
    assert result.exit_code == 1
    assert "require DOT output" in result.output


def test_run_movement_export_rejects_diagram_flag():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "examples/reference/chocolate_chip_cookies.flo", "--export", "movement", "--diagram", "swimlane"],
    )
    assert result.exit_code == 1
    assert "require DOT output" in result.output


def test_run_spaghetti_diagram_emits_neato_layout():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "examples/reference/chocolate_chip_cookies.flo", "--export", "dot", "--diagram", "spaghetti"],
    )
    assert result.exit_code == 0
    assert "layout=neato" in result.output
    assert '"pantry"' in result.output


def test_run_spaghetti_people_channel_filters_material_edges():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/chocolate_chip_cookies.flo",
            "--export",
            "dot",
            "--diagram",
            "spaghetti",
            "--spaghetti-channel",
            "people",
        ],
    )
    assert result.exit_code == 0
    assert "color=royalblue4" in result.output
    assert "style=dashed" in result.output
    assert "color=tomato4" not in result.output


def test_run_spaghetti_people_worker_mode_labels_worker_traces():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/chocolate_chip_cookies.flo",
            "--export",
            "dot",
            "--diagram",
            "spaghetti",
            "--spaghetti-channel",
            "people",
            "--spaghetti-people-mode",
            "worker",
            "--profile",
            "analysis",
        ],
    )
    assert result.exit_code == 0
    assert "xlabel=\"P assistant_baker" in result.output or "xlabel=\"P lead_baker" in result.output


def test_run_json_export_rejects_spaghetti_channel_flag():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "examples/reference/linear.flo", "--export", "json", "--spaghetti-channel", "people"],
    )
    assert result.exit_code == 1
    assert "require DOT output" in result.output


def test_run_json_export_rejects_spaghetti_people_mode_flag():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "examples/reference/linear.flo", "--export", "json", "--spaghetti-people-mode", "worker"],
    )
    assert result.exit_code == 1
    assert "require DOT output" in result.output


def test_run_spaghetti_renders_boundary_overlay_from_process_metadata(tmp_path):
    model = tmp_path / "boundary_model.flo"
    payload = {
        "spec_version": "0.1",
        "process": {
            "id": "boundary_demo",
            "name": "Boundary Demo",
            "metadata": {
                "layout_boundary": {
                    "type": "rectangle",
                    "x": -1.0,
                    "y": -1.0,
                    "width": 8.0,
                    "height": 6.0,
                    "label": "Kitchen Boundary",
                }
            },
        },
        "steps": [
            {
                "id": "start",
                "kind": "start",
                "name": "Start",
            },
            {
                "id": "gather",
                "kind": "task",
                "name": "Gather",
                "location": "pantry",
                "outputs": ["flour"],
            },
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "location": "prep_bench",
                "inputs": ["flour"],
            },
            {
                "id": "end",
                "kind": "end",
                "name": "End",
            },
        ],
        "edges": [
            {"source": "start", "target": "gather"},
            {"source": "gather", "target": "mix"},
            {"source": "mix", "target": "end"},
        ],
    }
    model.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", str(model), "--export", "dot", "--diagram", "spaghetti"],
    )
    assert result.exit_code == 0
    assert "__facility_boundary_0" in result.output
    assert "__facility_boundary_label" in result.output
    assert "Kitchen Boundary" in result.output
