import flo.render._graphviz_dot_common as common
import flo.render._graphviz_dot_spaghetti as spaghetti
from flo.render.options import RenderOptions


def test_common_extract_nodes_edges_handles_none_unknown_and_dict_filtering():
    class Unknown:
        pass

    assert common._extract_nodes_and_edges(None) == ([], [])
    assert common._extract_nodes_and_edges(Unknown()) == ([], [])

    nodes, edges = common._extract_from_dict(
        {
            "nodes": [
                42,
                {"id": "child", "attrs": {"subprocess_parent": "parent"}},
            ],
            "edges": [
                {"source": "a", "target": "b"},
                "not-an-edge",
            ],
        }
    )
    assert nodes == [{"id": "child", "attrs": {"subprocess_parent": "parent"}, "subprocess_parent": "parent"}]
    assert edges == [{"source": "a", "target": "b"}]


def test_common_node_lane_map_and_cross_lane_guards():
    lanes = common._node_lane_map(
        [
            {"id": "", "lane": "ops"},
            {"id": "a", "lane": "ops"},
            {"id": "b", "lane": "qa"},
        ]
    )
    assert lanes == {"a": "ops", "b": "qa"}
    assert common._is_cross_lane_edge("missing", "b", lanes) is False
    assert common._is_cross_lane_edge("a", "b", lanes) is True


def test_common_node_label_render_queue_shape_and_cluster_id_fallback():
    options = RenderOptions(detail="verbose", profile="analysis")
    label = common._node_label(
        node_id="node_1",
        name="Node",
        kind="task",
        lane="",
        note="",
        options=options,
    )
    assert "[task]" in label
    assert "lane:" not in label

    assert common._render_node_line({"name": "Missing ID"}, indent="  ", options=RenderOptions()) == []
    assert common._shape_for_kind("queue") == "box"
    assert common._safe_cluster_id("$$$") == "lane"


def test_common_parent_only_view_and_edge_collapse_dedup_paths():
    nodes = [{"id": "a"}, {"id": "b"}]
    edges = [{"source": "a", "target": "b"}]
    projected_nodes, projected_edges = common._project_parent_only_subprocess_view(nodes, edges)
    assert projected_nodes is nodes
    assert projected_edges is edges

    collapsed_edges: list[dict[str, str]] = []
    seen_edges: set[tuple[str, str, str | None]] = set()
    common._add_collapsed_edge(collapsed_edges, seen_edges, source="a", target="a", branch_label=None)
    common._add_collapsed_edge(collapsed_edges, seen_edges, source="a", target="b", branch_label="yes")
    common._add_collapsed_edge(collapsed_edges, seen_edges, source="a", target="b", branch_label="yes")
    assert collapsed_edges == [{"source": "a", "target": "b", "label": "yes"}]


def test_common_branch_label_trimming_and_hidden_target_traversal():
    assert common._edge_branch_label({"outcome": "  yes "}) == "yes"
    assert common._edge_branch_label({"outcome": "   "}) is None
    assert common._edge_branch_label({"label": " maybe "}) == "maybe"
    assert common._edge_branch_label({"label": "   "}) is None

    targets = common._visible_targets_through_hidden(
        start_hidden="h1",
        initial_label=None,
        hidden_ids={"h1", "h2"},
        visible_ids={"visible"},
        outgoing={
            "h1": [{"target": None}, {"target": "h2"}],
            "h2": [{"target": "h1"}, {"target": "visible"}],
        },
    )
    assert ("visible", None) in targets


def test_common_append_node_cluster_handles_reentry_skip_missing_and_child_recursion():
    options = RenderOptions()

    lines: list[str] = []
    common._append_node_or_subprocess_cluster(
        lines=lines,
        node_id="rendered",
        nodes_by_id={"rendered": {"id": "rendered", "name": "Rendered"}},
        children_by_parent={},
        rendered={"rendered"},
        active_stack=set(),
        options=options,
        indent="  ",
    )
    assert lines == []

    lines = []
    common._append_node_or_subprocess_cluster(
        lines=lines,
        node_id="missing",
        nodes_by_id={"present": {"id": "present", "name": "Present"}},
        children_by_parent={},
        rendered=set(),
        active_stack=set(),
        options=options,
        indent="  ",
    )
    assert lines == []

    lines = []
    rendered: set[str] = set()
    common._append_node_or_subprocess_cluster(
        lines=lines,
        node_id="loop",
        nodes_by_id={"loop": {"id": "loop", "name": "Loop", "kind": "task"}},
        children_by_parent={},
        rendered=rendered,
        active_stack={"loop"},
        options=options,
        indent="  ",
    )
    assert any('"loop"' in line for line in lines)
    assert "loop" in rendered

    lines = []
    rendered = set()
    common._append_node_or_subprocess_cluster(
        lines=lines,
        node_id="parent",
        nodes_by_id={
            "parent": {"id": "parent", "name": "Parent", "kind": "task"},
            "child": {"id": "child", "name": "Child", "kind": "task"},
        },
        children_by_parent={"parent": ["child"]},
        rendered=rendered,
        active_stack=set(),
        options=options,
        indent="  ",
    )
    assert any('"child"' in line for line in lines)


def test_common_append_clustered_node_pass_skips_top_level_children_with_parent():
    lines: list[str] = []
    common._append_clustered_node_pass(
        lines=lines,
        ordered_nodes=[
            {"id": "parent", "name": "Parent"},
            {"id": "child", "name": "Child", "subprocess_parent": "parent"},
        ],
        nodes_by_id={
            "parent": {"id": "parent", "name": "Parent"},
            "child": {"id": "child", "name": "Child", "subprocess_parent": "parent"},
        },
        children_by_parent={},
        rendered=set(),
        active_stack=set(),
        options=RenderOptions(),
        indent="  ",
        top_level_only=True,
    )
    assert any('"parent"' in line for line in lines)
    assert not any('"child"' in line for line in lines)


def test_spaghetti_boundary_and_numeric_helpers_cover_guard_paths():
    assert spaghetti._as_number(True) is None
    assert spaghetti._as_number(2.5) == 2.5

    assert spaghetti._boundary_points(None) == []
    assert spaghetti._boundary_points("invalid") == []
    assert spaghetti._boundary_points(
        [
            {"x": 0, "y": 0},
            {"x": True, "y": 1},
            {"x": 1, "y": 1},
        ]
    ) == [(0.0, 0.0), (1.0, 1.0)]
    assert spaghetti._boundary_centroid([]) == (0.0, 0.0)
    assert spaghetti._boundary_label({"label": "  ", "name": "  Area  "}) == "Area"


def test_spaghetti_rectangle_and_kind_normalization_helpers():
    assert spaghetti._rectangle_bounds({"min_x": 0, "min_y": 0, "max_x": 4, "max_y": 3}) == (0.0, 0.0, 4.0, 3.0)
    assert spaghetti._rectangle_bounds({"left": 4, "bottom": 3, "right": 0, "top": 0}) == (0.0, 0.0, 4.0, 3.0)
    assert spaghetti._rectangle_bounds({"x": 0, "y": 0, "width": 0, "height": 1}) is None

    assert spaghetti._normalize_location_kind_token("  transit--path  ") == "transit_path"
    assert spaghetti._canonical_spaghetti_location_kind("   ") is None
    assert spaghetti._spaghetti_location_visual_attrs({"kind": "unknown_kind"}) == []


def test_spaghetti_route_helpers_cover_missing_and_worker_fallbacks():
    assert spaghetti._spaghetti_route_edge_line(
        route={"to_location": "b"},
        options=RenderOptions(diagram="spaghetti"),
        channel="material",
    ) is None
    assert spaghetti._spaghetti_distance_label({"distance": {"value": "far", "unit": "m"}}) is None
    assert spaghetti._spaghetti_route_entities_taillabel({"workers": []}, channel="people") is None
    assert spaghetti._spaghetti_primary_worker({"workers": ["   "]}) is None

    edge_attrs = spaghetti._spaghetti_channel_edge_attrs(
        channel="people",
        route={"workers": []},
        options=RenderOptions(diagram="spaghetti", spaghetti_people_mode="worker"),
    )
    assert edge_attrs == ["color=royalblue4", "style=dashed", "fontcolor=royalblue4"]
