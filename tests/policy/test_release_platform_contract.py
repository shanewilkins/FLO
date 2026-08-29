"""Keep the smallest declared platform and SVG-consumer matrix in CI."""

from pathlib import Path


def test_ci_has_macos_wheel_smoke_and_headless_chrome_svg_consumer() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "macos-package-smoke:" in workflow
    assert "runs-on: macos-latest" in workflow
    assert "browser-actions/setup-chrome@" in workflow
    assert "scripts/check_svg_accessibility.py" in workflow
    assert "--headless" in workflow
