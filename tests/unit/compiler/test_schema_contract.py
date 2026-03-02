from flo.compiler.compile import compile_adapter
from flo.compiler.ir.validate import validate_against_schema
from flo.compiler.ir.models import IR, Node
from flo.services.errors import ValidationError


def test_compile_emits_schema_and_validates() -> None:
    adapter = {
        "name": "test_process",
        "nodes": [
            {"id": "n1", "kind": "task", "attrs": {"name": "Step 1"}},
            {"id": "n2", "kind": "task", "attrs": {"name": "Step 2"}},
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
