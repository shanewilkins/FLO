#!/usr/bin/env python3
"""Simple import checker enforcing architectural layer rules.

This is a lightweight alternative to import-linter when exact config
formats are not available. It scans `src/flo` and fails if forbidden
imports are found according to rules defined below.
"""
import ast
import pathlib
import sys
from typing import Dict, Iterable, List


BASE = pathlib.Path(__file__).resolve().parents[1] / "src"


def iter_py_files(package_dir: pathlib.Path) -> Iterable[pathlib.Path]:
    for p in package_dir.rglob("*.py"):
        yield p


def module_name_from_path(p: pathlib.Path, src_root: pathlib.Path) -> str:
    # src/flo/ir/models.py -> flo.ir.models
    rel = p.relative_to(src_root)
    parts = rel.with_suffix("").parts
    return ".".join(parts)


RULES: Dict[str, List[str]] = {
    # module prefix -> list of forbidden import prefixes
    "flo.compiler": ["flo.main", "flo.services.logging"],
    "flo.adapters": ["flo.main", "flo.services.logging"],
    "flo.ir": ["flo.compiler", "flo.main", "flo.adapters", "flo.analysis", "flo.render"],
    "flo.render": ["flo.main", "flo.services.logging"],
    # Note: generic 'flo' catch-all rule removed to allow CLI module
    # (`flo.cli`) to import the programmatic entrypoints in `flo.main`.
}


def check_file(p: pathlib.Path, src_root: pathlib.Path) -> List[str]:
    mod = module_name_from_path(p, src_root)
    src = p.read_text()
    tree = ast.parse(src)
    errors: List[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imp = n.name
                errors.extend(check_forbidden(mod, imp, p))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imp = node.module
                errors.extend(check_forbidden(mod, imp, p))
    return errors


def check_forbidden(module: str, imported: str, path: pathlib.Path) -> List[str]:
    errs: List[str] = []
    for prefix, forbidden_list in RULES.items():
        if module == prefix or module.startswith(prefix + ".") or (prefix == "flo" and module.startswith("flo.") and module != "flo.main"):
            for forbidden in forbidden_list:
                if imported == forbidden or imported.startswith(forbidden + "."):
                    errs.append(f"{path}: module '{module}' imports forbidden '{imported}' (rule for '{prefix}')")
    return errs


def main() -> int:
    src_root = BASE
    pkg_dir = src_root / "flo"
    all_errors: List[str] = []
    for p in iter_py_files(pkg_dir):
        errs = check_file(p, src_root)
        all_errors.extend(errs)

    if all_errors:
        print("Import rules violations detected:")
        for e in all_errors:
            print(e)
        return 2
    print("Import check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

