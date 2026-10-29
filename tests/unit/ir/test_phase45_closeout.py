"""Compatibility removal, canonical round trips and boundary ownership gates."""

import ast
import json
from copy import deepcopy
from dataclasses import asdict, fields
from pathlib import Path

import pytest
import yaml

from flo import api
from flo.errors import ValidationError
from flo.process.ir._internal_shape import ir_from_internal_dict, ir_to_internal_json
from flo.process.ir.models import IR, Edge, Node
from flo.process.ir.schema_projection import ir_to_schema_dict
from flo.process.ir.validate import validate_against_schema, validate_ir
from flo.render.layout_core.elk_support import extract_nodes_and_edges
from flo.source import compile_adapter
from flo.source.models import SourceShapeError, SourceStep


def document():
    return {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process"},
        "steps": [{"id": "start", "kind": "start"}, {"id": "end", "kind": "end"}],
    }


@pytest.mark.parametrize("alias", ["attrs", "subnodes", "edges", "from", "to"])
@pytest.mark.parametrize("included", [False, True], ids=["root", "fragment"])
def test_retired_source_keys_fail_without_parser_or_include_translation(
    tmp_path, alias, included
):
    data = document()
    if alias == "edges":
        data[alias] = [{"source": "start", "target": "end"}]
    elif alias in {"from", "to"}:
        data["transitions"] = [{"source": "start", "target": "end", alias: "start"}]
    else:
        data["steps"][0][alias] = {} if alias == "attrs" else []
    before = deepcopy(data)
    if included:
        fragment = tmp_path / "fragment.flo"
        fragment.write_text(yaml.safe_dump(data))
        source = "spec_version: '0.1'\nincludes: [fragment.flo]\n"
    else:
        source = yaml.safe_dump(data)
    result = api.validate(source, source_path=str(tmp_path / "root.flo"))
    assert not result.ok
    assert any(alias in (issue.field_path or "") for issue in result.diagnostics)
    assert result.diagnostics[0].source == str(
        tmp_path / ("fragment.flo" if included else "root.flo")
    )
    if included:
        assert result.diagnostics[0].include_chain
    with pytest.raises(SourceShapeError):
        compile_adapter(data)
    assert data == before


def test_retired_named_target_alias_is_rejected():
    data = document()
    data["steps"][0] = {
        "id": "choice",
        "kind": "decision",
        "outcomes": {"yes": {"to": "end"}, "no": "end"},
    }
    result = api.validate(yaml.safe_dump(data))
    assert not result.ok
    assert result.diagnostics[0].field_path.startswith("steps[0].outcomes.yes")


def test_source_and_dataclass_node_have_no_attrs_surface():
    assert "attrs" not in SourceStep.model_fields
    assert "attrs" not in {entry.name for entry in fields(Node)}


def test_every_internal_field_roundtrips_and_render_projection_retains_relation_context():
    profile = {
        "basis": "observed",
        "primary": "mean",
        "analysis_input": "mean",
        "results": {"mean": {"method": "mean", "value": 0, "unit": "min"}},
    }
    node_values = {
        "id": "work",
        "type": "task",
        "branch": None,
        "subprocess_parent": "parent",
        "name": "Work",
        "description": "Evidence",
        "lane": "ops",
        "location": "desk",
        "consumes": ["input"],
        "produces": ["output"],
        "performed_by": ["person"],
        "uses": ["tool"],
        "value_class": "unknown",
        "cycle_time": profile,
        "wait_time": profile,
        "changeover_time": profile,
        "extensions": {"example:annotation": [0, False]},
    }
    edge_values = {
        "source": "branch",
        "target": "work",
        "id": "transition",
        "outcome": "yes",
        "route": "chosen",
        "label": "Work",
        "handoff": {"type": "responsibility"},
        "rework": {"reason": "Correction"},
        "extensions": {"flo:continuation": {"outgoing": "A"}},
    }
    ir_values = {
        "name": "p",
        "nodes": [
            Node(**node_values),
            Node(id="branch", type="branch", branch={"mode": "dispatch"}),
        ],
        "edges": [Edge(**edge_values)],
        "process_metadata": {"process_id": "p", "process_name": "Process"},
        "process_version": 3,
        "process_owner": {"id": "ops", "name": "Operations"},
        "business_units": [{"id": "ops", "name": "Operations"}],
        "lanes": [{"id": "ops", "name": "Operations"}],
        "items": [{"id": "input", "name": "Input", "kind": "information"}],
        "resources": [{"id": "person", "name": "Person", "kind": "person"}],
        "locations": [
            {"id": "desk", "name": "Desk", "spatial": {"x": 0, "y": 0, "unit": "m"}}
        ],
        "render_intent": {"defaults": {"diagram": "sppm"}},
        "lead_time": profile,
        "extensions": {"example:process": True},
    }
    assert set(node_values) == {entry.name for entry in fields(Node)}
    assert set(edge_values) == {entry.name for entry in fields(Edge)}
    assert set(ir_values) == {entry.name for entry in fields(IR)}
    process = IR(**ir_values)
    before = deepcopy(process)
    restored = ir_from_internal_dict(json.loads(ir_to_internal_json(process)))
    assert asdict(restored) == asdict(process)
    projection = ir_to_schema_dict(process)
    nodes, edges = extract_nodes_and_edges(process)
    assert nodes == projection["nodes"]
    assert edges == projection["edges"]
    assert nodes[1]["branch"] == {"mode": "dispatch"}
    assert edges[0] == edge_values
    assert process == before


@pytest.mark.parametrize(
    "key,value",
    [
        ("process_owner", "bad"),
        ("business_units", False),
        ("lanes", False),
        ("process_version", True),
    ],
)
def test_invalid_first_class_context_survives_construction_and_is_not_hidden_by_projection(
    key, value
):
    process = IR(name="p", nodes=[Node(id="work", type="task")], **{key: value})
    assert getattr(process, key) is value
    with pytest.raises(ValidationError):
        validate_against_schema(process)


def test_retired_context_is_not_promoted_by_construction_or_restoration():
    process = IR(
        name="p",
        nodes=[Node(id="start", type="start"), Node(id="end", type="end")],
        edges=[Edge(source="start", target="end")],
        process_metadata={"render": {"defaults": {"diagram": "spaghetti"}}},
    )
    restored = ir_from_internal_dict(json.loads(ir_to_internal_json(process)))
    assert restored.render_intent is None
    assert restored.process_metadata == process.process_metadata
    with pytest.raises(ValidationError, match="E1201"):
        validate_ir(restored)


@pytest.mark.parametrize("retired", ["ingredients", "materials", "unsupported"])
def test_export_formats_do_not_fall_back_to_an_unrequested_payload(retired):
    result = api.export(yaml.safe_dump(document()), export_format=retired)
    assert not result.ok
    assert result.value is None
    assert "unsupported export format" in result.diagnostics[0].message


def test_pydantic_imports_are_confined_to_explicit_boundaries():
    allowed = {
        "app/_option_validation.py",
        "app/_flo_config.py",
        "process/contracts.py",
        "process/contract_validation.py",
        "process/ir/_boundary_validation.py",
        "source/models.py",
        "render/options.py",
    }
    actual = set()
    root = Path("src/flo")
    for path in root.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            imports = (
                [node.module]
                if isinstance(node, ast.ImportFrom)
                else [entry.name for entry in node.names]
                if isinstance(node, ast.Import)
                else []
            )
            if any(
                name and name.split(".")[0] in {"pydantic", "pydantic_core"}
                for name in imports
            ):
                actual.add(path.relative_to(root).as_posix())
    assert actual == allowed
