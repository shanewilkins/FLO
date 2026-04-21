"""Unit tests for the Graphviz rendering service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from flo.services.errors import RenderError
from flo.services.graphviz import render_dot_to_file


SIMPLE_DOT = "digraph G { A -> B }"


def test_dot_not_found_raises_render_error(monkeypatch):
    monkeypatch.setattr("flo.services.graphviz.shutil.which", lambda _: None)
    with pytest.raises(RenderError, match="not found on PATH"):
        render_dot_to_file(SIMPLE_DOT, "/tmp/out.png")


def test_unsupported_extension_raises_render_error(tmp_path, monkeypatch):
    monkeypatch.setattr("flo.services.graphviz.shutil.which", lambda _: "/usr/bin/dot")
    out = str(tmp_path / "out.bmp")
    with pytest.raises(RenderError, match="Unsupported output format"):
        render_dot_to_file(SIMPLE_DOT, out)


def test_dot_subprocess_success(tmp_path, monkeypatch):
    monkeypatch.setattr("flo.services.graphviz.shutil.which", lambda _: "/usr/bin/dot")
    out = str(tmp_path / "out.png")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with patch("flo.services.graphviz.subprocess.run", return_value=mock_result) as mock_run:
        render_dot_to_file(SIMPLE_DOT, out)

    mock_run.assert_called_once_with(
        ["dot", "-Tpng", "-o", out],
        input=SIMPLE_DOT,
        text=True,
        capture_output=True,
    )


def test_dot_subprocess_nonzero_raises_render_error(tmp_path, monkeypatch):
    monkeypatch.setattr("flo.services.graphviz.shutil.which", lambda _: "/usr/bin/dot")
    out = str(tmp_path / "out.svg")

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "syntax error"

    with patch("flo.services.graphviz.subprocess.run", return_value=mock_result):
        with pytest.raises(RenderError, match="syntax error"):
            render_dot_to_file(SIMPLE_DOT, out)


def test_dot_subprocess_oserror_raises_render_error(tmp_path, monkeypatch):
    monkeypatch.setattr("flo.services.graphviz.shutil.which", lambda _: "/usr/bin/dot")
    out = str(tmp_path / "out.pdf")

    with patch("flo.services.graphviz.subprocess.run", side_effect=OSError("permission denied")):
        with pytest.raises(RenderError, match="permission denied"):
            render_dot_to_file(SIMPLE_DOT, out)


@pytest.mark.parametrize("ext", ["png", "svg", "pdf", "eps", "ps"])
def test_all_supported_formats_accepted(ext, monkeypatch):
    monkeypatch.setattr("flo.services.graphviz.shutil.which", lambda _: "/usr/bin/dot")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with patch("flo.services.graphviz.subprocess.run", return_value=mock_result) as mock_run:
        render_dot_to_file(SIMPLE_DOT, f"/tmp/out.{ext}")

    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert f"-T{ext}" in cmd
