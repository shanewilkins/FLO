"""Policy test: ensure only approved top-level directories exist in the repo.

This test fails if new top-level directories are added that are not in the
`ALLOWED_TOP_LEVEL_DIRS` set. It helps catch accidental vendoring or stray
folders that don't belong in the repository root.
"""
from __future__ import annotations

from pathlib import Path


ALLOWED_TOP_LEVEL_DIRS = {
    "src",
    "tests",
    "docs",
    "examples",
    "schema",
    "scripts",
    ".github",
}


def _find_repo_root() -> Path:
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return Path.cwd()


def test_no_unapproved_top_level_dirs():
    root = _find_repo_root()
    unexpected = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        name = entry.name
        if name in ALLOWED_TOP_LEVEL_DIRS:
            continue
        # allow dotfiles and common files (handled elsewhere)
        if name.startswith("."):
            continue
        # allow virtualenv folder if present but not recommended
        if name in {"venv", ".venv"}:
            continue
        unexpected.append(name)

    assert not unexpected, f"Unexpected top-level directories: {unexpected}"
