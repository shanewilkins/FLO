"""Publication font measurements must run on both supported consumer platforms."""

from pathlib import Path

import yaml


def test_both_platforms_measure_and_retain_browser_metrics():
    workflow = yaml.safe_load(Path(".github/workflows/ci.yml").read_text())
    for name in ("macos-package-smoke", "test"):
        job = workflow["jobs"][name]
        assert any(
            "scripts/check_svg_browser.py" in step.get("run", "")
            for step in job["steps"]
        )
        assert any(
            "actions/upload-artifact@" in step.get("uses", "") for step in job["steps"]
        )
