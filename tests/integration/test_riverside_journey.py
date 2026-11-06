"""Riverside teaching exports preserve evidence and avoid false process totals."""

import importlib.util
import json
from pathlib import Path

import pytest
import yaml

import flo

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/reference/riverside"


def load_journey():
    spec = importlib.util.spec_from_file_location("riverside", EXAMPLE / "run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("state", ["current", "proposed"])
def test_riverside_evidence_and_timing_limits(state):
    path = EXAMPLE / f"{state}.flo"
    source = path.read_text()
    result = flo.validate(source, source_path=str(path))
    assert result.ok, result.report.as_dict()
    codes = {d.code for d in result.diagnostics}
    assert {"timing-incomplete", "timing-parallel-flow-unsupported"} <= codes
    timing = flo.inspect(source).value.timing
    assert timing.modeled_lead_time_seconds is None
    assert timing.minimum_path_lead_time_seconds is None
    assert timing.maximum_path_lead_time_seconds is None
    evidence = json.loads((EXAMPLE / "evidence.json").read_text())
    payload = json.loads(flo.export(source).value)
    for node in payload["nodes"]:
        for field in load_journey().FIELDS:
            if field not in node:
                continue
            profile = node[field]
            assert (
                profile["evidence_ref"]
                == f"evidence.json#/{state}/{node['id']}/{field}"
            )
            assert {
                k: v for k, v in profile.items() if k != "evidence_ref"
            } == evidence[state][node["id"]][field]
    nodes = {node["id"]: node for node in payload["nodes"]}
    assert "wait_time" not in nodes["clarify"]
    assert nodes["issue"]["wait_time"]["results"]["mean"]["value"] == 0
    rows = load_journey().evidence_rows(payload)
    assert ["clarify", "wait_time", "Unknown", "—", "Unknown", "—"] in rows
    issue_wait = next(row for row in rows if row[:2] == ["issue", "wait_time"])
    assert (
        issue_wait[2] == "mean: 0 min"
        if state == "current"
        else issue_wait[2] == "mean: 0.0 min"
    )
    if state == "proposed":
        assert issue_wait[4] == "Unknown (estimate)"


def test_riverside_report_contains_both_states_and_print_evidence(tmp_path):
    report = load_journey().build(tmp_path)
    content = report.read_text()
    assert "@page {size: A3 portrait" in content
    assert content.count("data:image/svg+xml;base64,") == 2
    assert content.count("<table>") == 2
    assert "End-to-end time: unavailable" in content
    assert "Unknown (estimate)" in content
    assert "evidence.json#/current/issue/wait_time" in content
    for state in ("current", "proposed"):
        assert "<svg" in (tmp_path / f"{state}.svg").read_text()
        inspection = json.loads((tmp_path / f"{state}-inspection.json").read_text())
        assert inspection["timing"]["modeled_lead_time_seconds"] is None


def test_riverside_notebook_code_runs_without_notebook_dependencies(
    tmp_path, monkeypatch
):
    # Execute the actual teaching cells; intercept only the output destination.
    notebook = json.loads((EXAMPLE / "riverside.ipynb").read_text())
    namespace = {}
    monkeypatch.chdir(ROOT)
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            code = "".join(cell["source"])
            code = code.replace(
                'ROOT / "renders/riverside"', f"Path({str(tmp_path)!r})"
            )
            exec(compile(code, "riverside.ipynb", "exec"), namespace)  # noqa: S102
    assert (tmp_path / "comparison.html").exists()


def test_selector_exercise_has_source_location_and_actionable_error():
    model = yaml.safe_load((EXAMPLE / "current.flo").read_text())
    model["steps"][1]["cycle_time"]["primary"] = "missing"
    result = flo.validate(
        yaml.safe_dump(model, sort_keys=False), source_path="exercise.flo"
    )
    assert not result.ok
    diagnostic = result.report.diagnostics[0]
    assert diagnostic.field_path == "steps[1].cycle_time"
    assert diagnostic.line is not None and diagnostic.excerpt
    assert "primary must reference a named result" in diagnostic.message
