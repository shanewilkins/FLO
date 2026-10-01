from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

from flo.render.layout_core import elk_runtime
from flo.render.layout_core.elk_errors import (
    ElkEngineProtocolError,
    ElkEngineSubprocessError,
    ElkEngineTimeoutError,
    ElkRuntimeUnavailableError,
)


def test_run_elkjs_layout_raises_when_node_binary_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(elk_runtime.shutil, "which", lambda _cmd: None)

    with pytest.raises(ElkRuntimeUnavailableError, match="not found"):
        elk_runtime.run_elkjs_layout({"id": "root"})


def test_run_elkjs_layout_raises_when_runtime_script_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(elk_runtime.shutil, "which", lambda _cmd: "/usr/bin/node")
    monkeypatch.setattr(elk_runtime.Path, "exists", lambda _self: False)

    with pytest.raises(ElkRuntimeUnavailableError, match="runtime script not found"):
        elk_runtime.run_elkjs_layout({"id": "root"})


def test_run_elkjs_layout_raises_when_subprocess_times_out(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(elk_runtime.shutil, "which", lambda _cmd: "/usr/bin/node")
    monkeypatch.setattr(elk_runtime.Path, "exists", lambda _self: True)

    def _timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="node elk_runtime.mjs", timeout=1)

    monkeypatch.setattr(elk_runtime.subprocess, "run", _timeout)

    with pytest.raises(ElkEngineTimeoutError, match="timed out"):
        elk_runtime.run_elkjs_layout({"id": "root"}, timeout_seconds=1)


def test_run_elkjs_layout_raises_when_subprocess_invocation_fails(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(elk_runtime.shutil, "which", lambda _cmd: "/usr/bin/node")
    monkeypatch.setattr(elk_runtime.Path, "exists", lambda _self: True)

    def _oserror(*_args, **_kwargs):
        raise OSError("boom")

    monkeypatch.setattr(elk_runtime.subprocess, "run", _oserror)

    with pytest.raises(ElkRuntimeUnavailableError, match="Failed to invoke"):
        elk_runtime.run_elkjs_layout({"id": "root"})


def test_run_elkjs_layout_raises_when_subprocess_returns_nonzero(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(elk_runtime.shutil, "which", lambda _cmd: "/usr/bin/node")
    monkeypatch.setattr(elk_runtime.Path, "exists", lambda _self: True)
    monkeypatch.setattr(
        elk_runtime.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=2, stdout="", stderr="bad input"
        ),
    )

    with pytest.raises(ElkEngineSubprocessError, match="code 2: bad input"):
        elk_runtime.run_elkjs_layout({"id": "root"})


def test_run_elkjs_layout_raises_on_invalid_json_response(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(elk_runtime.shutil, "which", lambda _cmd: "/usr/bin/node")
    monkeypatch.setattr(elk_runtime.Path, "exists", lambda _self: True)
    monkeypatch.setattr(
        elk_runtime.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0, stdout="not-json", stderr="oops"
        ),
    )

    with pytest.raises(ElkEngineProtocolError, match="invalid JSON"):
        elk_runtime.run_elkjs_layout({"id": "root"})


def test_run_elkjs_layout_raises_on_non_object_json_response(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(elk_runtime.shutil, "which", lambda _cmd: "/usr/bin/node")
    monkeypatch.setattr(elk_runtime.Path, "exists", lambda _self: True)
    monkeypatch.setattr(
        elk_runtime.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="[]", stderr=""),
    )

    with pytest.raises(ElkEngineProtocolError, match="non-object"):
        elk_runtime.run_elkjs_layout({"id": "root"})


def test_run_elkjs_layout_returns_decoded_object_on_success(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(elk_runtime.shutil, "which", lambda _cmd: "/usr/bin/node")
    monkeypatch.setattr(elk_runtime.Path, "exists", lambda _self: True)
    monkeypatch.setattr(
        elk_runtime.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout='{"id": "flo:ok", "children": []}',
            stderr="",
        ),
    )

    result = elk_runtime.run_elkjs_layout({"id": "root"})

    assert result["id"] == "flo:ok"
    assert result["children"] == []
