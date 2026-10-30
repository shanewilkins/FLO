"""Evidence survives validation, inspection, exchange and diagram presentation."""

import json
from copy import deepcopy
from xml.etree import ElementTree as ET

import pytest
import yaml
from click.testing import CliRunner

from flo import api
from flo.app.cli import cli
from flo.process.ir import validate_ir
from flo.render import render_artifact
from flo.source import compile_adapter, parse_adapter


def profile(value):
    return {
        "basis": "observed",
        "primary": "median",
        "analysis_input": "mean",
        "results": {
            "median": {"method": "median", "value": value, "unit": "min"},
            "mean": {"method": "mean", "value": 2, "unit": "min"},
        },
    }


def model():
    return {
        "spec_version": "0.1",
        "process": {
            "id": "evidence",
            "name": "Evidence",
            "lead_time": profile(30),
            "items": [
                {"id": "ticket", "name": "Request form", "kind": "information"},
                {"id": "part", "name": "Component", "kind": "material"},
            ],
            "resources": [
                {"id": "worker_id", "name": "Named Performer", "kind": "person"}
            ],
            "locations": [
                {
                    "id": "a",
                    "name": "Receiving",
                    "spatial": {"x": 0, "y": 0, "unit": "m"},
                },
                {
                    "id": "b",
                    "name": "Packing",
                    "spatial": {"x": 1, "y": 0, "unit": "m"},
                },
            ],
        },
        "steps": [
            {"id": "start", "kind": "start"},
            {
                "id": "work",
                "kind": "task",
                "name": "Work",
                "cycle_time": profile(1),
                "wait_time": profile(0),
                "changeover_time": profile(0),
                "performed_by": ["worker_id"],
                "consumes": ["ticket"],
                "produces": ["part"],
                "location": "a",
            },
            {
                "id": "finish",
                "kind": "task",
                "name": "Finish",
                "cycle_time": profile(1),
                "wait_time": profile(0),
                "changeover_time": profile(0),
                "consumes": ["part"],
                "location": "b",
            },
            {"id": "end", "kind": "end"},
        ],
        "transitions": [
            {"source": "start", "target": "work"},
            {
                "source": "work",
                "target": "finish",
                "handoff": {
                    "type": "material",
                    "extensions": {"example:owner": "Packing"},
                },
                "rework": {
                    "reason": "Correction",
                    "frequency": {
                        "basis": "observed",
                        "numerator": 0,
                        "denominator": 10,
                        "observation_unit": "orders",
                        "evidence_ref": "audit:Friday",
                    },
                    "note": "Recorded zero",
                    "extensions": {"example:sample": "Friday"},
                },
            },
            {"source": "finish", "target": "end"},
        ],
    }


@pytest.mark.parametrize("supplied", [0, 30])
@pytest.mark.parametrize("diagram", ["sppm", "swimlane", "spaghetti", "value_stream"])
def test_every_diagram_distinguishes_supplied_lead_time_and_relation_evidence(
    diagram, supplied
):
    data = model()
    data["process"]["lead_time"] = profile(supplied)
    source = yaml.safe_dump(data)
    process = compile_adapter(parse_adapter(source))
    validate_ir(process)
    before = deepcopy(process)
    artifact = render_artifact(process, options={"diagram": diagram})
    root = ET.fromstring(artifact.content)  # noqa: S314 - Renderer-produced SVG.
    text = " ".join(" ".join(root.itertext()).split())
    assert "Supplied lead time (observed)" in text
    assert f"{supplied} min" in text
    assert "Modeled lead time" in text
    assert "Handoff work" in text
    assert "material" in text
    assert "Correction" in text
    assert "0 of 10 orders (observed)" in text
    assert "audit:Friday" in text
    assert process == before


def test_inspection_and_exchange_preserve_supplied_profiles_and_relation_extensions():
    source = yaml.safe_dump(model())
    inspected = api.inspect(source)
    assert inspected.ok, inspected.diagnostics
    report = inspected.value.as_dict()
    assert report["timing"]["supplied_lead_time"] == model()["process"]["lead_time"]
    # The analytical selectors yield 12 minutes; supplied primary remains 30.
    assert report["timing"]["modeled_lead_time_seconds"] == 720
    assert (
        report["relations"]["rework"][0]["relation"]
        == model()["transitions"][1]["rework"]
    )
    assert (
        report["relations"]["handoffs"][0]["relation"]
        == model()["transitions"][1]["handoff"]
    )
    exported = api.export(source)
    assert exported.ok
    assert (
        json.loads(exported.value)["process"]["lead_time"]
        == model()["process"]["lead_time"]
    )
    text = CliRunner().invoke(
        cli, ["inspect", "-", "--analysis", "model"], input=source
    )
    assert text.exit_code == 0
    assert "Supplied lead time (observed): 30 min" in text.stdout
    assert "Correction" in text.stdout


def test_performer_ids_are_resolved_for_task_presentation_without_changing_exchange():
    data = model()
    process = compile_adapter(parse_adapter(yaml.safe_dump(data)))
    artifact = render_artifact(
        process, options={"diagram": "sppm", "sppm_label_density": "full"}
    )
    assert "Workers: Named Performer" in artifact.content
    assert process.nodes[1].performed_by == ["worker_id"]


@pytest.mark.parametrize("collection", ["items", "resources", "locations"])
def test_top_level_collections_are_rejected_without_precedence_or_translation(
    collection,
):
    data = model()
    data[collection] = data["process"][collection]
    result = api.validate(yaml.safe_dump(data))
    assert not result.ok
    assert result.diagnostics[0].code == "E0220"
    assert result.diagnostics[0].field_path == collection


def test_value_stream_cards_present_primary_without_changing_analytical_timeline():
    source = yaml.safe_dump(model())
    process = compile_adapter(parse_adapter(source))
    artifact = render_artifact(process, options={"diagram": "value_stream"})
    assert "P/T 1 min" in artifact.content
    assert "Modeled lead time: 12 min" in artifact.content


def test_processing_and_zero_setup_use_book_terms_without_claiming_cadence_or_switching():
    # Book glossary: P/T is active processing; S/T is setup, including zero.
    # C/T needs successive completions and C/O needs an identified mode switch.
    data = model()
    data["steps"] = [data["steps"][0], data["steps"][1], data["steps"][-1]]
    del data["transitions"]
    work = data["steps"][1]
    for field, value in (("cycle_time", 1), ("wait_time", 0), ("changeover_time", 0)):
        work[field] = profile(value)
        work[field]["analysis_input"] = "median"
    source = yaml.safe_dump(data)
    process = compile_adapter(parse_adapter(source))
    before = deepcopy(process)
    for diagram, processing, setup in (
        ("sppm", "P/T: 1 min", "S/T: 0 min"),
        ("value_stream", "P/T 1 min", "S/T 0 s"),
    ):
        artifact = render_artifact(
            process, options={"diagram": diagram, "sppm_label_density": "full"}
        )
        root = ET.fromstring(artifact.content)  # noqa: S314 - Renderer-produced SVG.
        text = " ".join(" ".join(root.itertext()).split())
        assert processing in text
        assert setup in text
        assert "CT " not in text and "C/O " not in text
    inspected = CliRunner().invoke(cli, ["inspect", "-"], input=source)
    assert inspected.exit_code == 0
    assert "Processing time (P/T): 1 min" in inspected.stdout
    assert "Setup time (S/T): 0 min" in inspected.stdout
    assert "Cycle time:" not in inspected.stdout
    assert "Changeover time:" not in inspected.stdout
    assert process == before


def test_supplied_evidence_does_not_hide_a_modeled_path_range():
    from flo.render._process_header import process_evidence_rows

    data = model()
    first = deepcopy(data["steps"][1])
    second = deepcopy(data["steps"][2])
    for step, seconds in ((first, 2), (second, 10)):
        step["cycle_time"]["results"]["mean"]["value"] = seconds
        step["wait_time"]["results"]["mean"]["value"] = 0
        step["changeover_time"]["results"]["mean"]["value"] = 0
    data["steps"] = [
        data["steps"][0],
        {"id": "choose", "kind": "decision"},
        first,
        second,
        data["steps"][-1],
    ]
    data["transitions"] = [
        {"source": "start", "target": "choose"},
        {"source": "choose", "target": "work", "outcome": "short"},
        {"source": "choose", "target": "finish", "outcome": "long"},
        {"source": "work", "target": "end"},
        {"source": "finish", "target": "end"},
    ]
    process = compile_adapter(parse_adapter(yaml.safe_dump(data)))
    validate_ir(process)
    rows = dict(process_evidence_rows(process))
    assert rows["Supplied lead time (observed)"] == "30 min"
    assert rows["Modeled lead time range"] == "2 to 10 min"
