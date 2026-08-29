#!/usr/bin/env python3
"""Check deterministic baseline SVG accessibility metadata."""

from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO_ROOT / "tests" / "golden" / "sppm"
SVG_NAMESPACE = "http://www.w3.org/2000/svg"


def accessibility_violations(path: Path) -> tuple[str, ...]:
    """Return accessible-name violations for one standalone SVG."""
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        return (f"cannot parse SVG: {exc}",)

    violations: list[str] = []
    if root.tag != f"{{{SVG_NAMESPACE}}}svg":
        violations.append("root element must be SVG")
    if root.get("role") != "img":
        violations.append("root SVG must declare role=img")

    labelled_by = root.get("aria-labelledby", "").split()
    if labelled_by != ["flo-svg-title", "flo-svg-description"]:
        violations.append("root SVG must reference deterministic title and description ids")

    expected = {
        "flo-svg-title": f"{{{SVG_NAMESPACE}}}title",
        "flo-svg-description": f"{{{SVG_NAMESPACE}}}desc",
    }
    id_index = {element.get("id"): element for element in root.iter() if element.get("id")}
    for element_id, tag in expected.items():
        element = id_index.get(element_id)
        if element is None or element.tag != tag:
            violations.append(f"missing {tag.rsplit('}', 1)[-1]}#{element_id}")
        elif not "".join(element.itertext()).strip():
            violations.append(f"{element_id} must contain text")

    duplicate_ids = _duplicate_ids(root)
    if duplicate_ids:
        violations.append(f"duplicate SVG ids: {', '.join(duplicate_ids)}")
    return tuple(violations)


def _duplicate_ids(root: ET.Element) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for element in root.iter():
        element_id = element.get("id")
        if not element_id:
            continue
        if element_id in seen:
            duplicates.add(element_id)
        seen.add(element_id)
    return tuple(sorted(duplicates))


def main() -> int:
    """Validate selected SVGs, or every committed SPPM golden SVG."""
    parser = argparse.ArgumentParser(prog="check_svg_accessibility.py")
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = [path.resolve() for path in args.paths]
    if not paths:
        paths = sorted(DEFAULT_ROOT.glob("*/render.svg"))

    failures: list[str] = []
    for path in paths:
        for violation in accessibility_violations(path):
            failures.append(f"{path}: {violation}")
    if failures:
        for failure in failures:
            print(f"FAIL  {failure}")
        return 1
    print(f"SVG accessibility check passed for {len(paths)} artifact(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
