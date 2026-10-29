"""White Belt semantic failures must stop every validated consumer."""

import json

import pytest
import yaml
from click.testing import CliRunner

from flo import api
from flo.app.cli import cli
from flo.errors import EXIT_COMPILE_ERROR, EXIT_VALIDATION_ERROR


def _model():
    return {
        "spec_version": "0.1",
        "process": {"id": "audit", "name": "Audit"},
        "steps": [
            {"id": "start", "kind": "start"},
            {"id": "work", "kind": "task"},
            {"id": "end", "kind": "end"},
        ],
    }


def _profile(value=0, unit="min"):
    return {
        "basis": "observed",
        "results": {
            "mean": {"method": "mean", "value": value, "unit": unit},
        },
        "primary": "mean",
        "analysis_input": "mean",
    }


def _invalid_model(case):
    model = _model()
    step = model["steps"][1]
    step_overrides = {
        "attrs": {"attrs": "discarded"},
        "metadata": {"metadata": "discarded"},
        "attrs_metadata": {"attrs": {"metadata": "discarded"}},
        "parent": {"subprocess_parent": 42},
        "null_children": {"kind": "subprocess", "subnodes": None},
        "two_child_lists": {"kind": "subprocess", "subnodes": [], "steps": []},
        "attrs_wait_aliases": {
            "attrs": {"metadata": {"wait_time": {}, "wait_before": {}}}
        },
        "attrs_outcomes": {"attrs": {"outcomes": {"a": "end", "b": "end"}}},
    }
    if case in step_overrides:
        step.update(step_overrides[case])
    elif case == "null_transitions":
        model["transitions"] = None
    elif case == "process_metadata":
        model["process"]["metadata"] = "discarded"
    elif case == "empty_items":
        model["process"]["items"] = []
        step["consumes"] = ["missing"]
    elif case == "empty_resources":
        model["process"]["resources"] = []
        step["performed_by"] = ["missing"]
    elif case == "empty_locations":
        model["process"]["locations"] = []
        step["location"] = "missing"
    elif case == "lane":
        model["lanes"] = [{"id": "known", "name": "Known"}]
        step["lane"] = "missing"
    elif case == "location":
        model["process"]["locations"] = [{"id": "known", "name": "Known"}]
        step["location"] = "missing"
    elif case == "schema":
        step["name"] = ["not", "text"]
    elif case == "render_intent":
        model["process"]["metadata"] = {"render": {"unknown": "invalid"}}
    else:
        step.update(kind="queue", metadata={"buffer_capacity": case})
    return model


@pytest.mark.parametrize(
    "case",
    [
        "null_transitions",
        "process_metadata",
        "attrs",
        "metadata",
        "attrs_metadata",
        "parent",
        "null_children",
        "two_child_lists",
        "attrs_wait_aliases",
        "attrs_outcomes",
        "empty_items",
        "empty_resources",
        "empty_locations",
        "lane",
        "location",
        "schema",
        "render_intent",
        True,
        None,
    ],
)
def test_semantic_failures_stop_api_and_cli_consumers(tmp_path, case):
    content = yaml.safe_dump(_invalid_model(case))
    source = tmp_path / "invalid.flo"
    source.write_text(content)
    for operation in (api.validate, api.inspect, api.export):
        result = operation(content, source_path=str(source))
        assert not result.ok, case
        assert result.value is None
        assert result.diagnostics[0].message
        assert result.diagnostics[0].source == str(source)
    runner = CliRunner()
    validation = runner.invoke(cli, ["validate", str(source), "--format", "json"])
    assert validation.exit_code in {EXIT_COMPILE_ERROR, EXIT_VALIDATION_ERROR}, (
        validation.output
    )
    diagnostic = json.loads(validation.output)
    assert diagnostic["message"]
    output = tmp_path / "invalid.svg"
    for command in (
        ["inspect", str(source), "--format", "json"],
        ["export", str(source)],
        ["render", str(source), "--render-to", str(output)],
    ):
        result = runner.invoke(cli, command)
        assert result.exit_code == validation.exit_code, result.output
    assert not output.exists()


def test_valid_context_references_and_timing_survive_export():
    model = _model()
    model["process"]["locations"] = {"floor": [{"id": "station", "name": "Station"}]}
    model["lanes"] = [{"id": "operator", "name": "Operator"}]
    model["steps"][1].update(
        lane="operator",
        location="station",
        wait_time=_profile(),
    )
    content = yaml.safe_dump(model)
    result = api.export(content)
    assert result.ok, result.diagnostics
    assert api.export(content).value == result.value
    work = json.loads(result.value)["nodes"][1]
    assert work["location"] == "station"
    assert work["lane"] == "operator"
    assert work["wait_time"] == _profile()


@pytest.mark.parametrize("node_index", [0, 2])
@pytest.mark.parametrize(
    "field",
    [
        "cycle_time",
        "changeover_time",
        "wait_time",
    ],
)
def test_control_boundaries_cannot_own_work_or_queue_timing(node_index, field):
    model = _model()
    model["steps"][node_index][field] = _profile()
    result = api.validate(yaml.safe_dump(model))
    assert not result.ok
    assert result.diagnostics[0].code == "E0222"
    assert f"{field} cannot be declared on kind" in result.diagnostics[0].message


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), 10**400])
@pytest.mark.parametrize(
    "field",
    ["quantity", "canonical_quantity", "spatial", "rework_count", "rework_rate"],
)
def test_typed_numeric_evidence_must_be_finite(value, field):
    model = _model()
    if field == "spatial":
        model["process"]["locations"] = [
            {
                "id": "station",
                "name": "Station",
                "spatial": {"x": value, "y": 0},
            }
        ]
    elif field.startswith("rework"):
        model["transitions"] = [
            {
                "source": "start",
                "target": "work",
                "rework": {
                    "frequency": {
                        "basis": "observed",
                        "numerator": value,
                        "denominator": 10,
                        "observation_unit": "cases",
                    }
                },
            },
            {"source": "work", "target": "end"},
        ]
    else:
        quantity = {"kind": "measure", "value": value, "unit": "kg"}
        if field == "canonical_quantity":
            quantity.update(value=1, canonical_value=value, canonical_unit="kg")
        model["process"]["items"] = [
            {
                "id": "material",
                "name": "Material",
                "kind": "material",
                "quantity": quantity,
            }
        ]
    result = api.validate(yaml.safe_dump(model))
    assert not result.ok
    assert result.diagnostics[0].code in {
        "E0222",
        "E1209",
        "E1212",
        "E1215",
        "E1401",
        "E1403",
    }
