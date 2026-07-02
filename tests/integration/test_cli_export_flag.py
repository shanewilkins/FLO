from click.testing import CliRunner
import json
import yaml

from flo.core.cli import cli


def test_default_path_accepts_export_json_flag():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["render", "examples/reference/linear.flo", "--export", "json"]
    )
    assert result.exit_code == 0
    assert '"process"' in result.output
    assert '"nodes"' in result.output


def test_default_path_export_json_emits_canonical_ir_contract() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["render", "examples/reference/new_semantics.flo", "--export", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert set(payload.keys()) == {"process", "nodes", "edges"}
    assert payload["process"]["id"] == "canonical_semantics_reference"
    assert isinstance(payload["nodes"], list)
    assert isinstance(payload["edges"], list)
    assert payload["nodes"]
    assert payload["edges"]

    first_node = payload["nodes"][0]
    assert "id" in first_node
    assert "kind" in first_node

    first_edge = payload["edges"][0]
    assert "source" in first_edge
    assert "target" in first_edge


def test_default_path_exports_json_to_file(tmp_path):
    runner = CliRunner()
    out = tmp_path / "linear.json"
    result = runner.invoke(
        cli,
        [
            "render",
            "examples/reference/linear.flo",
            "--export",
            "json",
            "-o",
            str(out),
        ],
    )
    assert result.exit_code == 0
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert '"process"' in content
    assert '"nodes"' in content


def test_default_path_export_json_reports_compile_contract_error(tmp_path) -> None:
    model = tmp_path / "invalid_export.flo"
    model.write_text(
        yaml.safe_dump(
            {
                "spec_version": "0.1",
                "process": {"name": "Missing Id"},
                "steps": [
                    {"id": "start", "kind": "start", "name": "Start"},
                    {"id": "end", "kind": "end", "name": "End"},
                ],
                "transitions": [{"source": "start", "target": "end"}],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["render", str(model), "--export", "json"])

    assert result.exit_code != 0
    assert "process.id must be a non-empty string" in result.output


def test_default_path_export_json_reports_write_error(tmp_path) -> None:
    missing_dir = tmp_path / "missing"
    out = missing_dir / "linear.json"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "render",
            "examples/reference/linear.flo",
            "--export",
            "json",
            "-o",
            str(out),
        ],
    )

    assert result.exit_code != 0
    assert "I/O error writing" in result.output


def test_default_path_accepts_export_ingredients_flag():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "render",
            "examples/reference/chocolate_chip_cookies.flo",
            "--export",
            "ingredients",
        ],
    )
    assert result.exit_code == 0
    assert "Materials and Equipment" in result.output


def test_default_path_accepts_export_ingredients_flag_for_canonical_fixture():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "render",
            "examples/reference/new_semantics.flo",
            "--export",
            "ingredients",
        ],
    )

    assert result.exit_code == 0
    assert "Items and Resources" in result.output
    assert "Work Ticket" in result.output
    assert "Baker" in result.output


def test_default_path_accepts_export_movement_flag():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "render",
            "examples/reference/chocolate_chip_cookies.flo",
            "--export",
            "movement",
        ],
    )
    assert result.exit_code == 0
    assert "Inferred Material Movement" in result.output


def test_default_path_accepts_export_movement_flag_for_canonical_payload(tmp_path):
    model = tmp_path / "canonical_movement.flo"
    payload = {
        "spec_version": "0.1",
        "process": {
            "id": "canonical_movement_demo",
            "name": "Canonical Movement Demo",
        },
        "items": [
            {"id": "dough", "name": "Dough", "kind": "material"},
        ],
        "resources": [
            {"id": "baker", "name": "Baker", "kind": "person"},
        ],
        "locations": [
            {
                "id": "bench",
                "name": "Bench",
                "metadata": {"spatial": {"x": 0.0, "y": 0.0, "unit": "m"}},
            },
            {
                "id": "sealer",
                "name": "Sealer",
                "metadata": {"spatial": {"x": 3.0, "y": 4.0, "unit": "m"}},
            },
        ],
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {
                "id": "shape",
                "kind": "task",
                "name": "Shape Dough",
                "location": "bench",
                "produces": ["dough"],
                "performed_by": ["baker"],
            },
            {
                "id": "pack",
                "kind": "task",
                "name": "Pack Dough",
                "location": "sealer",
                "consumes": ["dough"],
                "performed_by": ["baker"],
            },
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "shape"},
            {"source": "shape", "target": "pack"},
            {"source": "pack", "target": "end"},
        ],
    }
    model.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["render", str(model), "--export", "movement"])

    assert result.exit_code == 0
    assert "Inferred Material Movement" in result.output
    assert "bench -> sealer" in result.output
    assert "items=dough" in result.output
    assert "distance=5.00 m" in result.output
    assert "Inferred People Movement" in result.output
    assert "workers=baker" in result.output
