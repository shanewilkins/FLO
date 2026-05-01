from click.testing import CliRunner
import yaml
import pytest

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


def test_run_json_export_rejects_sppm_density_flag():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "examples/reference/linear.flo", "--export", "json", "--sppm-label-density", "compact"],
    )
    assert result.exit_code == 1
    assert "require DOT output" in result.output


@pytest.mark.parametrize(
    "flag",
    [
        "--layout-max-width-px",
        "--layout-target-columns",
        "--sppm-max-label-step-name",
        "--sppm-max-label-workers",
        "--sppm-max-label-ctwt",
    ],
)
def test_run_sppm_rejects_non_positive_numeric_render_options(flag: str):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/washnfold.flo",
            "--export",
            "dot",
            "--diagram",
            "sppm",
            flag,
            "0",
        ],
    )
    assert result.exit_code == 1
    assert "expected a positive integer" in result.output


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


def test_run_spaghetti_location_kind_shapes_are_rendered(tmp_path):
    model = tmp_path / "location_kind_model.flo"
    payload = {
        "spec_version": "0.1",
        "process": {
            "id": "location_kinds_demo",
            "name": "Location Kinds Demo",
        },
        "locations": [
            {
                "id": "pantry",
                "name": "Pantry",
                "kind": "storage",
            },
            {
                "id": "oven_station",
                "name": "Oven Station",
                "kind": "processing",
            },
        ],
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
                "id": "bake",
                "kind": "task",
                "name": "Bake",
                "location": "oven_station",
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
            {"source": "gather", "target": "bake"},
            {"source": "bake", "target": "end"},
        ],
    }
    model.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", str(model), "--export", "dot", "--diagram", "spaghetti"],
    )
    assert result.exit_code == 0
    assert '"pantry" [label="Pantry", shape=box, fillcolor=lemonchiffon, color=goldenrod4' in result.output
    assert '"oven_station" [label="Oven Station", shape=hexagon, fillcolor=mistyrose, color=firebrick3' in result.output


def test_run_layout_wrap_lr_on_reference_fixture():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/washnfold.flo",
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
        ],
    )
    assert result.exit_code == 0
    assert "// Autoformat wrapped layout: orientation=lr" in result.output
    assert "rankdir=TB;" in result.output
    assert "cluster_wrap_lr_0" in result.output
    assert "splines=ortho" in result.output
    assert "minlen=2, penwidth=1.2" in result.output


def test_run_layout_wrap_tb_on_reference_fixture():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/washnfold.flo",
            "--export",
            "dot",
            "--diagram",
            "sppm",
            "--orientation",
            "tb",
            "--layout-wrap",
            "auto",
            "--layout-target-columns",
            "3",
        ],
    )
    assert result.exit_code == 0
    assert "// Autoformat wrapped layout: orientation=tb" in result.output
    assert "rankdir=LR;" in result.output
    assert "cluster_wrap_tb_0" in result.output
    assert "splines=ortho" in result.output
    assert "minlen=2, penwidth=1.2" in result.output


def test_run_layout_wrap_off_is_unchanged_on_reference_fixture():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/washnfold.flo",
            "--export",
            "dot",
            "--diagram",
            "sppm",
            "--layout-wrap",
            "off",
            "--layout-target-columns",
            "3",
        ],
    )
    assert result.exit_code == 0
    assert "splines=ortho" in result.output
    assert "cluster_wrap_" not in result.output
    assert "minlen=2, penwidth=1.2" not in result.output


def test_run_sppm_uses_diagrams_toml_defaults(tmp_path, monkeypatch):
    model = tmp_path / "washnfold_local.flo"
    model.write_text((
        "process:\n"
        "  id: local\n"
        "  name: Local\n"
        "steps:\n"
        "  - id: start\n"
        "    kind: start\n"
        "    name: Start\n"
        "  - id: a\n"
        "    kind: task\n"
        "    name: A\n"
        "  - id: b\n"
        "    kind: task\n"
        "    name: B\n"
        "  - id: c\n"
        "    kind: task\n"
        "    name: C\n"
        "  - id: d\n"
        "    kind: task\n"
        "    name: D\n"
        "  - id: end\n"
        "    kind: end\n"
        "    name: End\n"
        "edges:\n"
        "  - source: start\n"
        "    target: a\n"
        "  - source: a\n"
        "    target: b\n"
        "  - source: b\n"
        "    target: c\n"
        "  - source: c\n"
        "    target: d\n"
        "  - source: d\n"
        "    target: end\n"
    ), encoding="utf-8")

    diagrams = tmp_path / "diagrams.toml"
    diagrams.write_text(
        "[sppm]\n"
        "output_profile = \"print\"\n"
        "target_columns = 2\n"
        "wrap_layout = \"auto\"\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
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
    assert "// Autoformat wrapped layout: orientation=tb" in result.output
    assert "rankdir=LR;" in result.output
    assert "cluster_wrap_tb_0" in result.output


def test_run_sppm_cli_overrides_diagrams_toml_defaults(tmp_path, monkeypatch):
    model = tmp_path / "washnfold_local.flo"
    model.write_text((
        "process:\n"
        "  id: local\n"
        "  name: Local\n"
        "steps:\n"
        "  - id: start\n"
        "    kind: start\n"
        "    name: Start\n"
        "  - id: a\n"
        "    kind: task\n"
        "    name: A\n"
        "  - id: b\n"
        "    kind: task\n"
        "    name: B\n"
        "  - id: c\n"
        "    kind: task\n"
        "    name: C\n"
        "  - id: d\n"
        "    kind: task\n"
        "    name: D\n"
        "  - id: end\n"
        "    kind: end\n"
        "    name: End\n"
        "edges:\n"
        "  - source: start\n"
        "    target: a\n"
        "  - source: a\n"
        "    target: b\n"
        "  - source: b\n"
        "    target: c\n"
        "  - source: c\n"
        "    target: d\n"
        "  - source: d\n"
        "    target: end\n"
    ), encoding="utf-8")

    diagrams = tmp_path / "diagrams.toml"
    diagrams.write_text(
        "[sppm]\n"
        "output_profile = \"print\"\n"
        "target_columns = 2\n"
        "wrap_layout = \"auto\"\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
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
            "--orientation",
            "lr",
            "--layout-wrap",
            "off",
        ],
    )
    assert result.exit_code == 0
    assert "rankdir=LR;" in result.output
    assert "cluster_sppm_wrap_" not in result.output
