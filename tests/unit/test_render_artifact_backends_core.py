from flo.render import render_artifact


def test_render_artifact_can_select_direct_svg_spaghetti_backend():
    ir_like = {
        "nodes": [
            {
                "id": "gather",
                "kind": "task",
                "name": "Gather",
                "location": "pantry",
                "produces": ["flour"],
                "performed_by": ["assistant_baker"],
            },
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "location": "prep_bench",
                "consumes": ["flour"],
                "performed_by": ["assistant_baker"],
            },
        ],
        "edges": [{"source": "gather", "target": "mix"}],
        "process": {
            "extensions": {
                "flo:spaghetti": {
                    "boundary": {
                        "x": -1.0,
                        "y": -1.0,
                        "width": 6.0,
                        "height": 7.0,
                        "label": "Kitchen Boundary",
                    }
                }
            },
            "locations": [
                {
                    "id": "pantry",
                    "name": "Pantry",
                    "kind": "storage",
                    "spatial": {"x": 0, "y": 0, "unit": "m"},
                },
                {
                    "id": "prep_bench",
                    "name": "Prep Bench",
                    "kind": "operation",
                    "spatial": {"x": 3, "y": 4, "unit": "m"},
                },
            ],
        },
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "spaghetti",
            "render_backend": "svg",
            "detail": "verbose",
        },
    )

    assert artifact.kind == "svg"
    assert artifact.backend == "svg"
    assert "<svg" in artifact.content
    assert 'data-route-channel="material"' in artifact.content
    assert 'data-route-channel="people"' in artifact.content
    assert "Kitchen Boundary" in artifact.content
    assert "Pantry" in artifact.content
    assert "Prep Bench" in artifact.content
