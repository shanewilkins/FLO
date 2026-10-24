"""Policy tests for renderer shared-core and renderer-specific boundaries."""

from __future__ import annotations

import ast
from importlib.util import resolve_name
from pathlib import Path


def _find_repo_root() -> Path:
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return Path.cwd()


def test_all_neutral_modules_have_a_dependency_contract() -> None:
    """New modules must receive an explicit neutral or dispatch classification."""
    import tomllib

    root = _find_repo_root()
    config = tomllib.loads((root / "pyproject.toml").read_text())
    contract = next(
        item
        for item in config["tool"]["importlinter"]["contracts"]
        if item["name"].startswith("Neutral render infrastructure")
    )
    neutral = set(contract["source_modules"])
    dispatch = {"flo.render.registry", "flo.render.capability_matrix"}
    render = root / "src/flo/render"
    modules = {
        f"flo.render.{path.stem}"
        for path in render.glob("*.py")
        if path.stem != "__init__"
    }
    packages = {
        f"flo.render.{path.name}"
        for path in render.iterdir()
        if path.is_dir() and (path / "__init__.py").exists()
    }
    diagrams = {
        f"flo.render.{name}"
        for name in ("sppm", "swimlane", "spaghetti", "value_stream")
    }
    assert modules | packages == neutral | dispatch | diagrams
    assert set(contract["forbidden_modules"]) == dispatch | diagrams
    assert not neutral & (dispatch | diagrams)


def _import_targets(node: ast.AST, package: str) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom):
        target = node.module or ""
        if node.level:
            target = resolve_name("." * node.level + target, package)
        return [f"{target}.{alias.name}" for alias in node.names]
    return []


def test_neutral_modules_cannot_import_the_render_facade() -> None:
    """Prevent reaching dispatch indirectly through the ancestor package facade."""
    import tomllib

    root = _find_repo_root()
    config = tomllib.loads((root / "pyproject.toml").read_text())
    contract = next(
        item
        for item in config["tool"]["importlinter"]["contracts"]
        if item["name"].startswith("Neutral render infrastructure")
    )
    offenders = []
    for module in contract["source_modules"]:
        location = root / "src" / module.replace(".", "/")
        paths = (
            location.rglob("*.py")
            if location.is_dir()
            else [location.with_suffix(".py")]
        )
        for path in paths:
            importer = ".".join(path.relative_to(root / "src").with_suffix("").parts)
            package = importer.rpartition(".")[0]
            for node in ast.walk(ast.parse(path.read_text())):
                targets = _import_targets(node, package)
                if any(
                    target
                    in {
                        "flo.render",
                        "flo.render.render_artifact",
                        "flo.render.render_artifact_and_contract",
                        "flo.render.render_execution",
                        "flo.render.*",
                    }
                    for target in targets
                ):
                    offenders.append(f"{path.relative_to(root)}:{node.lineno}")
    assert not offenders, "Neutral code imports render dispatch facade: " + ", ".join(
        offenders
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
