"""Unit tests for the Graphviz rendering service."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from flo.services.errors import RenderError
from flo.services.graphviz import _normalize_svg_outer_padding, _postprocess_wrapped_sppm_svg, render_dot_to_file


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


def test_postprocess_wrapped_sppm_svg_rewrites_boundary_dogleg_geometry(tmp_path: Path):
    dot = '\n'.join(
        [
            'digraph {',
            '  "sort_tag" -> "__wrap_exit_lr_0" [tailport="out_0:e", arrowhead=none, constraint=false, weight=0];',
            '  "__wrap_exit_lr_0" -> "wash" [headport="boundary_in:s", minlen=2, penwidth=1.2];',
            '}',
        ]
    )
    svg_path = tmp_path / "out.svg"
    svg_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <g class="node"><title>sort_tag</title><polygon points="300,260 380,260 380,330 300,330" /></g>
  <g class="node"><title>wash</title><polygon points="80,140 160,140 160,210 80,210" /></g>
  <g class="edge"><title>sort_tag:e-&gt;__wrap_exit_lr_0</title><path d="M 0,0 L 1,1" /></g>
  <g class="edge"><title>__wrap_exit_lr_0-&gt;wash:s</title><path d="M 0,0 L 1,1" /><polygon points="0,0 1,1 2,2 0,0" /></g>
</svg>
""",
        encoding="utf-8",
    )

    _postprocess_wrapped_sppm_svg(dot=dot, output_path=svg_path)

    svg = svg_path.read_text(encoding="utf-8")
    assert 'd="M 380.00,295.00 L 392.00,295.00 L 392.00,128.00 L 120.00,128.00"' in svg
    assert 'd="M 120.00,128.00 L 120.00,140.00"' in svg
    assert 'points="120.00,140.00 116.00,132.00 124.00,132.00 120.00,140.00"' in svg

def test_postprocess_wrapped_sppm_svg_rewrites_two_boundary_doglegs_exactly(tmp_path: Path):
    dot = "\n".join(
        [
            "digraph {",
            '  "sort_tag" -> "__wrap_exit_lr_0" [tailport="out_0:e", arrowhead=none, constraint=false, weight=0];',
            '  "__wrap_exit_lr_0" -> "wash" [headport="boundary_in:s", minlen=2, penwidth=1.2];',
            '  "fold_package" -> "__wrap_exit_lr_1" [tailport="out_0:e", arrowhead=none, constraint=false, weight=0];',
            '  "__wrap_exit_lr_1" -> "stage_notify" [headport="boundary_in:s", minlen=2, penwidth=1.2];',
            "}",
        ]
    )
    svg_path = tmp_path / "out.svg"
    svg_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <g class="node"><title>sort_tag</title><polygon points="307.75,263.5 386.25,263.5 386.25,332.75 307.75,332.75" /></g>
  <g class="node"><title>wash</title><polygon points="79.75,141.25 158.25,141.25 158.25,210.5 79.75,210.5" /></g>
  <g class="node"><title>fold_package</title><polygon points="298.88,141.25 405.12,141.25 405.12,210.5 298.88,210.5" /></g>
  <g class="node"><title>stage_notify</title><polygon points="79.25,19 178.75,19 178.75,88.25 79.25,88.25" /></g>
  <g class="edge"><title>sort_tag:e-&gt;__wrap_exit_lr_0</title><path d="M 0,0 L 1,1" /></g>
  <g class="edge"><title>__wrap_exit_lr_0-&gt;wash:s</title><path d="M 0,0 L 1,1" /><polygon points="0,0 1,1 2,2 0,0" /></g>
  <g class="edge"><title>fold_package:e-&gt;__wrap_exit_lr_1</title><path d="M 0,0 L 1,1" /></g>
  <g class="edge"><title>__wrap_exit_lr_1-&gt;stage_notify:s</title><path d="M 0,0 L 1,1" /><polygon points="0,0 1,1 2,2 0,0" /></g>
</svg>
""",
        encoding="utf-8",
    )

    _postprocess_wrapped_sppm_svg(dot=dot, output_path=svg_path)
    svg = svg_path.read_text(encoding="utf-8")

    assert 'd="M 386.25,298.12 L 398.25,298.12 L 398.25,129.25 L 119.00,129.25"' in svg
    assert 'd="M 119.00,129.25 L 119.00,141.25"' in svg
    assert 'points="119.00,141.25 115.00,133.25 123.00,133.25 119.00,141.25"' in svg

    assert 'd="M 405.12,175.88 L 417.12,175.88 L 417.12,7.00 L 129.00,7.00"' in svg
    assert 'd="M 129.00,7.00 L 129.00,19.00"' in svg
    assert 'points="129.00,19.00 125.00,11.00 133.00,11.00 129.00,19.00"' in svg


def test_normalize_svg_outer_padding_sets_even_border_and_updates_canvas(tmp_path: Path):
        svg_path = tmp_path / "pad.svg"
        svg_path.write_text(
                """<?xml version="1.0" encoding="UTF-8"?>
<svg width="200pt" height="150pt" viewBox="0 0 200 150" xmlns="http://www.w3.org/2000/svg">
    <g class="node"><title>a</title><polygon points="20,30 120,30 120,80 20,80" /></g>
</svg>
""",
                encoding="utf-8",
        )

        _normalize_svg_outer_padding(output_path=svg_path, padding=10.0)
        svg = svg_path.read_text(encoding="utf-8")

        assert 'viewBox="10.00 20.00 120.00 70.00"' in svg
        assert 'width="120.00pt"' in svg
        assert 'height="70.00pt"' in svg
        assert 'id="__flo_canvas_bg"' in svg
        assert 'fill="white"' in svg
        assert 'style="background:#fff;"' in svg


def test_normalize_svg_outer_padding_accounts_for_graph_transform_translation(tmp_path: Path):
        svg_path = tmp_path / "pad_transform.svg"
        svg_path.write_text(
                """<?xml version="1.0" encoding="UTF-8"?>
<svg width="200pt" height="150pt" viewBox="0 0 200 150" xmlns="http://www.w3.org/2000/svg">
    <g class="graph" transform="scale(1 1) rotate(0) translate(7.2 165.2)">
        <g class="node"><title>a</title><polygon points="20,30 120,30 120,80 20,80" /></g>
    </g>
</svg>
""",
                encoding="utf-8",
        )

        _normalize_svg_outer_padding(output_path=svg_path, padding=10.0)
        svg = svg_path.read_text(encoding="utf-8")

        assert 'viewBox="17.20 185.20 120.00 70.00"' in svg
        assert 'width="120.00pt"' in svg
        assert 'height="70.00pt"' in svg
        assert 'id="__flo_canvas_bg"' in svg
        assert 'style="background:#fff;"' in svg


def test_normalize_svg_outer_padding_ignores_graph_background_bounds(tmp_path: Path):
        svg_path = tmp_path / "pad_graph_bounds.svg"
        svg_path.write_text(
                """<?xml version="1.0" encoding="UTF-8"?>
<svg width="421pt" height="335.75pt" viewBox="0 0 421 335.75" xmlns="http://www.w3.org/2000/svg">
    <g class="graph" transform="scale(1 1) rotate(0) translate(7.2 365.2)">
        <polygon fill="white" stroke="none" points="-3.6,3.6 -3.6,-361.6 431.6,-361.6 431.6,3.6 -3.6,3.6" />
        <g class="node"><title>a</title><polygon points="20,-30 120,-30 120,-80 20,-80" /></g>
    </g>
</svg>
""",
                encoding="utf-8",
        )

        _normalize_svg_outer_padding(output_path=svg_path, padding=10.0)
        svg = svg_path.read_text(encoding="utf-8")

        assert 'viewBox="17.20 275.20 120.00 70.00"' in svg
        assert 'width="120.00pt"' in svg
        assert 'height="70.00pt"' in svg
        assert 'style="background:#fff;"' in svg
