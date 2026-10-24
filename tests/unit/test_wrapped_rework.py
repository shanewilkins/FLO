from dataclasses import replace
from itertools import pairwise

from flo.render.layout_core.elk_contracts import (
    ElkLayoutEdge,
    ElkLayoutLane,
    ElkLayoutNode,
    ElkLayoutRequest,
)
from flo.render.layout_core.models import LayoutBounds
from flo.render.layout_core.rework_geometry import segment_hits
from flo.render.sppm.layout_wrap import _apply_sppm_wrap_rows
from flo.render.sppm.wrapped_rework import (
    choose_rework_rows,
    simple_rework_chains,
)


def _request():
    rows = (("wash", "dry"), ("fold", "check", "ready"), ("stage", "notify", "stop"))
    nodes = tuple(
        ElkLayoutNode(node, node, kind, width, height)
        for node, kind, width, height in (
            ("wash", "task", 150, 110),
            ("dry", "task", 200, 110),
            ("fold", "task", 200, 130),
            ("check", "decision", 220, 140),
            ("ready", "queue", 220, 160),
            ("stage", "task", 240, 110),
            ("notify", "task", 210, 110),
            ("stop", "end", 140, 60),
            ("correction_queue", "queue", 200, 160),
            ("correct", "task", 200, 110),
        )
    )
    mainline = [node for row in rows for node in row]
    edges = tuple(
        ElkLayoutEdge(str(i), a, b) for i, (a, b) in enumerate(pairwise(mainline))
    )
    edges += (
        ElkLayoutEdge(
            "branch",
            "check",
            "correction_queue",
            label="No",
            is_rework=True,
            rework_variant="branch",
        ),
        ElkLayoutEdge("correction", "correction_queue", "correct"),
        ElkLayoutEdge(
            "return",
            "correct",
            "ready",
            label="Corrected",
            is_rework=True,
            rework_variant="return",
        ),
    )
    lanes = tuple(
        ElkLayoutLane(f"__sppm_row_wrap_{i}", "", row) for i, row in enumerate(rows)
    )
    lanes += (
        ElkLayoutLane("__sppm_row_wrap_rework_3", "", ("correction_queue", "correct")),
    )
    return ElkLayoutRequest("sppm", "RIGHT", lanes, nodes, edges)


def _layout(request):
    bounds = {
        node.id: LayoutBounds(0, 0, node.width_px, node.height_px)
        for node in request.nodes
    }
    paths = {}
    canvas, lanes = _apply_sppm_wrap_rows(
        request=request, node_bounds=bounds, edge_paths=paths
    )
    return canvas, lanes, bounds, paths


def test_local_rework_goes_above_and_routes_around_frozen_mainline():
    request = _request()
    first = _layout(request)
    assert first == _layout(request)
    _canvas, lanes, bounds, paths = first
    assert (
        bounds["dry"].y_px
        < bounds["correct"].y_px
        < bounds["check"].y_px
        < bounds["stage"].y_px
    )
    assert paths[("check", "correction_queue")].source_port_side == "NORTH"
    assert paths[("correct", "ready")].target_port_side == "NORTH"
    assert [lane.node_ids for lane in lanes.values() if "rework" not in lane.id] == [
        lane.node_ids for lane in request.lanes if "rework" not in lane.id
    ]
    for (source, target), path in paths.items():
        for a, b in pairwise(path.points):
            assert a.x_px == b.x_px or a.y_px == b.y_px
            for node, box in bounds.items():
                if node not in (source, target):
                    assert not segment_hits(a, b, box), (source, target, node)


def test_ties_choose_below_and_only_two_candidates_are_scored():
    calls = []

    def score(candidate):
        calls.append(candidate)
        return (0, 0, 0, 0.0)

    chosen = choose_rework_rows(_request(), score)
    assert len(calls) == 2
    lanes = [lane.node_ids for lane in chosen.lanes]
    assert (
        lanes.index(("correction_queue", "correct"))
        == lanes.index(("fold", "check", "ready")) + 1
    )


def test_colliding_candidates_keep_the_outside_fallback():
    request = _request()
    assert choose_rework_rows(request, lambda _: (1, 0, 0, 0.0)) == request


def test_cross_row_rejoin_shared_and_nested_corrections_use_fallback():
    request = _request()
    cross_row = replace(
        request,
        edges=tuple(
            replace(edge, target_id="wash") if edge.id == "return" else edge
            for edge in request.edges
        ),
    )
    shared = replace(
        request,
        edges=(
            *request.edges,
            ElkLayoutEdge(
                "shared",
                "ready",
                "correction_queue",
                is_rework=True,
                rework_variant="branch",
            ),
        ),
    )
    nested = replace(
        request,
        edges=(
            *request.edges,
            ElkLayoutEdge(
                "nested",
                "correct",
                "correction_queue",
                is_rework=True,
                rework_variant="branch",
            ),
        ),
    )
    for complex_request in (cross_row, shared, nested):
        assert simple_rework_chains(complex_request) == []
        assert (
            choose_rework_rows(
                complex_request,
                lambda _: (_ for _ in ()).throw(AssertionError("must not score")),
            )
            == complex_request
        )


def test_edge_order_and_captions_do_not_change_chain_classification():
    request = _request()
    changed = replace(
        request,
        edges=tuple(
            replace(edge, label="Different caption") for edge in reversed(request.edges)
        ),
    )
    assert simple_rework_chains(changed) == simple_rework_chains(request)
    assert _layout(changed)[2] == _layout(request)[2]


def test_below_is_selected_when_it_has_the_shorter_clear_route():
    request = _request()
    request = replace(
        request,
        nodes=tuple(
            replace(
                node,
                width_px={"wash": 280, "dry": 300, "fold": 280}.get(
                    node.id, node.width_px
                ),
            )
            for node in request.nodes
        ),
    )
    _canvas, _lanes, bounds, paths = _layout(request)
    assert bounds["check"].y_px < bounds["correct"].y_px < bounds["stage"].y_px
    assert paths[("check", "correction_queue")].source_port_side == "SOUTH"
    assert paths[("correct", "ready")].target_port_side == "SOUTH"


def test_independent_chains_are_considered_once_in_stable_order():
    request = _request()
    extra = ("other_queue", "other_correction")
    request = replace(
        request,
        nodes=(
            *request.nodes,
            replace(request.nodes[-2], id=extra[0]),
            replace(request.nodes[-1], id=extra[1]),
        ),
        lanes=(
            *request.lanes[:-1],
            replace(request.lanes[-1], node_ids=(*request.lanes[-1].node_ids, *extra)),
        ),
        edges=(
            *request.edges,
            ElkLayoutEdge(
                "other_branch",
                "check",
                extra[0],
                is_rework=True,
                rework_variant="branch",
            ),
            ElkLayoutEdge("other_work", *extra),
            ElkLayoutEdge(
                "other_return",
                extra[1],
                "ready",
                is_rework=True,
                rework_variant="return",
            ),
        ),
    )
    calls = []

    def score(candidate):
        calls.append(candidate)
        return (0, 0, 0, 0.0)

    chosen = choose_rework_rows(request, score)
    assert len(calls) == 4
    assert len({lane.id for lane in chosen.lanes}) == len(chosen.lanes)
    reordered = replace(request, edges=tuple(reversed(request.edges)))
    assert chosen.lanes == choose_rework_rows(reordered, lambda _: (0, 0, 0, 0.0)).lanes
    assert sorted(node for lane in chosen.lanes for node in lane.node_ids) == sorted(
        node.id for node in request.nodes
    )


def test_continuation_corridors_clear_tall_neighbors_in_the_same_row():
    request = _request()
    request = replace(
        request,
        nodes=tuple(
            replace(node, height_px=300) if node.id == "wash" else node
            for node in request.nodes
        ),
    )
    _canvas, _lanes, bounds, paths = _layout(request)
    for (source, target), path in paths.items():
        for a, b in pairwise(path.points):
            for node, box in bounds.items():
                if node not in (source, target):
                    assert not segment_hits(a, b, box), (source, target, node)
