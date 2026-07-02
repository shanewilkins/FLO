"""Policy tests for renderer shared-core and renderer-specific boundaries."""

from __future__ import annotations

import ast
from pathlib import Path


def _find_repo_root() -> Path:
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return Path.cwd()


def _import_modules_for_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            # Keep relative import dots so local module intent remains visible.
            prefix = "." * node.level
            modules.append(f"{prefix}{node.module or ''}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)

    return modules


def test_backend_neutral_renderer_core_does_not_import_backend_modules() -> None:
    root = _find_repo_root()
    shared_files = [
        root / "src" / "flo" / "render" / "_publication.py",
    ]

    offenders: list[str] = []
    for file_path in shared_files:
        imports = _import_modules_for_file(file_path)
        backend_imports = [
            module
            for module in imports
            if any(marker in module for marker in ("_graphviz", "_sppm", "_svg"))
        ]
        if backend_imports:
            offenders.append(f"{file_path.name}: {', '.join(sorted(backend_imports))}")

    assert not offenders, "Backend-neutral renderer core imports backend modules: " + (
        "; ".join(offenders)
    )


def test_graphviz_renderer_modules_are_removed() -> None:
    root = _find_repo_root()
    offenders = sorted(
        path.relative_to(root).as_posix()
        for path in (root / "src" / "flo").rglob("*graphviz*.py")
    )

    assert not offenders, "Graphviz renderer/source modules remain: " + "; ".join(
        offenders
    )
