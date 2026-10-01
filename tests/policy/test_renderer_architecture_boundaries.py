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
        root / "src" / "flo" / "render" / "_artifact.py",
        root / "src" / "flo" / "render" / "_diagnostics.py",
        root / "src" / "flo" / "render" / "themes.py",
        root / "src" / "flo" / "render" / "shared" / "svg.py",
        root / "src" / "flo" / "render" / "layout_core" / "elk_contracts.py",
        root / "src" / "flo" / "render" / "layout_core" / "elk_errors.py",
        root / "src" / "flo" / "render" / "layout_core" / "models.py",
        root / "src" / "flo" / "render" / "layout_core" / "placement.py",
        root / "src" / "flo" / "render" / "layout_core" / "ports.py",
        root / "src" / "flo" / "render" / "layout_core" / "rework_geometry.py",
        root / "src" / "flo" / "render" / "layout_core" / "rework_semantics.py",
        root / "src" / "flo" / "render" / "layout_core" / "routing.py",
    ]

    offenders: list[str] = []
    for file_path in shared_files:
        assert file_path.exists(), f"Registered neutral module is missing: {file_path}"
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


def test_each_renderer_has_an_owned_package_entrypoint() -> None:
    root = _find_repo_root() / "src" / "flo" / "render"
    expected = {"sppm", "swimlane", "spaghetti", "value_stream"}

    assert {
        package
        for package in expected
        if (root / package / "__init__.py").exists()
        and (root / package / "renderer.py").exists()
    } == expected


def test_legacy_flat_renderer_modules_are_removed() -> None:
    root = _find_repo_root() / "src" / "flo" / "render"
    legacy_paths = [
        root / "_backend_selector.py",
        root / "_svg_shared_primitives.py",
        root / "_svg_sppm.py",
        root / "_svg_swimlane.py",
        root / "_svg_spaghetti.py",
        root / "_svg_value_stream.py",
    ]
    legacy_paths.extend(root.glob("_sppm_*.py"))
    legacy_paths.extend(root.glob("_svg_sppm_*.py"))

    assert not [path for path in legacy_paths if path.exists()]


def test_application_does_not_apply_global_renderer_preprocessing() -> None:
    root = _find_repo_root()
    app_source = (root / "src" / "flo" / "app" / "__init__.py").read_text(
        encoding="utf-8"
    )

    assert "scc_condense" not in app_source


def test_graphviz_renderer_modules_are_removed() -> None:
    root = _find_repo_root()
    offenders = sorted(
        path.relative_to(root).as_posix()
        for path in (root / "src" / "flo").rglob("*graphviz*.py")
    )

    assert not offenders, "Graphviz renderer/source modules remain: " + "; ".join(
        offenders
    )
