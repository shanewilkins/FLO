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


def test_shared_renderer_core_does_not_import_sppm_modules() -> None:
    root = _find_repo_root()
    shared_files = [
        root / "src" / "flo" / "render" / "_continuation_labels.py",
        root / "src" / "flo" / "render" / "_graphviz_dot_edge_routing.py",
        root / "src" / "flo" / "render" / "_publication.py",
    ]

    offenders: list[str] = []
    for file_path in shared_files:
        imports = _import_modules_for_file(file_path)
        sppm_imports = [module for module in imports if "_sppm" in module]
        if sppm_imports:
            offenders.append(f"{file_path.name}: {', '.join(sorted(sppm_imports))}")

    assert not offenders, "Shared renderer core imports SPPM modules: " + "; ".join(offenders)


def test_shared_continuation_labels_are_consumed_by_sppm_and_non_sppm_paths() -> None:
    root = _find_repo_root()

    edge_routing_imports = _import_modules_for_file(
        root / "src" / "flo" / "render" / "_graphviz_dot_edge_routing.py"
    )
    sppm_continuation_imports = _import_modules_for_file(
        root / "src" / "flo" / "render" / "_sppm_continuation_labels.py"
    )

    assert "._continuation_labels" in edge_routing_imports
    assert "._continuation_labels" in sppm_continuation_imports
