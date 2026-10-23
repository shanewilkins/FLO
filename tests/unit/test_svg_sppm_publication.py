import xml.etree.ElementTree as ET
from pathlib import Path

from flo.render import render_artifact
from flo.render.options import RenderOptions
from flo.source import parse_adapter


def test_sppm_svg_renders_publication_header_and_footer_bands():
    process = {
        "process": {
            "id": "ops_review",
            "name": "Operations Review",
            "metadata": {
                "footer_metrics": {"Lead Time": "24 min"},
                "footer_notes": ["Draft for review"],
            },
        },
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "finish", "kind": "end", "name": "Finish"},
        ],
        "edges": [{"source": "start", "target": "finish"}],
    }

    artifact = render_artifact(
        process,
        options={
            "diagram": "sppm",
            "render_backend": "svg",
            "publication_page_format": "letter",
        },
    )

    assert 'data-sppm-publication-page-id="main-p1"' in artifact.content
    assert 'data-sppm-publication-band="header"' in artifact.content
    assert 'data-sppm-publication-band="footer"' in artifact.content
    assert "Operations Review" in artifact.content
    assert "Process: ops_review" in artifact.content
    assert "Lead Time: 24 min" in artifact.content
    assert "Draft for review" in artifact.content
    assert artifact.metadata["publication"] == {
        "page_id": "main-p1",
        "page_format": "letter",
    }


def test_sppm_svg_omits_disabled_publication_bands():
    process = {
        "process": {
            "id": "ops_review",
            "name": "Operations Review",
            "metadata": {"footer_notes": ["Draft for review"]},
        },
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "finish", "kind": "end", "name": "Finish"},
        ],
        "edges": [{"source": "start", "target": "finish"}],
    }

    artifact = render_artifact(
        process,
        options={
            "diagram": "sppm",
            "render_backend": "svg",
            "no_header": True,
            "no_footer": True,
        },
    )

    assert "data-sppm-publication-band" not in artifact.content
    assert (
        '<title id="flo-svg-title">Operations Review — SPPM</title>' in artifact.content
    )
    assert ">Process: ops_review</text>" not in artifact.content
    assert "Draft for review" not in artifact.content


def test_book_rework_connectors_are_vertical_and_entire_correction_path_is_red():
    source = Path("examples/reference/book_washnfold.flo")
    process = parse_adapter(source.read_text(), source_path=str(source))
    options = {
        "diagram": "sppm",
        "render_backend": "svg",
        "layout_width": "1200px",
        "layout_wrap": "auto",
        "theme": "mpi-lms",
        "sppm_output_profile": "book",
        "no_header": True,
        "no_footer": True,
    }
    artifact = render_artifact(process, options=options)
    assert artifact.content == render_artifact(process, options=options).content
    edges = _svg_edge_elements(artifact.content)
    namespace = "{http://www.w3.org/2000/svg}"
    for key in (
        ("packaging_check", "correction_queue"),
        ("fold_correction", "notification_queue"),
    ):
        line = edges[key].find(f"{namespace}polyline")
        assert line is not None
        assert (
            len({point.split(",")[0] for point in line.attrib["points"].split()}) == 1
        )
    correction = edges[("correction_queue", "fold_correction")]
    line = correction.find(f"{namespace}polyline")
    assert line is not None
    assert (
        line.get("stroke")
        == RenderOptions.from_mapping(options).resolved_theme.role("rework").border
    )
    assert line.get("stroke-dasharray") == "2 6"
    assert line.get("marker-end") == "url(#flo-sppm-rework-arrow)"
    assert correction.get("data-edge-rework-variant") is None
    assert (
        edges[("packaging_check", "notification_queue")].get("data-edge-kind")
        == "direct"
    )
    internal = next(
        edge
        for edge in process["transitions"]
        if edge["source"] == "correction_queue" and edge["target"] == "fold_correction"
    )
    assert not internal.get("rework")


def _svg_edge_elements(content):
    return {
        (group.get("data-edge-source"), group.get("data-edge-target")): group
        for group in ET.fromstring(content).iter()
        if group.get("data-edge-source")
    }
