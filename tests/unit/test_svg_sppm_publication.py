from flo.render import render_artifact


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
    assert "Operations Review" not in artifact.content
    assert "Draft for review" not in artifact.content
