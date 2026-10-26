"""Policy tests for import-linter contract governance."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
import yaml


def _find_repo_root() -> Path:
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return Path.cwd()


def test_importlinter_contracts_are_configured_and_nonempty() -> None:
    root = _find_repo_root()
    pyproject = root / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))

    tool = data.get("tool")
    assert isinstance(tool, dict), "pyproject.toml must define [tool] settings"

    importlinter = tool.get("importlinter")
    assert isinstance(importlinter, dict), (
        "pyproject.toml must define [tool.importlinter]"
    )

    root_package = importlinter.get("root_package")
    assert root_package == "flo", "import-linter root_package must be 'flo'"

    contracts = importlinter.get("contracts")
    assert isinstance(contracts, list) and contracts, (
        "import-linter must define at least one contract under "
        "[[tool.importlinter.contracts]]"
    )

    # Fail fast if someone reintroduces the non-functional legacy schema.
    assert "rules" not in importlinter, (
        "Use [[tool.importlinter.contracts]]; legacy [rules] schema is unsupported"
    )

    for idx, contract in enumerate(contracts):
        assert isinstance(contract, dict), f"contract #{idx + 1} must be a table"
        assert isinstance(contract.get("name"), str) and contract["name"].strip(), (
            f"contract #{idx + 1} requires a non-empty name"
        )
        contract_type = contract.get("type")
        assert contract_type in {"forbidden", "acyclic_siblings"}, (
            f"contract #{idx + 1} uses unsupported type {contract_type!r}"
        )
        if contract_type == "forbidden":
            source_modules = contract.get("source_modules")
            forbidden_modules = contract.get("forbidden_modules")
            assert isinstance(source_modules, list) and source_modules, (
                f"contract #{idx + 1} requires non-empty source_modules"
            )
            assert isinstance(forbidden_modules, list) and forbidden_modules, (
                f"contract #{idx + 1} requires non-empty forbidden_modules"
            )
        else:
            ancestors = contract.get("ancestors")
            assert isinstance(ancestors, list) and ancestors, (
                f"contract #{idx + 1} requires non-empty ancestors"
            )
            assert isinstance(contract.get("depth"), int), (
                f"contract #{idx + 1} requires an explicit cycle-check depth"
            )


def test_neutral_contract_has_no_dependency_bypasses() -> None:
    """Neutral boundaries cover indirect paths and carry no migration waivers."""
    config = tomllib.loads((_find_repo_root() / "pyproject.toml").read_text())
    contract = next(
        item
        for item in config["tool"]["importlinter"]["contracts"]
        if item["name"].startswith("Neutral render infrastructure")
    )
    assert not contract.get("allow_indirect_imports", False)
    assert not contract.get("ignore_imports", [])


def test_fast_architecture_checks_are_required_local_hooks() -> None:
    """Responsibility checks run before engine and installed-wheel acceptance."""
    config = yaml.safe_load((_find_repo_root() / ".pre-commit-config.yaml").read_text())
    hooks = {hook["id"]: hook for repo in config["repos"] for hook in repo["hooks"]}
    for hook_id, command in (
        ("importlinter-check", "uv run --locked lint-imports"),
        (
            "architecture-responsibility-check",
            "uv run --locked python scripts/architecture_boundaries.py",
        ),
    ):
        hook = hooks[hook_id]
        assert hook["entry"] == command
        assert not hook["pass_filenames"]
        assert "files" not in hook and "exclude" not in hook


@pytest.mark.parametrize(
    ("source", "passes"),
    [
        ("from .. import sppm as diagram", False),
        ("def run():\n    import flo.render.swimlane as diagram", False),
        ("from flo.render import registry", False),
        ("from .. import _text as text", True),
    ],
)
def test_neutral_import_contract_rejects_new_module_regressions(
    tmp_path, source, passes
):
    """Exercise the real configured contract on fresh modules, not just its schema."""
    config = tomllib.loads((_find_repo_root() / "pyproject.toml").read_text())
    contract = next(
        item
        for item in config["tool"]["importlinter"]["contracts"]
        if item["name"].startswith("Neutral render infrastructure")
    )
    packages = {
        "layout_core",
        "shared",
        "sppm",
        "swimlane",
        "spaghetti",
        "value_stream",
    }
    for module in contract["source_modules"] + contract["forbidden_modules"]:
        path = tmp_path / module.replace(".", "/")
        if path.name in packages:
            path = path / "__init__.py"
        else:
            path = path.with_suffix(".py")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
    (tmp_path / "flo/__init__.py").write_text("")
    (tmp_path / "flo/render/__init__.py").write_text("")
    (tmp_path / "flo/render/layout_core/new_module.py").write_text(source)
    text = (
        '[tool.importlinter]\nroot_package = "flo"\n[[tool.importlinter.contracts]]\n'
    )
    text += "\n".join(f"{key} = {json.dumps(value)}" for key, value in contract.items())
    (tmp_path / "pyproject.toml").write_text(text)
    result = subprocess.run(  # noqa: S603 - Installed tool with a generated test fixture.
        [str(Path(sys.executable).parent / "lint-imports")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert (result.returncode == 0) is passes, result.stdout + result.stderr
    assert ("KEPT" if passes else "BROKEN") in result.stdout
