#!/usr/bin/env python3
"""Copy the pinned elkjs runtime and license into FLO's package tree."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "node_modules" / "elkjs"
VENDOR_ROOT = REPO_ROOT / "src" / "flo" / "render" / "layout_core" / "vendor"


def _pinned_version() -> str:
    lock_data = json.loads(
        (REPO_ROOT / "package-lock.json").read_text(encoding="utf-8")
    )
    package = lock_data.get("packages", {}).get("node_modules/elkjs", {})
    version = str(package.get("version") or "")
    if not version:
        raise RuntimeError("package-lock.json does not pin node_modules/elkjs")
    return version


def main() -> int:
    """Vendor the exact locked elkjs runtime into the Python package."""
    locked_version = _pinned_version()
    package_data = json.loads(
        (PACKAGE_ROOT / "package.json").read_text(encoding="utf-8")
    )
    installed_version = str(package_data.get("version") or "")
    if installed_version != locked_version:
        raise RuntimeError(
            "Installed elkjs does not match package-lock.json: "
            f"installed={installed_version or 'missing'}, locked={locked_version}. "
            "Run npm ci before vendoring."
        )

    source_bundle = PACKAGE_ROOT / "lib" / "elk.bundled.js"
    source_license = PACKAGE_ROOT / "LICENSE.md"
    if not source_bundle.is_file() or not source_license.is_file():
        raise RuntimeError("elkjs bundle or license is missing; run npm ci")

    VENDOR_ROOT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_bundle, VENDOR_ROOT / "elk.bundled.js")
    shutil.copyfile(source_license, VENDOR_ROOT / "ELKJS_LICENSE.md")
    print(f"Vendored elkjs {locked_version} into {VENDOR_ROOT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
