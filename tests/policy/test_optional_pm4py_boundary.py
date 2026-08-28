"""Keep PM4Py optional and quarantined behind one FLO bridge module."""

from __future__ import annotations

import ast
from pathlib import Path
import tomllib


_ALLOWED_IMPORTER = "flo.pm4py_bridge"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _module_name(path: Path, *, source_root: Path) -> str:
    relative = path.relative_to(source_root).with_suffix("")
    parts = relative.parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _imports_pm4py(tree: ast.AST) -> list[int]:
    lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            lines.extend(
                node.lineno
                for alias in node.names
                if alias.name == "pm4py" or alias.name.startswith("pm4py.")
            )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "pm4py" or module.startswith("pm4py."):
                lines.append(node.lineno)
    return lines


def test_only_bridge_module_may_import_pm4py() -> None:
    source_root = _repo_root() / "src"
    offenders: list[str] = []

    for path in sorted((source_root / "flo").rglob("*.py")):
        importer = _module_name(path, source_root=source_root)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if importer != _ALLOWED_IMPORTER:
            offenders.extend(f"{importer}:{line}" for line in _imports_pm4py(tree))

    assert not offenders, (
        "PM4Py imports are allowed only in flo.pm4py_bridge: " + "; ".join(offenders)
    )


def test_pm4py_is_not_a_core_runtime_dependency() -> None:
    pyproject = tomllib.loads(
        (_repo_root() / "pyproject.toml").read_text(encoding="utf-8")
    )
    dependencies = pyproject["project"].get("dependencies", [])

    assert not any(
        str(item).strip().lower().startswith("pm4py") for item in dependencies
    )
