from pathlib import Path

from flo.adapters import parse_adapter
from flo.compiler import compile_adapter
from flo.ir import validate_ir
from flo.render import render_dot


def _repo_root(start: Path | None = None) -> Path:
    start = start or Path(__file__).resolve()
    cur = start
    while cur != cur.parent:
        if (cur / "examples").is_dir():
            return cur
        cur = cur.parent
    raise RuntimeError("repo root with examples/ not found")


def test_compile_and_render_examples():
    examples = sorted((_repo_root() / "examples").glob("*.flo"))
    assert examples

    for ex in examples:
        content = ex.read_text()
        adapter = parse_adapter(content)
        ir = compile_adapter(adapter)
        # validate_ir raises on failure
        validate_ir(ir)
        dot = render_dot(ir)
        assert isinstance(dot, str)
