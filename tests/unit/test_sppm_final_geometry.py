"""Independent final-SVG checks and shared-terminal routing regressions."""

import importlib.util
import json
from pathlib import Path

import pytest

from flo.render.layout_core.rework_geometry import infer_rework_row_ids

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "sppm_final_geometry", ROOT / "scripts/check_sppm_geometry.py"
)
assert SPEC is not None and SPEC.loader is not None
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


@pytest.mark.parametrize(
    "svg",
    sorted((ROOT / "tests/golden/sppm").glob("*/render.svg")),
    ids=lambda path: path.parent.name,
)
def test_release_corpus_final_svg_geometry(svg):
    layout = json.loads(svg.with_name("layout_result.json").read_text())
    members = {lane["id"]: lane["node_ids"] for lane in layout["lanes"]}
    assert CHECK.geometry_violations(svg.read_text(), members) == ()


def test_shared_end_remains_mainline_when_correction_has_no_return_edge():
    mainline, correction = infer_rework_row_ids(
        node_ids={"start", "decision", "fix", "done"},
        edges=[
            ("start", "decision", False, None),
            ("decision", "done", False, None),
            ("decision", "fix", True, "branch"),
            ("fix", "done", False, None),
        ],
    )
    assert correction == {"fix"}
    assert mainline == {"start", "decision", "done"}


_BASE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200">
<g transform="translate(0,0)">
<g data-node-id="a"><rect x="0" y="20" width="50" height="50"/></g>
<g data-node-id="b"><rect x="200" y="20" width="50" height="50"/></g>
<g data-edge-source="a" data-edge-target="b"><polyline points="50,45 200,45"/>{annotation}</g>
</g></svg>"""


@pytest.mark.parametrize(
    ("before", "after", "message"),
    [
        ("50,45 200,45", "51,45 200,45", "detached"),
        ("50,45 200,45", "50,45 100,100 200,45", "diagonal"),
        ('x="200"', 'x="30"', "overlap"),
        ('viewBox="0 0 400 200"', 'viewBox="0 0 220 200"', "outside canvas"),
    ],
)
def test_final_geometry_gate_detects_broken_svg(before, after, message):
    svg = _BASE.format(annotation="").replace(before, after)
    assert any(message in issue for issue in CHECK.geometry_violations(svg))


def test_final_geometry_gate_detects_annotation_covering_a_node():
    svg = _BASE.format(annotation='<rect x="40" y="30" width="30" height="18"/>')
    assert any(
        "annotation a->b overlaps node a" in issue
        for issue in CHECK.geometry_violations(svg)
    )


def test_final_geometry_gate_detects_a_route_through_an_unrelated_node():
    svg = _BASE.format(annotation="").replace(
        "</g></svg>",
        '<g data-node-id="c"><rect x="100" y="20" width="30" height="50"/></g></g></svg>',
    )
    assert "edge a->b crosses node c" in CHECK.geometry_violations(svg)


def test_final_geometry_gate_detects_node_outside_its_lane():
    svg = _BASE.format(annotation="").replace(
        '<g transform="translate(0,0)">',
        '<g transform="translate(0,0)"><g data-lane-id="owner"><rect x="10" y="10" width="20" height="20"/></g>',
    )
    assert "node a outside lane owner" in CHECK.geometry_violations(
        svg, {"owner": ["a"]}
    )


def test_final_geometry_gate_preserves_missing_route_behavior():
    svg = _BASE.format(annotation='<rect x="390" y="30" width="30" height="18"/>')
    svg = svg.replace('<polyline points="50,45 200,45"/>', "")

    assert CHECK.geometry_violations(svg) == ("edge a->b has no route",)


def test_final_geometry_gate_reports_outside_segments_once():
    svg = _BASE.format(annotation="").replace(
        "50,45 200,45", "50,45 50,250 200,250 200,45"
    )

    assert CHECK.geometry_violations(svg) == ("edge a->b outside canvas",)


def test_final_geometry_gate_preserves_cross_edge_annotation_checks():
    annotation = '<rect x="100" y="30" width="20" height="18"/>'
    svg = _BASE.format(annotation=annotation).replace(
        "</g></svg>",
        (
            '<g data-edge-source="a" data-edge-target="b">'
            '<polyline points="50,45 200,45"/>'
            f"{annotation}</g></g></svg>"
        ),
    )

    assert CHECK.geometry_violations(svg) == ("annotations a->b/a->b overlap",)
