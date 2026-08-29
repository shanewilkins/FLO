import json
from pathlib import Path

from flo.source.compile import compile_adapter
from flo.process.ir.schema_projection import ir_to_schema_dict
from flo.process.ir.validate import validate_against_schema
from flo.process.ir.models import IR, Node, Edge
from flo.errors import ValidationError


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
            Edge(source="split", target="join", handoff=True),
            Edge(source="join", target="end"),
        ],
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


def test_flo_types_schema_includes_phase2_canonical_keys() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    schema_path = repo_root / "schema" / "flo_types.json"

    with schema_path.open("r", encoding="utf-8") as fh:
        typed_schema = json.load(fh)

    process_props = typed_schema["properties"]["process"]["properties"]
    assert "items" in process_props
    assert "resources" in process_props
    assert "locations" in process_props

    handoff_type = typed_schema["definitions"]["handoff_type"]
    assert handoff_type["enum"] == [
        "responsibility",
        "information",
        "material",
        "system",
        "location",
        "mixed",
    ]


def test_canonical_entity_identity_and_kind_contracts_match_ir_schema() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    with (repo_root / "schema" / "flo_types.json").open(encoding="utf-8") as fh:
        typed = json.load(fh)["definitions"]
    with (repo_root / "schema" / "flo_ir.json").open(encoding="utf-8") as fh:
        ir_defs = json.load(fh)["definitions"]

    for entity_name in ("canonical_item", "canonical_resource"):
        assert ir_defs[entity_name]["required"] == typed[entity_name]["required"]
        typed_kind_ref = typed[entity_name]["properties"]["kind"]["$ref"]
        typed_kind_name = typed_kind_ref.rsplit("/", 1)[-1]
        assert (
            ir_defs[entity_name]["properties"]["kind"]["enum"]
            == typed[typed_kind_name]["enum"]
        )


def test_compile_preserves_first_class_process_context_and_hierarchy() -> None:
    adapter = {
        "spec_version": "0.1",
        "process": {
            "id": "context",
            "name": "Context",
            "version": 2,
            "owner": {"id": "owner", "name": "Process Owner"},
            "business_units": [
                {"id": "ops", "name": "Operations"},
            ],
        },
        "lanes": [
            {
                "id": "operations",
                "name": "Operations",
                "type": "team",
                "metadata": {"color_hint": "blue"},
            },
            {"id": "quality", "name": "Quality", "type": "team"},
        ],
        "steps": [
            {"id": "start", "kind": "start", "lane": "operations"},
            {
                "id": "work",
                "kind": "subprocess",
                "lane": "operations",
                "subnodes": [
                    {"id": "child", "kind": "task", "lane": "operations"},
                ],
            },
            {"id": "end", "kind": "end", "lane": "operations"},
        ],
        "transitions": [
            {"source": "start", "target": "work"},
            {"source": "work", "target": "child"},
            {"source": "child", "target": "end"},
        ],
    }

    projected = ir_to_schema_dict(compile_adapter(adapter))

    assert projected["process"]["owner"] == {
        "id": "owner",
        "name": "Process Owner",
    }
    assert projected["process"]["business_units"] == [
        {"id": "ops", "name": "Operations"}
    ]
    assert projected["lanes"] == [
        {
            "id": "operations",
            "name": "Operations",
            "type": "team",
            "metadata": {"color_hint": "blue"},
        },
        {"id": "quality", "name": "Quality", "type": "team"},
    ]
    child = next(node for node in projected["nodes"] if node["id"] == "child")
    assert child["subprocess_parent"] == "work"

    validate_against_schema(compile_adapter(adapter))
