"""Policy tests for import-linter contract governance."""

from __future__ import annotations

from pathlib import Path
import tomllib


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
        assert contract.get("type") == "forbidden", (
            f"contract #{idx + 1} currently must use type='forbidden'"
        )
        source_modules = contract.get("source_modules")
        forbidden_modules = contract.get("forbidden_modules")
        assert isinstance(source_modules, list) and source_modules, (
            f"contract #{idx + 1} requires non-empty source_modules"
        )
        assert isinstance(forbidden_modules, list) and forbidden_modules, (
            f"contract #{idx + 1} requires non-empty forbidden_modules"
        )
