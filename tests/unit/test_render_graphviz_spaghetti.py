from flo.render import render_dot


def test_spaghetti_renders_rectangle_boundary_overlay():
    ir_like = {
        "nodes": [
            {
                "id": "a",
                "kind": "task",
                "name": "A",
                "location": "pantry",
                "outputs": ["flour"],
            },
            {
                "id": "b",
                "kind": "task",
                "name": "B",
                "location": "prep_bench",
                "inputs": ["flour"],
            },
        ],
        "edges": [{"source": "a", "target": "b"}],
        "process": {
            "metadata": {
                "layout_boundary": {
                    "type": "rectangle",
                    "x": -1.0,
                    "y": -1.0,
                    "width": 8.0,
                    "height": 6.0,
                    "label": "Kitchen Boundary",
                }
            }
        },
    }

    out = render_dot(ir_like, options={"diagram": "spaghetti"})
    assert "__facility_boundary_0" in out
    assert "__facility_boundary_1" in out
    assert "dir=none" in out
    assert "style=dashed" in out
    assert 'label="Kitchen Boundary"' in out


def test_spaghetti_renders_polygon_boundary_overlay_from_points():
    ir_like = {
        "nodes": [
            {
                "id": "a",
                "kind": "task",
                "name": "A",
                "location": "pantry",
                "outputs": ["flour"],
            },
            {
                "id": "b",
                "kind": "task",
                "name": "B",
                "location": "prep_bench",
                "inputs": ["flour"],
            },
        ],
        "edges": [{"source": "a", "target": "b"}],
        "process": {
            "metadata": {
                "layout": {
                    "boundary": {
                        "type": "polygon",
                        "name": "Production Area",
                        "points": [
                            {"x": 0.0, "y": 0.0},
                            {"x": 8.0, "y": 0.0},
                            {"x": 8.0, "y": 4.0},
                            {"x": 0.0, "y": 4.0},
                        ],
                    }
                }
            }
        },
    }

    out = render_dot(ir_like, options={"diagram": "spaghetti"})
    assert "__facility_boundary_0" in out
    assert "__facility_boundary_3" in out
    assert 'label="Production Area"' in out


def test_spaghetti_location_kind_styles_apply_generic_semantic_shapes():
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
                "location": "prep_bench",
                "inputs": ["flour"],
            },
        ],
        "edges": [{"source": "gather", "target": "mix"}],
        "process": {
            "metadata": {
                "locations": [
                    {"id": "pantry", "name": "Pantry", "kind": "storage"},
                    {"id": "prep_bench", "name": "Prep Bench", "kind": "operation"},
                    {"id": "oven_station", "name": "Oven", "kind": "processing"},
                    {"id": "cool_rack", "name": "Cooling Rack", "kind": "staging"},
                    {"id": "sink", "name": "Sink", "kind": "support"},
                    {"id": "hallway", "name": "Hallway", "kind": "transit"},
                ]
            }
        },
    }

    out = render_dot(ir_like, options={"diagram": "spaghetti"})
    assert '"pantry" [label="Pantry", shape=box, fillcolor=lemonchiffon, color=goldenrod4' in out
    assert '"prep_bench" [label="Prep Bench", shape=ellipse, fillcolor=aliceblue, color=steelblue4' in out
    assert '"oven_station" [label="Oven", shape=hexagon, fillcolor=mistyrose, color=firebrick3' in out
    assert '"cool_rack" [label="Cooling Rack", shape=trapezium, fillcolor=honeydew, color=seagreen4' in out
    assert '"sink" [label="Sink", shape=octagon, fillcolor=azure, color=deepskyblue4' in out
    assert '"hallway" [label="Hallway", shape=diamond, fillcolor=mintcream, color=slategray4' in out


def test_spaghetti_legacy_location_kind_aliases_remain_supported():
    ir_like = {
        "nodes": [],
        "edges": [],
        "process": {
            "metadata": {
                "locations": [
                    {"id": "legacy_prep", "name": "Legacy Prep", "kind": "prep"},
                    {"id": "legacy_heat", "name": "Legacy Heat", "kind": "heat"},
                    {"id": "legacy_cooling", "name": "Legacy Cooling", "kind": "cooling"},
                    {"id": "legacy_wash", "name": "Legacy Wash", "kind": "wash"},
                ]
            }
        },
    }

    out = render_dot(ir_like, options={"diagram": "spaghetti"})
    assert '"legacy_prep" [label="Legacy Prep", shape=ellipse, fillcolor=aliceblue, color=steelblue4' in out
    assert '"legacy_heat" [label="Legacy Heat", shape=hexagon, fillcolor=mistyrose, color=firebrick3' in out
    assert '"legacy_cooling" [label="Legacy Cooling", shape=trapezium, fillcolor=honeydew, color=seagreen4' in out
    assert '"legacy_wash" [label="Legacy Wash", shape=octagon, fillcolor=azure, color=deepskyblue4' in out


def test_spaghetti_unknown_location_kind_falls_back_to_default_style():
    ir_like = {
        "nodes": [],
        "edges": [],
        "process": {
            "metadata": {
                "locations": [
                    {"id": "mystery", "name": "Mystery Area", "kind": "custom_kind"},
                ]
            }
        },
    }

    out = render_dot(ir_like, options={"diagram": "spaghetti"})
    assert '"mystery" [label="Mystery Area"];' in out