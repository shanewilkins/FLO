import json
from pathlib import Path
from typing import Any

from flo.errors import ValidationError
from flo.process.ir.models import IR, Edge, Node
from flo.process.ir.schema_projection import ir_to_schema_dict
from flo.process.ir.validate import validate_against_schema
from flo.source.compile import compile_adapter


def test_compile_emits_schema_and_validates() -> None:
    adapter = {
        "spec_version": "0.1",
        "process": {"id": "test_process", "name": "Test Process"},
        "steps": [
            {"id": "n1", "kind": "task", "name": "Step 1"},
            {"id": "n2", "kind": "task", "name": "Step 2"},
        ],
    }

    ir = compile_adapter(adapter)

    # Compiler output should validate via schema projection.
    validate_against_schema(ir)


def test_malformed_ir_raises_validation_error() -> None:
    # Use a node type not allowed by the JSON schema enum.
    ir = IR(name="bad", nodes=[Node(id="n1", type="process", attrs={"name": "x"})])

    try:
        validate_against_schema(ir)
        raise AssertionError("Expected ValidationError for malformed IR")
    except ValidationError:
        # expected
        pass


def test_schema_accepts_parallel_kinds_and_handoff_field() -> None:
    ir = IR(
        name="p",
        nodes=[
            Node(id="start", type="start", attrs={}),
            Node(id="split", type="parallel_split", attrs={}),
            Node(id="join", type="parallel_join", attrs={}),
            Node(id="end", type="end", attrs={}),
        ],
        edges=[
            Edge(source="start", target="split"),
            Edge(source="split", target="join", handoff={}),
            Edge(source="join", target="end"),
        ],
    )

    validate_against_schema(ir)


def test_schema_accepts_generic_branch_and_route() -> None:
    ir = IR(
        name="p",
        nodes=[
            Node(
                id="assign",
                type="branch",
                attrs={"branch": {"mode": "dispatch", "policy": "least_loaded"}},
            )
        ],
        edges=[Edge(source="assign", target="work", route="worker_a")],
    )

    validate_against_schema(ir)


def test_repo_and_packaged_ir_schema_are_in_sync() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    schema_path = repo_root / "schema" / "flo_ir.json"
    packaged_schema_path = (
        repo_root / "src" / "flo" / "process" / "schema" / "flo_ir.json"
    )

    with schema_path.open("r", encoding="utf-8") as fh:
        repo_schema = json.load(fh)
    with packaged_schema_path.open("r", encoding="utf-8") as fh:
        packaged_schema = json.load(fh)

    assert packaged_schema == repo_schema


def test_generated_source_schema_includes_first_class_semantic_keys() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    schema_path = repo_root / "schema" / "flo_source.json"

    with schema_path.open("r", encoding="utf-8") as fh:
        source_schema = json.load(fh)

    definitions = source_schema["$defs"]
    process_props = definitions["SourceProcess"]["properties"]
    assert "items" in process_props
    assert "resources" in process_props
    assert "locations" in process_props
    step_props = definitions["SourceStep"]["properties"]
    assert {"cycle_time", "wait_time", "changeover_time", "value_class"} <= set(
        step_props
    )
    assert "metadata" not in step_props


def test_generated_ir_schema_contains_structured_relations() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    with (repo_root / "schema" / "flo_ir.json").open(encoding="utf-8") as fh:
        ir_defs = json.load(fh)["$defs"]

    edge_props = ir_defs["CanonicalEdgeContract"]["properties"]
    assert edge_props["handoff"]["anyOf"][0]["$ref"].endswith("/HandoffRelation")
    assert edge_props["rework"]["anyOf"][0]["$ref"].endswith("/ReworkRelation")


def test_compile_preserves_first_class_process_context_and_hierarchy() -> None:
    adapter = {
        "spec_version": "0.1",
        "process": {
            "id": "context",
            "name": "Context",
            "version": 2,
            "owner": {"id": "owner", "name": "Process Owner"},
            "business_units": [{"id": "ops", "name": "Operations"}],
            "render": {"defaults": {"diagram": "sppm"}},
            "extensions": {"example:source_system": "erp"},
            "items": [{"id": "order", "name": "Order", "kind": "information"}],
            "resources": [{"id": "operator", "name": "Operator", "kind": "person"}],
            "locations": [{"id": "workcell", "name": "Workcell"}],
        },
        "lanes": [
            {
                "id": "operations",
                "name": "Operations",
                "type": "team",
                "extensions": {"example:color_hint": "blue"},
            },
            {"id": "quality", "name": "Quality", "type": "team"},
        ],
        "steps": [
            {"id": "start", "kind": "start", "lane": "operations"},
            {
                "id": "work",
                "kind": "subprocess",
                "lane": "operations",
                "subnodes": [{"id": "child", "kind": "task", "lane": "operations"}],
            },
            {"id": "end", "kind": "end", "lane": "operations"},
        ],
        "transitions": [
            {"source": "start", "target": "work"},
            {"source": "work", "target": "child"},
            {"source": "child", "target": "end"},
        ],
    }

    ir = compile_adapter(adapter)
    projected = ir_to_schema_dict(ir)

    _assert_projected_process_context(projected)
    _assert_explicit_ir_context(ir, adapter)
    _assert_projected_metadata(projected, adapter)
    validate_against_schema(ir)


def _assert_projected_process_context(projected: dict[str, Any]) -> None:
    process = projected["process"]
    assert isinstance(process, dict)

    assert process["owner"] == {
        "id": "owner",
        "name": "Process Owner",
    }
    assert process["business_units"] == [{"id": "ops", "name": "Operations"}]
    assert projected["lanes"] == [
        {
            "id": "operations",
            "name": "Operations",
            "type": "team",
            "extensions": {"example:color_hint": "blue"},
        },
        {"id": "quality", "name": "Quality", "type": "team"},
    ]
    child = next(node for node in projected["nodes"] if node["id"] == "child")
    assert child["subprocess_parent"] == "work"


def _assert_explicit_ir_context(ir: IR, adapter: dict[str, Any]) -> None:
    assert (
        next(node for node in ir.nodes if node.id == "child").subprocess_parent
        == "work"
    )
    assert ir.items == adapter["process"]["items"]
    assert ir.resources == adapter["process"]["resources"]
    assert ir.locations == adapter["process"]["locations"]
    assert ir.render_intent == {"defaults": {"diagram": "sppm"}}
    assert ir.extensions == {"example:source_system": "erp"}


def _assert_projected_metadata(
    projected: dict[str, Any], adapter: dict[str, Any]
) -> None:
    process = projected["process"]
    assert isinstance(process, dict)
    assert process["items"] == adapter["process"]["items"]
    assert process["resources"] == adapter["process"]["resources"]
    assert process["locations"] == adapter["process"]["locations"]
    assert process["render"] == {"defaults": {"diagram": "sppm"}}
    assert process["extensions"] == {"example:source_system": "erp"}
