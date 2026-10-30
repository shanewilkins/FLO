"""Valid cyclic models expose consistent topology evidence through API and CLI."""

import json

import pytest
import yaml
from click.testing import CliRunner

from flo import api
from flo.app.cli import cli
from flo.process.ir._internal_shape import ir_to_internal_dict


def model():
    return {
        "spec_version": "0.1",
        "process": {"id": "cycles", "name": "Cycles"},
        "steps": [
            {"id": "s", "kind": "start"},
            {"id": "work", "kind": "task"},
            {"id": "gate", "kind": "decision"},
            {"id": "e", "kind": "end"},
        ],
        "transitions": [
            {
                "id": "entry",
                "source": "s",
                "target": "work",
                "handoff": {"type": "information"},
            },
            {"id": "forward", "source": "work", "target": "gate"},
            {
                "id": "repeat",
                "source": "gate",
                "target": "work",
                "outcome": "again",
                "rework": {
                    "reason": "Correct",
                    "frequency": {
                        "basis": "observed",
                        "numerator": 2,
                        "denominator": 10,
                        "observation_unit": "cases",
                    },
                },
                "extensions": {"example:evidence": {"ref": "record"}},
            },
            {"id": "self", "source": "gate", "target": "gate", "outcome": "retry"},
            {"id": "exit", "source": "gate", "target": "e", "outcome": "done"},
        ],
    }


def test_api_and_cli_inspect_expose_same_regions_without_changing_canonical_semantics():
    source = yaml.safe_dump(model(), sort_keys=False)
    validated = api.validate(source)
    assert validated.ok
    before = ir_to_internal_dict(validated.value)
    inspected = api.inspect(source)
    assert inspected.ok
    regions = inspected.value.as_dict()["cycle_regions"]
    assert len(regions) == 1
    region = regions[0]
    assert region["node_ids"] == ["gate", "work"]
    assert region["self_loop_node_ids"] == ["gate"]
    assert [edge["id"] for edge in region["entry_edges"]] == ["entry"]
    assert [edge["id"] for edge in region["exit_edges"]] == ["exit"]
    repeat = next(edge for edge in region["internal_edges"] if edge["id"] == "repeat")
    assert repeat["rework"] == model()["transitions"][2]["rework"]
    assert repeat["extensions"] == {"example:evidence": {"ref": "record"}}
    (info,) = [
        item
        for item in inspected.report.diagnostics
        if item.code == "structure-cycle-region"
    ]
    assert info.severity == "info"
    for analysis in ("model", "structure"):
        result = CliRunner().invoke(
            cli,
            ["inspect", "-", "--analysis", analysis, "--format", "json"],
            input=source,
        )
        assert result.exit_code == 0, result.output
        assert json.loads(result.stdout)["cycle_regions"] == regions
    text = CliRunner().invoke(
        cli, ["inspect", "-", "--analysis", "structure"], input=source
    )
    assert text.exit_code == 0
    assert (
        "Cyclic regions: 1" in text.stdout
        and "self-loops gate; entries 1; exits 1" in text.stdout
    )
    exported = api.export(source)
    assert exported.ok
    assert (
        next(
            edge for edge in json.loads(exported.value)["edges"] if edge["id"] == "self"
        ).get("rework")
        is None
    )
    assert ir_to_internal_dict(validated.value) == before


def test_inspection_regions_do_not_change_when_declarations_are_reordered():
    document = model()
    original = api.inspect(yaml.safe_dump(document)).value.as_dict()
    document["steps"].reverse()
    document["transitions"].reverse()
    shuffled = api.inspect(yaml.safe_dump(document)).value.as_dict()
    assert original == shuffled


@pytest.mark.parametrize("target", ["s", "missing"])
def test_graph_projection_does_not_bypass_existing_boundary_and_endpoint_checks(target):
    document = model()
    document["transitions"].append(
        {"source": "gate", "target": target, "outcome": "invalid"}
    )
    result = api.validate(yaml.safe_dump(document))
    assert not result.ok
    assert result.report.diagnostics[0].code == ("E1023" if target == "s" else "E1004")
