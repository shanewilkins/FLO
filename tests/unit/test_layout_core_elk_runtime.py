import shutil
from types import SimpleNamespace
import subprocess

import pytest

from flo.render.layout_core import (
    ElkEngineProtocolError,
    ElkEngineSubprocessError,
    ElkEngineTimeoutError,
    ElkRuntimeUnavailableError,
    run_elkjs_layout,
)


def test_run_elkjs_layout_reports_missing_node_runtime():
    with pytest.raises(ElkRuntimeUnavailableError) as excinfo:
        run_elkjs_layout({}, node_command="node-does-not-exist-for-flo")

    assert str(excinfo.value) == (
        "Node.js executable 'node-does-not-exist-for-flo' not found on PATH."
    )


def test_run_elkjs_layout_reports_subprocess_failure(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="elk exploded",
        ),
    )

    with pytest.raises(ElkEngineSubprocessError) as excinfo:
        run_elkjs_layout({}, node_command="node")

    assert str(excinfo.value) == "ELK runtime exited with code 1: elk exploded"


def test_run_elkjs_layout_reports_timeout(monkeypatch):
    def _raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["node"], timeout=3.0)

    monkeypatch.setattr(subprocess, "run", _raise_timeout)

    with pytest.raises(ElkEngineTimeoutError) as excinfo:
        run_elkjs_layout({}, node_command="node", timeout_seconds=3.0)

    assert str(excinfo.value) == "ELK runtime timed out after 3s."


def test_run_elkjs_layout_reports_invalid_json(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="not json",
            stderr="",
        ),
    )

    with pytest.raises(ElkEngineProtocolError) as excinfo:
        run_elkjs_layout({}, node_command="node")

    assert str(excinfo.value) == "ELK runtime returned invalid JSON."


def test_run_elkjs_layout_reports_non_object_json(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="[]",
            stderr="",
        ),
    )

    with pytest.raises(ElkEngineProtocolError) as excinfo:
        run_elkjs_layout({}, node_command="node")

    assert str(excinfo.value) == "ELK runtime returned a non-object JSON payload."


def test_run_elkjs_layout_executes_real_elkjs_when_available():
    if shutil.which("node") is None:
        pytest.skip("Node.js is not available")

    payload = {
        "id": "flo:test",
        "layoutOptions": {"elk.algorithm": "layered", "elk.direction": "RIGHT"},
        "children": [
            {"id": "start", "width": 120, "height": 52, "labels": [{"text": "Start"}]},
            {
                "id": "finish",
                "width": 120,
                "height": 52,
                "labels": [{"text": "Finish"}],
            },
        ],
        "edges": [
            {"id": "e0:start->finish", "sources": ["start"], "targets": ["finish"]}
        ],
    }

    result = run_elkjs_layout(payload)

    assert result["id"] == "flo:test"
    assert len(result.get("children") or []) == 2
    assert len(result.get("edges") or []) == 1
    assert isinstance(result["children"][0].get("x"), (int, float))
    assert isinstance(result["edges"][0].get("sections"), list)
