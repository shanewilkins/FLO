"""Acceptance checks for canonical book evidence in the actual SVG."""

from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from flo.process.ir import validate_ir
from flo.render import render_artifact
from flo.source import compile_adapter, parse_adapter

_OPTIONS = {
    "diagram": "sppm",
    "sppm_theme": "mpi-lms",
    "sppm_output_profile": "book",
    "background_color": "transparent",
    "no_header": True,
    "no_footer": True,
    "layout_wrap": "auto",
    "layout_width": "1200px",
}
_NS = {"svg": "http://www.w3.org/2000/svg"}


def _book_ir():
    source = Path("examples/reference/book_washnfold.flo")
    process = compile_adapter(
        parse_adapter(source.read_text(), source_path=str(source))
    )
    validate_ir(process)
    return process


def _node_groups(svg):
    root = ET.fromstring(svg)  # noqa: S314 - Renderer-produced SVG.
    return {
        group.get("data-node-id"): group
        for group in root.findall(".//svg:g[@data-node-id]", _NS)
    }


def test_book_referenced_waits_render_primary_values_without_mutating_evidence():
    process = _book_ir()
    before = deepcopy(process)
    artifact = render_artifact(process, options=_OPTIONS)
    groups = _node_groups(artifact.content)

    for node_id, expected in (
        ("notification_queue", "W/T: 37.9 min"),
        ("correction_queue", "W/T: 5.6 min"),
    ):
        text = " ".join(groups[node_id].itertext())
        assert expected in text
        assert "W/T: ?" not in text
    assert process == before
    assert next(
        node for node in process.nodes if node.id == "notification_queue"
    ).wait_time == {"ref": "stage_collection.wait_time"}


def test_book_task_text_stays_inside_measured_cards():
    artifact = render_artifact(_book_ir(), options=_OPTIONS)
    groups = _node_groups(artifact.content)
    checked = 0
    for group in groups.values():
        if group.get("data-node-kind") != "task":
            continue
        card = group.find("svg:rect", _NS)
        assert card is not None
        left, top, width, height = (
            float(card.get(key)) for key in ("x", "y", "width", "height")
        )
        body = [
            text
            for text in group.findall("svg:text", _NS)
            if text.get("text-anchor") == "start"
        ]
        assert body
        assert any("P/T:" in (text.text or "") for text in body)
        for text in body:
            x, y = float(text.get("x")), float(text.get("y"))
            size = float(text.get("font-size"))
            # A conservative average advance for this Latin/numeric body text;
            # exercise emitted lines and card bounds, independently of sizing code.
            estimated_right = x + len(text.text or "") * size * 0.6
            assert left < x < estimated_right <= left + width - 6, text.text
            assert top + size <= y <= top + height - 6, text.text
        checked += 1
    assert checked == 8
    assert artifact.metadata["geometry"]["overflows_requested_bounds"] is False


@pytest.mark.parametrize("value", [0, 37.9])
def test_included_wait_references_resolve_for_measurement_and_svg(tmp_path, value):
    included = tmp_path / "work.flo"
    included.write_text(f"""steps:
  - {{id: start, kind: start}}
  - {{id: queue, kind: queue, wait_time: {{ref: work.wait_time}}}}
  - id: work
    kind: task
    wait_time:
      basis: observed
      primary: median
      analysis_input: mean
      results:
        median: {{method: median, value: {value}, unit: min}}
        mean: {{method: mean, value: 100, unit: min}}
""")
    source = tmp_path / "root.flo"
    source.write_text("""spec_version: "0.1"
process: {id: included, name: Included waiting}
includes: [work.flo]
steps:
  - {id: end, kind: end}
transitions:
  - {source: start, target: queue}
  - {source: queue, target: work}
  - {source: work, target: end}
""")
    process = compile_adapter(
        parse_adapter(source.read_text(), source_path=str(source))
    )
    validate_ir(process)
    before = deepcopy(process)
    artifact = render_artifact(process, options={"diagram": "sppm"})
    groups = _node_groups(artifact.content)
    assert f"W/T: {value:g} min" in " ".join(groups["queue"].itertext())
    assert process == before
