from flo.render import render_artifact, render_dot


def test_render_artifact_can_select_direct_svg_flowchart_backend():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "review", "kind": "decision", "name": "Approved?"},
            {"id": "finish", "kind": "end", "name": "Done"},
        ],
        "edges": [
            {"source": "start", "target": "review"},
            {"source": "review", "target": "finish", "outcome": "yes"},
        ],
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "flowchart",
            "render_backend": "svg",
        },
    )

    assert artifact.kind == "svg"
    assert artifact.backend == "svg"
    assert "<svg" in artifact.content
    assert 'data-flo-diagram="flowchart"' in artifact.content
    assert 'data-node-id="start"' in artifact.content
    assert 'data-node-kind="decision"' in artifact.content
    assert 'data-edge-source="review"' in artifact.content
    assert ">yes<" in artifact.content


def test_render_artifact_can_select_direct_svg_spaghetti_backend():
    ir_like = {
        "nodes": [
            {
                "id": "gather",
                "kind": "task",
                "name": "Gather",
                "location": "pantry",
                "outputs": ["flour"],
                "workers": ["assistant_baker"],
            },
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "location": "prep_bench",
                "inputs": ["flour"],
                "workers": ["assistant_baker"],
            },
        ],
        "edges": [{"source": "gather", "target": "mix"}],
        "process": {
            "metadata": {
                "locations": [
                    {
                        "id": "pantry",
                        "name": "Pantry",
                        "kind": "storage",
                        "metadata": {"spatial": {"x": 0, "y": 0, "unit": "m"}},
                    },
                    {
                        "id": "prep_bench",
                        "name": "Prep Bench",
                        "kind": "operation",
                        "metadata": {"spatial": {"x": 3, "y": 4, "unit": "m"}},
                    },
                ],
                "layout_boundary": {
                    "x": -1.0,
                    "y": -1.0,
                    "width": 6.0,
                    "height": 7.0,
                    "label": "Kitchen Boundary",
                },
            }
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


def test_render_dot_forces_graphviz_even_when_svg_backend_is_requested():
    ir_like = {
        "nodes": [
            {"id": "a", "kind": "task", "name": "A", "location": "one"},
            {"id": "b", "kind": "task", "name": "B", "location": "two"},
        ],
        "edges": [{"source": "a", "target": "b"}],
        "process": {
            "metadata": {
                "locations": [
                    {
                        "id": "one",
                        "name": "One",
                        "metadata": {"spatial": {"x": 0, "y": 0}},
                    },
                    {
                        "id": "two",
                        "name": "Two",
                        "metadata": {"spatial": {"x": 1, "y": 1}},
                    },
                ]
            }
        },
    }

    out = render_dot(ir_like, options={"diagram": "spaghetti", "render_backend": "svg"})

    assert "digraph" in out
    assert "<svg" not in out
