import json
from pathlib import Path

from flo.compiler.compile import compile_adapter
from flo.compiler.ir.validate import validate_against_schema
from flo.compiler.ir.models import IR, Node, Edge
from flo.services.errors import ValidationError


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
    packaged_schema_path = repo_root / "src" / "flo" / "schema" / "flo_ir.json"

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
