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
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def _iter_example_files(examples_dir: Path, include_invalid: bool) -> list[Path]:
    files = sorted(path for path in examples_dir.rglob("*.flo") if path.is_file())
    included_files = _collect_included_files(files)
    files = [path for path in files if path.resolve() not in included_files]

    if include_invalid:
        return files
    return [
        path
        for path in files
        if "conformance/invalid" not in path.relative_to(examples_dir).as_posix()
    ]


def _collect_included_files(files: list[Path]) -> set[Path]:
    file_set = {path.resolve() for path in files}
    included: set[Path] = set()

    for path in files:
        include_refs = _include_refs_from_file(path)
        for include_ref in include_refs:
            include_path = _resolve_include_ref(current_path=path, include_ref=include_ref)
            if include_path in file_set:
                included.add(include_path)

    return included


def _include_refs_from_file(path: Path) -> list[str]:
    try:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return []

    if not isinstance(parsed, dict):
        return []
    return _extract_include_refs(parsed)


def _extract_include_refs(document: dict[str, object]) -> list[str]:
    include_value = document.get("includes")
    if include_value is None:
        include_value = document.get("include")

    if include_value is None:
        return []
    if isinstance(include_value, str):
        text = include_value.strip()
        return [text] if text else []
    if isinstance(include_value, list):
        return [entry.strip() for entry in include_value if isinstance(entry, str) and entry.strip()]
    return []


def _resolve_include_ref(current_path: Path, include_ref: str) -> Path:
    include_path = Path(include_ref)
    if include_path.is_absolute():
        return include_path.resolve()
    return (current_path.parent / include_path).resolve()


def _build_one(example_file: Path, examples_dir: Path, renders_dir: Path) -> tuple[bool, str]:
    from flo.adapters import parse_adapter
    from flo.compiler import compile_adapter
    from flo.compiler.ir import ensure_schema_aligned, validate_ir
    from flo.export import export_ir
    from flo.render import render_dot
    from flo.services.graphviz import render_dot_to_file

    rel = example_file.relative_to(examples_dir)
    base_out = (renders_dir / rel).with_suffix("")
    build_variants = [("", _render_options_for_example(example_file)), *_extra_render_variants_for_example(example_file)]

    base_out.parent.mkdir(parents=True, exist_ok=True)

    try:
        content = example_file.read_text(encoding="utf-8")
        adapter = parse_adapter(content, source_path=str(example_file))
        ir = compile_adapter(adapter)
        validate_ir(ir)
        ensure_schema_aligned(ir)
        has_dot = shutil.which("dot") is not None
        created: list[str] = []

        for suffix, render_options in build_variants:
            dot_out = base_out.with_name(f"{base_out.name}{suffix}").with_suffix(".dot")
            svg_out = base_out.with_name(f"{base_out.name}{suffix}").with_suffix(".svg")

            dot = render_dot(ir, options=render_options)
            dot_out.write_text(dot, encoding="utf-8")
            created.append(str(dot_out.relative_to(REPO_ROOT)))

            if has_dot:
                render_dot_to_file(dot, str(svg_out))
                created.append(str(svg_out.relative_to(REPO_ROOT)))

        if _has_materials_or_equipment_collection(ir):
            ingredients_out = base_out.with_name(f"{base_out.name}_ingredients").with_suffix(".md")
            legacy_ingredients_out = base_out.with_name(f"{base_out.name}_ingredients").with_suffix(".txt")
            ingredients = export_ir(ir, options={"export": "ingredients"})
            if not ingredients.endswith("\n"):
                ingredients += "\n"
            ingredients_out.write_text(ingredients, encoding="utf-8")
            if legacy_ingredients_out.exists():
                legacy_ingredients_out.unlink()
            created.append(str(ingredients_out.relative_to(REPO_ROOT)))

        if has_dot:
            return True, f"OK {rel} -> {', '.join(created)}"

        return True, f"OK {rel} -> {', '.join(created)} (svg skipped: dot not found)"
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


def _extra_render_variants_for_example(example_file: Path) -> list[tuple[str, dict[str, str]]]:
    if example_file.stem.lower() == "chocolate_chip_cookies":
        return [
            ("_topdown", {"diagram": "flowchart", "orientation": "tb"}),
            ("_spaghetti", {"diagram": "spaghetti"}),
        ]
    if example_file.stem.lower() == "washnfold":
        return [
            ("_sppm", {"diagram": "sppm", "orientation": "lr"}),
            (
                "_sppm_wrap800",
                {
                    "diagram": "sppm",
                    "orientation": "lr",
                    "layout_wrap": "auto",
                    "layout_max_width_px": "800",
                },
            ),
        ]
    return []


def _has_materials_or_equipment_collection(ir: object) -> bool:
    process_metadata = getattr(ir, "process_metadata", None)
    if not isinstance(process_metadata, dict):
        return False
    return process_metadata.get("materials") is not None or process_metadata.get("equipment") is not None


if __name__ == "__main__":
    raise SystemExit(main())
