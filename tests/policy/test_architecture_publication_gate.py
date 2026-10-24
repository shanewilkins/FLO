"""Known architecture violations must block distribution publication."""

from pathlib import Path

import yaml


def test_publish_workflow_requires_architecture_check_before_artifact_upload():
    root = Path(__file__).resolve().parents[2]
    workflow = yaml.safe_load((root / ".github/workflows/publish.yml").read_text())
    build = workflow["jobs"]["build"]
    steps = build["steps"]
    gate_index = next(
        index
        for index, step in enumerate(steps)
        if "scripts/architecture_trace.py" in step.get("run", "")
    )
    smoke_index = next(
        index
        for index, step in enumerate(steps)
        if step.get("name") == "Smoke-test wheel install"
    )
    upload_index = next(
        index
        for index, step in enumerate(steps)
        if str(step.get("uses", "")).startswith("actions/upload-artifact@")
    )
    assert smoke_index < gate_index < upload_index
    gate = steps[gate_index]
    assert "--check" in gate["run"]
    assert "--installed-python" in gate["run"]
    assert not gate.get("continue-on-error", False)
    assert "||" not in gate["run"]
    assert workflow["jobs"]["publish"]["needs"] == "build"
