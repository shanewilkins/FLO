"""Policy test: ensure `src/flo/` only contains approved subpackages.

This test fails if unexpected directories appear directly under
`src/flo/`. The approved physical directories correspond to our
conceptual layers (compiler may include `ir/` and `analysis/`).
"""
from __future__ import annotations

from pathlib import Path


APPROVED_SUBDIRS = {
    "adapters",
    "analysis",
    "compiler",
    "ir",
    "render",
    "services",
}


def _find_repo_root() -> Path:
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return Path.cwd()


def test_src_flo_only_has_approved_subdirs():
    root = _find_repo_root()
    src_flo = root / "src" / "flo"
    assert src_flo.exists(), "src/flo directory not found"

    unexpected = []
    for entry in sorted(src_flo.iterdir()):
        if not entry.is_dir():
            continue
        name = entry.name
        if name == "__pycache__":
            continue
        if name not in APPROVED_SUBDIRS:
            unexpected.append(name)

    assert not unexpected, f"Unexpected directories under src/flo: {unexpected}"
