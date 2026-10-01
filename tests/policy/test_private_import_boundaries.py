"""Prevent private implementation modules from becoming cross-package APIs."""

from __future__ import annotations

import ast
from importlib.util import resolve_name
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _module_name(path: Path, *, source_root: Path) -> tuple[str, bool]:
    relative = path.relative_to(source_root).with_suffix("")
    parts = relative.parts
    is_package = parts[-1] == "__init__"
    if is_package:
        parts = parts[:-1]
    return ".".join(parts), is_package


def _resolved_imports(
    *, tree: ast.AST, importer: str, importer_is_package: bool
) -> list[tuple[str, int]]:
    imports: list[tuple[str, int]] = []
    importer_package = importer if importer_is_package else importer.rpartition(".")[0]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((alias.name, node.lineno) for alias in node.names)
            continue
        if not isinstance(node, ast.ImportFrom):
            continue

        module = node.module or ""
        if node.level:
            module = resolve_name(f"{'.' * node.level}{module}", importer_package)
        for alias in node.names:
            target = module
            if alias.name.startswith("_"):
                target = f"{module}.{alias.name}" if module else alias.name
            imports.append((target, node.lineno))
    return imports


def _is_cross_package_private_import(*, importer: str, imported: str) -> bool:
    importer_parts = importer.split(".")
    imported_parts = imported.split(".")
    if len(importer_parts) < 2 or len(imported_parts) < 3:
        return False
    if imported_parts[0] != "flo" or importer_parts[0] != "flo":
        return False
    if importer_parts[1] == imported_parts[1]:
        return False
    return any(part.startswith("_") for part in imported_parts[2:])


def test_flo_packages_do_not_import_other_packages_private_modules() -> None:
    source_root = _repo_root() / "src"
    offenders: list[str] = []

    for path in sorted((source_root / "flo").rglob("*.py")):
        importer, importer_is_package = _module_name(path, source_root=source_root)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for imported, line in _resolved_imports(
            tree=tree,
            importer=importer,
            importer_is_package=importer_is_package,
        ):
            if _is_cross_package_private_import(importer=importer, imported=imported):
                offenders.append(f"{importer}:{line} -> {imported}")

    assert not offenders, "Cross-package private imports are forbidden: " + "; ".join(
        offenders
    )
