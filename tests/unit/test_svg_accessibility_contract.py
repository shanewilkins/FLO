from __future__ import annotations

import importlib.util
from pathlib import Path

_SCRIPT = Path("scripts/check_svg_accessibility.py")
_SPEC = importlib.util.spec_from_file_location("check_svg_accessibility", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def test_accessibility_checker_accepts_named_svg(tmp_path: Path) -> None:
    svg = tmp_path / "named.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-labelledby="flo-svg-title flo-svg-description">'
        '<title id="flo-svg-title">Process</title>'
        '<desc id="flo-svg-description">Process diagram</desc>'
        "</svg>",
        encoding="utf-8",
    )

    assert _MODULE.accessibility_violations(svg) == ()


def test_accessibility_checker_rejects_unnamed_svg(tmp_path: Path) -> None:
    svg = tmp_path / "unnamed.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
        encoding="utf-8",
    )

    assert _MODULE.accessibility_violations(svg) == (
        "root SVG must declare role=img",
        "root SVG must reference deterministic title and description ids",
        "missing title#flo-svg-title",
        "missing desc#flo-svg-description",
    )
