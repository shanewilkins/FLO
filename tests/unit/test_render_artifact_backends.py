import pytest

from flo.render import render_artifact, render_dot


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


def test_render_artifact_svg_spaghetti_people_channel_suppresses_material_routes():
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
                ]
            }
        },
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "spaghetti",
            "render_backend": "svg",
            "spaghetti_channel": "people",
        },
    )

    assert artifact.kind == "svg"
    assert 'data-route-channel="people"' in artifact.content
    assert 'data-route-channel="material"' not in artifact.content
    assert ">P 1x<" in artifact.content
    assert "Pantry" in artifact.content
    assert "Prep Bench" in artifact.content


def test_render_artifact_svg_spaghetti_worker_mode_labels_people_routes_by_worker():
    ir_like = {
        "nodes": [
            {
                "id": "gather",
                "kind": "task",
                "name": "Gather",
                "location": "pantry",
                "workers": ["assistant_baker"],
            },
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "location": "prep_bench",
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
                ]
            }
        },
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "spaghetti",
            "render_backend": "svg",
            "spaghetti_channel": "people",
            "spaghetti_people_mode": "worker",
        },
    )

    assert artifact.kind == "svg"
    assert 'data-route-channel="people"' in artifact.content
    assert ">P assistant_baker 1x<" in artifact.content
    assert 'stroke-dasharray="10 4"' not in artifact.content


def test_render_artifact_svg_spaghetti_renders_boundary_polygon_and_label():
    ir_like = {
        "nodes": [
            {
                "id": "gather",
                "kind": "task",
                "name": "Gather",
                "location": "pantry",
                "outputs": ["flour"],
            },
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "location": "bench",
                "inputs": ["flour"],
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
                        "id": "bench",
                        "name": "Bench",
                        "kind": "operation",
                        "metadata": {"spatial": {"x": 3, "y": 1, "unit": "m"}},
                    },
                ],
                "layout_boundary": {
                    "x": -1.0,
                    "y": -1.0,
                    "width": 6.0,
                    "height": 4.0,
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
            "spaghetti_channel": "material",
        },
    )

    assert artifact.kind == "svg"
    assert 'stroke-dasharray="6 4"' in artifact.content
    assert ">Kitchen Boundary<" in artifact.content
    assert '<polygon points="' in artifact.content


def test_render_artifact_svg_spaghetti_maps_location_kinds_to_svg_shapes():
    ir_like = {
        "nodes": [
            {
                "id": "gather",
                "kind": "task",
                "name": "Gather",
                "location": "pantry",
                "outputs": ["tray"],
            },
            {
                "id": "move",
                "kind": "task",
                "name": "Move",
                "location": "corridor",
                "inputs": ["tray"],
                "outputs": ["tray"],
            },
            {
                "id": "bake",
                "kind": "task",
                "name": "Bake",
                "location": "oven",
                "inputs": ["tray"],
            },
        ],
        "edges": [
            {"source": "gather", "target": "move"},
            {"source": "move", "target": "bake"},
        ],
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
                        "id": "corridor",
                        "name": "Corridor",
                        "kind": "transit",
                        "metadata": {"spatial": {"x": 2, "y": 1, "unit": "m"}},
                    },
                    {
                        "id": "oven",
                        "name": "Oven",
                        "kind": "processing",
                        "metadata": {"spatial": {"x": 4, "y": 0, "unit": "m"}},
                    },
                ]
            }
        },
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "spaghetti",
            "render_backend": "svg",
            "spaghetti_channel": "material",
        },
    )

    assert (
        '<g data-location-id="pantry" data-location-shape="rect">' in artifact.content
    )
    assert (
        '<g data-location-id="corridor" data-location-shape="diamond">'
        in artifact.content
    )
    assert (
        '<g data-location-id="oven" data-location-shape="ellipse">' in artifact.content
    )
    assert "Pantry" in artifact.content
    assert "Corridor" in artifact.content
    assert "Oven" in artifact.content


def test_render_artifact_svg_spaghetti_material_routes_emit_item_titles_and_labels():
    ir_like = {
        "nodes": [
            {
                "id": "gather",
                "kind": "task",
                "name": "Gather",
                "location": "pantry",
                "outputs": ["flour"],
            },
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "location": "bench",
                "inputs": ["flour"],
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
                        "id": "bench",
                        "name": "Bench",
                        "kind": "operation",
                        "metadata": {"spatial": {"x": 3, "y": 1, "unit": "m"}},
                    },
                ]
            }
        },
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "spaghetti",
            "render_backend": "svg",
            "spaghetti_channel": "material",
        },
    )

    assert 'data-route-channel="material"' in artifact.content
    assert ">M 1x<" in artifact.content
    assert "<title>items: flour</title>" in artifact.content
    assert 'stroke="tomato"' in artifact.content


def test_render_artifact_svg_spaghetti_people_routes_emit_titles_and_aggregate_style():
    ir_like = {
        "nodes": [
            {
                "id": "gather",
                "kind": "task",
                "name": "Gather",
                "location": "pantry",
                "workers": ["assistant_baker"],
            },
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "location": "bench",
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
                        "id": "bench",
                        "name": "Bench",
                        "kind": "operation",
                        "metadata": {"spatial": {"x": 3, "y": 1, "unit": "m"}},
                    },
                ]
            }
        },
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "spaghetti",
            "render_backend": "svg",
            "spaghetti_channel": "people",
            "spaghetti_people_mode": "aggregate",
        },
    )

    assert 'data-route-channel="people"' in artifact.content
    assert ">P 1x<" in artifact.content
    assert "<title>workers: assistant_baker</title>" in artifact.content
    assert 'stroke="royalblue"' in artifact.content
    assert 'stroke-dasharray="8 6"' in artifact.content


def test_render_artifact_svg_spaghetti_rejects_missing_spatial_metadata():
    ir_like = {
        "nodes": [
            {
                "id": "gather",
                "kind": "task",
                "name": "Gather",
                "location": "pantry",
                "outputs": ["flour"],
            },
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "location": "bench",
                "inputs": ["flour"],
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
                        "id": "bench",
                        "name": "Bench",
                        "kind": "operation",
                    },
                ]
            }
        },
    }

    with pytest.raises(
        ValueError,
        match=r"Direct SVG spaghetti rendering requires explicit spatial metadata .* Missing: bench",
    ):
        render_artifact(
            ir_like,
            options={
                "diagram": "spaghetti",
                "render_backend": "svg",
                "spaghetti_channel": "material",
            },
        )


def test_render_artifact_svg_spaghetti_aggregates_multi_route_hops_and_counts():
    ir_like = {
        "nodes": [
            {
                "id": "gather_a",
                "kind": "task",
                "name": "Gather A",
                "location": "pantry",
                "outputs": ["flour"],
                "workers": ["assistant_baker"],
            },
            {
                "id": "gather_b",
                "kind": "task",
                "name": "Gather B",
                "location": "pantry",
                "outputs": ["flour"],
                "workers": ["lead_baker"],
            },
            {
                "id": "mix_a",
                "kind": "task",
                "name": "Mix A",
                "location": "bench",
                "inputs": ["flour"],
                "outputs": ["dough"],
                "workers": ["assistant_baker"],
            },
            {
                "id": "mix_b",
                "kind": "task",
                "name": "Mix B",
                "location": "bench",
                "inputs": ["flour"],
                "outputs": ["dough"],
                "workers": ["lead_baker"],
            },
            {
                "id": "bake",
                "kind": "task",
                "name": "Bake",
                "location": "oven",
                "inputs": ["dough"],
                "workers": ["assistant_baker", "lead_baker"],
            },
        ],
        "edges": [
            {"source": "gather_a", "target": "mix_a"},
            {"source": "gather_b", "target": "mix_b"},
            {"source": "mix_a", "target": "bake"},
            {"source": "mix_b", "target": "bake"},
        ],
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
                        "id": "bench",
                        "name": "Bench",
                        "kind": "operation",
                        "metadata": {"spatial": {"x": 3, "y": 1, "unit": "m"}},
                    },
                    {
                        "id": "oven",
                        "name": "Oven",
                        "kind": "processing",
                        "metadata": {"spatial": {"x": 6, "y": 0, "unit": "m"}},
                    },
                ]
            }
        },
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "spaghetti",
            "render_backend": "svg",
            "spaghetti_channel": "both",
            "spaghetti_people_mode": "aggregate",
        },
    )

    assert artifact.kind == "svg"
    assert artifact.content.count('data-route-channel="material"') == 2
    assert artifact.content.count('data-route-channel="people"') == 2
    assert artifact.content.count(">M 2x<") == 2
    assert artifact.content.count(">P 2x<") == 2
    assert "<title>items: flour</title>" in artifact.content
    assert "<title>items: dough</title>" in artifact.content
    assert "assistant_baker" in artifact.content
    assert "lead_baker" in artifact.content
    assert 'data-from="pantry" data-to="bench"' in artifact.content
    assert 'data-from="bench" data-to="oven"' in artifact.content
