from flo.compiler.compile import compile_adapter
from flo.ir.validate import validate_against_schema
from flo.ir.models import IR, Node
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

    # Compiler should emit schema-aligned IR and validation should pass
    validate_against_schema(ir)


def test_malformed_ir_raises_validation_error() -> None:
    # Create an IR that is not schema-aligned (old minimal shape)
    ir = IR(name="bad", nodes=[Node(id="n1", type="task", attrs={"name": "x"})], schema_aligned=False)

    try:
        validate_against_schema(ir)
        raise AssertionError("Expected ValidationError for malformed IR")
    except ValidationError:
        # expected
        pass
