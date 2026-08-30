"""Keep the smallest declared platform and SVG-consumer matrix in CI."""

from pathlib import Path


def _job_section(workflow: str, job: str, next_job: str) -> str:
    return workflow.split(f"  {job}:", 1)[1].split(f"  {next_job}:", 1)[0]


def test_ci_has_macos_wheel_smoke_and_headless_chrome_svg_consumer() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "macos-package-smoke:" in workflow
    assert "runs-on: macos-latest" in workflow
    assert "browser-actions/setup-chrome@" in workflow
    assert "scripts/check_svg_accessibility.py" in workflow
    assert "--headless" in workflow


def test_wheel_smoke_jobs_vendor_elk_before_building() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    sections = (
        _job_section(workflow, "package-smoke", "macos-package-smoke"),
        _job_section(workflow, "macos-package-smoke", "sppm-determinism"),
    )

    for section in sections:
        npm_index = section.index("npm ci --ignore-scripts --no-audit --no-fund")
        vendor_index = section.index("python scripts/vendor_elkjs.py")
        build_index = section.index("uv build --wheel")
        assert npm_index < vendor_index < build_index
