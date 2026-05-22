"""Unit tests for the Graphviz rendering service."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

from flo.render._sppm_postprocess_contract import SppmSvgPostprocessContract

from flo.services.graphviz import (
    _normalize_node_backing_fills_svg,
    _normalize_svg_outer_padding,
    _postprocess_queue_baseline_alignment_svg,
    _postprocess_direct_midpoint_edges_svg,
    _postprocess_wrapped_sppm_svg,
)


def test_postprocess_wrapped_sppm_svg_rewrites_boundary_dogleg_geometry(tmp_path: Path):
    dot = "\n".join(
        [
            "digraph {",
            '  "sort_tag" -> "__wrap_exit_lr_0" [tailport="out_0:e", arrowhead=none, constraint=false, weight=0];',
            '  "__wrap_exit_lr_0" -> "wash" [headport="boundary_in:s", minlen=2, penwidth=1.2];',
            "}",
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


def test_postprocess_wrapped_sppm_svg_rewrites_two_boundary_doglegs_exactly(
    tmp_path: Path,
):
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


def test_postprocess_direct_midpoint_edges_svg_rewrites_horizontal_edge_endpoints(
    tmp_path: Path,
):
    svg_path = tmp_path / "direct.svg"
    svg_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
    <g class="node"><title>start</title><path d="M 0,0 L 40,0 L 40,20 L 0,20" /></g>
    <g class="node"><title>next</title><polygon points="100,40 180,40 180,100 100,100" /></g>
    <g class="edge"><title>start:e-&gt;next:w</title><path d="M 1,1 L 2,2" /><polygon points="0,0 1,1 2,2 0,0" /></g>
</svg>
""",
        encoding="utf-8",
    )

    _postprocess_direct_midpoint_edges_svg(output_path=svg_path)
    svg = svg_path.read_text(encoding="utf-8")

    assert 'd="M 40.00,10.00 L 100.00,70.00"' in svg
    assert 'points="100.00,70.00 90.00,73.50 90.00,66.50 100.00,70.00"' in svg


def test_postprocess_direct_midpoint_edges_svg_handles_ellipse_nodes(tmp_path: Path):
    svg_path = tmp_path / "direct_ellipse.svg"
    svg_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
    <g class="node"><title>triage</title><polygon fill="#ffffff" stroke="#333333" points="405,-730.42 625.83,-620 405,-509.58" /></g>
    <g class="node"><title>process_queue</title><ellipse fill="#ff9800" stroke="#e65100" cx="756.83" cy="-620" rx="45" ry="45" /></g>
    <g class="edge"><title>triage:e-&gt;process_queue:w</title><path d="M 1,1 L 2,2" /><polygon points="0,0 1,1 2,2 0,0" /></g>
</svg>
""",
        encoding="utf-8",
    )

    _postprocess_direct_midpoint_edges_svg(output_path=svg_path)
    svg = svg_path.read_text(encoding="utf-8")

    assert 'd="M 625.83,-620.00 L 711.83,-620.00"' in svg
    assert 'points="711.83,-620.00 701.83,-616.50 701.83,-623.50 711.83,-620.00"' in svg


def test_postprocess_direct_midpoint_edges_svg_uses_triangle_side_midpoint_for_queue(
    tmp_path: Path,
):
    svg_path = tmp_path / "direct_triangle_midpoint.svg"
    svg_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
    <g class="node"><title>start</title><polygon points="0,40 40,40 40,80 0,80" /></g>
    <g class="node"><title>queue</title><polygon fill="#ff9800" stroke="#e65100" points="100,0 50,100 150,100 100,0" /></g>
    <g class="edge"><title>start:e-&gt;queue:w</title><path d="M 1,1 L 2,2" /><polygon points="0,0 1,1 2,2 0,0" /></g>
</svg>
""",
        encoding="utf-8",
    )

    _postprocess_direct_midpoint_edges_svg(output_path=svg_path)
    svg = svg_path.read_text(encoding="utf-8")

    # Left non-base side midpoint of the triangle is (75, 50).
    assert 'd="M 40.00,50.00 L 75.00,50.00"' in svg
    assert 'points="75.00,50.00 65.00,53.50 65.00,46.50 75.00,50.00"' in svg


def test_postprocess_queue_baseline_alignment_svg_moves_queue_to_mainline_baseline(
    tmp_path: Path,
):
    svg_path = tmp_path / "queue_baseline.svg"
    svg_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
    <g class="node"><title>left</title><polygon fill="#ffffff" stroke="#333333" points="0,50 40,50 40,90 0,90" /></g>
    <g class="node"><title>queue</title><polygon fill="#ff9800" stroke="#e65100" points="100,0 50,100 150,100 100,0" /></g>
    <g class="node"><title>right</title><polygon fill="#ffffff" stroke="#333333" points="200,50 240,50 240,90 200,90" /></g>
    <g class="edge"><title>left:e-&gt;queue:w</title><path d="M 40,60 L 75,60" /></g>
    <g class="edge"><title>queue:e-&gt;right:w</title><path d="M 125,60 L 200,60" /></g>
</svg>
""",
        encoding="utf-8",
    )

    _postprocess_queue_baseline_alignment_svg(output_path=svg_path)
    _postprocess_direct_midpoint_edges_svg(output_path=svg_path)
    svg = svg_path.read_text(encoding="utf-8")

    # Triangle gets shifted so side-midpoint Y aligns with neighboring baseline Y=70.
    # Edges initially at Y=60 get rewritten to Y=70 with .2f formatting.
    assert 'points="100.00,20.00 50.00,120.00 150.00,120.00 100.00,20.00"' in svg
    assert 'd="M 40.00,70.00 L 75.00,70.00"' in svg
    assert 'd="M 125.00,70.00 L 200.00,70.00"' in svg


def test_postprocess_direct_midpoint_edges_svg_preserves_existing_horizontal_paths(
    tmp_path: Path,
):
    svg_path = tmp_path / "direct_preserve_horizontal.svg"
    svg_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
    <g class="node"><title>triage</title><polygon fill="#ffffff" stroke="#333333" points="510,-570 630,-570 630,-530 510,-530" /></g>
    <g class="node"><title>process_queue</title><polygon fill="#ffffff" stroke="#333333" points="770,-575 716,-525 824,-525 770,-575" /></g>
    <g class="edge"><title>triage:e-&gt;process_queue:w</title><path d="M630.00,-550.00C630.00,-550.00 716.00,-550.00 716.00,-550.00" /><polygon points="716.00,-553.50 726.00,-550.00 716.00,-546.50 716.00,-553.50" /></g>
</svg>
""",
        encoding="utf-8",
    )

    _postprocess_direct_midpoint_edges_svg(output_path=svg_path)
    svg = svg_path.read_text(encoding="utf-8")

    # Already-horizontal path at correct Y should remain untouched.
    assert 'd="M630.00,-550.00C630.00,-550.00 716.00,-550.00 716.00,-550.00"' in svg


def test_normalize_node_backing_fills_svg_replaces_lightgrey_backings(tmp_path: Path):
    svg_path = tmp_path / "fills.svg"
    svg_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
    <g class="node"><title>a</title><polygon fill="lightgrey" stroke="none" points="0,0 10,0 10,10 0,10" /></g>
    <g class="node"><title>b</title><polygon fill="#81c784" stroke="none" points="0,0 10,0 10,10 0,10" /></g>
</svg>
""",
        encoding="utf-8",
    )

    _normalize_node_backing_fills_svg(output_path=svg_path)
    svg = svg_path.read_text(encoding="utf-8")

    assert (
        'fill="#ffffff" stroke="none" points="0,0 10,0 10,10 0,10" fill-opacity="1"'
        in svg
    )
    assert 'fill="#81c784" stroke="none" points="0,0 10,0 10,10 0,10"' in svg


def test_normalize_svg_outer_padding_sets_even_border_and_updates_canvas(
    tmp_path: Path,
):
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
    assert 'fill="#ffffff"' in svg
    assert 'style="background:#ffffff;"' in svg


def test_normalize_svg_outer_padding_accounts_for_graph_transform_translation(
    tmp_path: Path,
):
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
    assert 'style="background:#ffffff;"' in svg


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
    assert 'style="background:#ffffff;"' in svg


def test_postprocess_wrapped_sppm_svg_supports_contract_and_north_port_fallback(
    tmp_path: Path,
):
    contract = SimpleNamespace(
        wrapped_boundary_edges=[SimpleNamespace(source_id="sort_tag", target_id="wash")]
    )
    svg_path = tmp_path / "wrapped_contract.svg"
    svg_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
    <svg xmlns="http://www.w3.org/2000/svg">
      <g class="node"><title>sort_tag</title><polygon points="300,260 380,260 380,330 300,330" /></g>
      <g class="node"><title>wash</title><polygon points="80,140 160,140 160,210 80,210" /></g>
      <g class="edge"><title>sort_tag:e-&gt;__wrap_exit_lr_0</title><path d="M 0,0 L 1,1" /></g>
      <g class="edge"><title>__wrap_exit_lr_0-&gt;wash:n</title><path d="M 0,0 L 1,1" /><polygon points="0,0 1,1 2,2 0,0" /></g>
    </svg>
    """,
        encoding="utf-8",
    )

    _postprocess_wrapped_sppm_svg(
        dot="digraph {}",
        output_path=svg_path,
        contract=cast(SppmSvgPostprocessContract, contract),
    )
    svg = svg_path.read_text(encoding="utf-8")

    assert 'd="M 380.00,295.00 L 392.00,295.00 L 392.00,128.00 L 120.00,128.00"' in svg
    assert 'd="M 120.00,128.00 L 120.00,140.00"' in svg


def test_postprocess_wrapped_sppm_svg_contract_rewrites_multiple_anchors(
    tmp_path: Path,
):
    contract = SimpleNamespace(
        wrapped_boundary_edges=[
            SimpleNamespace(
                source_id="sort_tag", target_id="wash", anchor_id="__wrap_exit_lr_0"
            ),
            SimpleNamespace(
                source_id="fold_package",
                target_id="stage_notify",
                anchor_id="__wrap_exit_lr_1",
            ),
        ]
    )
    svg_path = tmp_path / "wrapped_contract_multi.svg"
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

    _postprocess_wrapped_sppm_svg(
        dot="digraph {}",
        output_path=svg_path,
        contract=cast(SppmSvgPostprocessContract, contract),
    )
    svg = svg_path.read_text(encoding="utf-8")

    assert 'd="M 386.25,298.12 L 398.25,298.12 L 398.25,129.25 L 119.00,129.25"' in svg
    assert 'd="M 119.00,129.25 L 119.00,141.25"' in svg
    assert 'd="M 405.12,175.88 L 417.12,175.88 L 417.12,7.00 L 129.00,7.00"' in svg
    assert 'd="M 129.00,7.00 L 129.00,19.00"' in svg


def test_postprocess_wrapped_sppm_svg_contract_resolves_missing_anchor_from_svg_titles(
    tmp_path: Path,
):
    contract = SimpleNamespace(
        wrapped_boundary_edges=[
            SimpleNamespace(source_id="sort_tag", target_id="wash", anchor_id=None)
        ]
    )
    svg_path = tmp_path / "wrapped_contract_missing_anchor.svg"
    svg_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
    <svg xmlns="http://www.w3.org/2000/svg">
      <g class="node"><title>sort_tag</title><polygon points="300,260 380,260 380,330 300,330" /></g>
      <g class="node"><title>wash</title><polygon points="80,140 160,140 160,210 80,210" /></g>
      <g class="edge"><title>sort_tag:e-&gt;__wrap_exit_lr_7</title><path d="M 0,0 L 1,1" /></g>
      <g class="edge"><title>__wrap_exit_lr_7-&gt;wash:n</title><path d="M 0,0 L 1,1" /><polygon points="0,0 1,1 2,2 0,0" /></g>
    </svg>
    """,
        encoding="utf-8",
    )

    _postprocess_wrapped_sppm_svg(
        dot="digraph {}",
        output_path=svg_path,
        contract=cast(SppmSvgPostprocessContract, contract),
    )
    svg = svg_path.read_text(encoding="utf-8")

    assert 'd="M 380.00,295.00 L 392.00,295.00 L 392.00,128.00 L 120.00,128.00"' in svg
    assert 'd="M 120.00,128.00 L 120.00,140.00"' in svg


def test_normalize_svg_outer_padding_no_content_points_is_noop(tmp_path: Path):
    svg_path = tmp_path / "empty.svg"
    original = """<?xml version="1.0" encoding="UTF-8"?>
    <svg width="10pt" height="10pt" viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg"></svg>
    """
    svg_path.write_text(original, encoding="utf-8")

    _normalize_svg_outer_padding(output_path=svg_path, padding=10.0)
    assert svg_path.read_text(encoding="utf-8") == original


def test_postprocess_direct_midpoint_edges_skips_invalid_and_internal_edges(
    tmp_path: Path,
):
    svg_path = tmp_path / "skip_direct.svg"
    svg_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
    <svg xmlns="http://www.w3.org/2000/svg">
        <g class="node"><title>a</title><polygon points="0,0 40,0 40,20 0,20" /></g>
        <g class="node"><title>b</title><polygon points="100,0 140,0 140,20 100,20" /></g>
        <g class="edge"><title>invalid-title</title><path d="M 1,1 L 2,2" /></g>
        <g class="edge"><title>a:n-&gt;b:s</title><path d="M 3,3 L 4,4" /></g>
        <g class="edge"><title>__anchor:e-&gt;b:w</title><path d="M 5,5 L 6,6" /></g>
    </svg>
    """,
        encoding="utf-8",
    )

    _postprocess_direct_midpoint_edges_svg(output_path=svg_path)
    svg = svg_path.read_text(encoding="utf-8")

    assert 'd="M 1,1 L 2,2"' in svg
    assert 'd="M 3,3 L 4,4"' in svg
    assert 'd="M 5,5 L 6,6"' in svg


def test_normalize_node_backing_fills_svg_skips_non_none_stroke(tmp_path: Path):
    svg_path = tmp_path / "stroke_skip.svg"
    svg_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
    <svg xmlns="http://www.w3.org/2000/svg">
        <g class="node"><title>a</title><polygon fill="lightgrey" stroke="black" points="0,0 10,0 10,10 0,10" /></g>
    </svg>
    """,
        encoding="utf-8",
    )

    _normalize_node_backing_fills_svg(output_path=svg_path)
    svg = svg_path.read_text(encoding="utf-8")
    assert 'fill="lightgrey" stroke="black"' in svg
