"""Validate compiled IR for each example against the JSON schema.

Run this script from the repository root. It requires `jsonschema` to be
installed in the environment (CI will install it).
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flo.adapters import parse_adapter
from flo.compiler import compile_adapter
from flo.ir.validate import validate_against_schema


def main() -> int:
    """Compile example files and validate the resulting IRs against schema.

    Returns a non-zero exit code when validation fails.
    """
    repo_root = Path(__file__).resolve().parents[1]
    examples = sorted((repo_root / "examples").glob("*.flo"))
    if not examples:
        print("No example files found, skipping schema validation")
        return 0

    ok = True
    for ex in examples:
        print(f"Validating {ex}")
        content = ex.read_text()
        adapter = parse_adapter(content)
        ir = compile_adapter(adapter)
        try:
            validate_against_schema(ir)
            print("  OK")
        except Exception as e:
            ok = False
            print(f"  FAILED: {e}")

    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
