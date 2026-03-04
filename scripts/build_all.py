"""Build render artifacts for all FLO examples.

Scans `examples/` recursively for `.flo` files, compiles each file through
FLO's parser/compiler/validator pipeline, writes DOT into `renders/` using the
same relative path, and (when Graphviz `dot` is available) also writes SVG.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import shutil
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def _iter_example_files(examples_dir: Path, include_invalid: bool) -> list[Path]:
    files = sorted(path for path in examples_dir.rglob("*.flo") if path.is_file())
    if include_invalid:
        return files
    return [
        path
        for path in files
        if "conformance/invalid" not in path.relative_to(examples_dir).as_posix()
    ]


def _build_one(example_file: Path, examples_dir: Path, renders_dir: Path) -> tuple[bool, str]:
    from flo.adapters import parse_adapter
    from flo.compiler import compile_adapter
    from flo.compiler.ir import ensure_schema_aligned, validate_ir
    from flo.render import render_dot

    rel = example_file.relative_to(examples_dir)
    base_out = (renders_dir / rel).with_suffix("")
    dot_out = base_out.with_suffix(".dot")
    svg_out = base_out.with_suffix(".svg")

    dot_out.parent.mkdir(parents=True, exist_ok=True)

    try:
        content = example_file.read_text(encoding="utf-8")
        adapter = parse_adapter(content)
        ir = compile_adapter(adapter)
        validate_ir(ir)
        ensure_schema_aligned(ir)
        render_options = _render_options_for_example(example_file)
        dot = render_dot(ir, options=render_options)
        dot_out.write_text(dot, encoding="utf-8")

        has_dot = shutil.which("dot") is not None
        if has_dot:
            subprocess.run(["dot", "-Tsvg", str(dot_out), "-o", str(svg_out)], check=True)
            return True, f"OK {rel} -> {dot_out.relative_to(REPO_ROOT)}, {svg_out.relative_to(REPO_ROOT)}"

        return True, f"OK {rel} -> {dot_out.relative_to(REPO_ROOT)} (svg skipped: dot not found)"
    except Exception as exc:
        return False, f"FAIL {rel}: {exc}"


def main() -> int:
    """Build DOT/SVG artifacts for example FLO files under `examples/`."""
    parser = argparse.ArgumentParser(prog="build_all.py")
    parser.add_argument(
        "--include-invalid",
        action="store_true",
        help="Include intentionally invalid conformance fixtures.",
    )
    args = parser.parse_args()

    examples_dir = REPO_ROOT / "examples"
    renders_dir = REPO_ROOT / "renders"

    if not examples_dir.exists():
        print(f"examples directory not found: {examples_dir}")
        return 2

    renders_dir.mkdir(parents=True, exist_ok=True)
    files = _iter_example_files(examples_dir, include_invalid=bool(args.include_invalid))

    if not files:
        print("No .flo files found under examples/")
        return 0

    failures = 0
    for example_file in files:
        ok, message = _build_one(example_file, examples_dir, renders_dir)
        print(message)
        if not ok:
            failures += 1

    if failures:
        print(f"Completed with {failures} failure(s).")
        return 1

    print(f"Completed successfully for {len(files)} file(s).")
    return 0


def _render_options_for_example(example_file: Path) -> dict[str, str]:
    name = example_file.stem.lower()
    if name == "swimlane":
        return {"diagram": "swimlane"}
    return {}


if __name__ == "__main__":
    raise SystemExit(main())
