"""Run SPPM layout strategy matrix against invariant checks."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
from statistics import fmean
from typing import Any, Iterator

from flo.adapters import parse_adapter
from flo.render._diagnostics import RenderDiagnosticsReport
from flo.render.layout_core import (
    ElkLayoutRequest,
    LayoutBounds,
    LayoutPoint,
    LayoutResult,
    build_sppm_elk_layout_request,
    execute_elk_layout,
    run_elkjs_layout,
    serialize_layout_result,
)
from flo.render.options import RenderOptions

REPO_ROOT = Path(__file__).resolve().parents[1]

CORPUS_PATH = REPO_ROOT / "examples" / "conformance" / "sppm_corpus.json"
OUT_DIR = REPO_ROOT / "renders" / "conformance" / "sppm_strategy_matrix"

ENV_PARTITION_MODE = "FLO_SPPM_PARTITION_MODE"
ENV_PORT_CONSTRAINTS = "FLO_SPPM_PORT_CONSTRAINTS"
ENV_HELPER_ANCHORS = "FLO_SPPM_HELPER_ANCHORS"
ENV_SPACING_PROFILE = "FLO_SPPM_SPACING_PROFILE"

PARTITION_MODES = ("branch_aligned", "chain_progressive")
PORT_CONSTRAINTS = ("fixed_side", "fixed_order")
HELPER_ANCHORS = ("off", "conditional", "always")
SPACING_PROFILES = ("compact", "balanced", "roomy")


@dataclass(frozen=True)
class Strategy:
    partition_mode: str
    port_constraints: str
    helper_anchors: str
    spacing_profile: str

    @property
    def id(self) -> str:
        return (
            f"part={self.partition_mode}|port={self.port_constraints}|"
            f"anchors={self.helper_anchors}|space={self.spacing_profile}"
        )


@dataclass(frozen=True)
class CaseEvaluation:
    case_id: str
    passed: bool
    failures: tuple[str, ...]
    determinism_hash: str
    total_bends: int
    total_edge_length_px: float
    canvas_area_px2: float
    weighted_crossings: float
    p95_bends: float
    p95_edge_length_px: float
    diagnostic_warning_count: int
    diagnostic_error_count: int
    diagnostic_warning_burden: float
    partial_output: bool


@dataclass(frozen=True)
class StrategyEvaluation:
    strategy: Strategy
    total_cases: int
    passed_cases: int
    failed_cases: int
    total_failures: int
    case_results: tuple[CaseEvaluation, ...]
    avg_weighted_crossings: float
    avg_p95_bends: float
    avg_p95_edge_length_px: float
    avg_bends: float
    avg_edge_length_px: float
    avg_canvas_area_px2: float
    avg_diagnostic_warning_count: float
    avg_diagnostic_error_count: float
    avg_diagnostic_warning_burden: float
    partial_output_cases: int


def main() -> int:
    parser = argparse.ArgumentParser(prog="run_sppm_strategy_matrix.py")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=CORPUS_PATH,
        help="Path to SPPM corpus manifest JSON.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=OUT_DIR,
        help="Directory for matrix score outputs.",
    )
    args = parser.parse_args()

    manifest = _resolve_path(args.manifest)
    out_dir = _resolve_path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cases = _load_cases(manifest)
    evaluations = _run_matrix(cases)
    sorted_evaluations = sorted(
        evaluations,
        key=lambda current: (
            -current.passed_cases,
            current.total_failures,
            current.avg_diagnostic_warning_burden,
            current.avg_diagnostic_warning_count,
            current.avg_weighted_crossings,
            current.avg_p95_bends,
            current.avg_p95_edge_length_px,
            current.avg_bends,
            current.avg_edge_length_px,
            current.avg_canvas_area_px2,
            current.strategy.id,
        ),
    )

    scoreboard = {
        "manifest": str(manifest.relative_to(REPO_ROOT)),
        "total_cases": len(cases),
        "total_strategies": len(sorted_evaluations),
        "strategies": [_evaluation_json(current) for current in sorted_evaluations],
    }
    (out_dir / "scoreboard.json").write_text(
        json.dumps(scoreboard, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "scoreboard.md").write_text(
        _scoreboard_markdown(sorted_evaluations),
        encoding="utf-8",
    )

    top = sorted_evaluations[0]
    print(
        "Top strategy: "
        f"{top.strategy.id} "
        f"({top.passed_cases}/{top.total_cases} cases, "
        f"{top.total_failures} invariant failures, "
        f"avg_weighted_crossings={top.avg_weighted_crossings:.2f}, "
        f"avg_p95_bends={top.avg_p95_bends:.2f}, "
        f"avg_p95_edge_length_px={top.avg_p95_edge_length_px:.2f}, "
        f"avg_diag_warning_burden={top.avg_diagnostic_warning_burden:.2f}, "
        f"avg_diag_warnings={top.avg_diagnostic_warning_count:.2f}, "
        f"avg_bends={top.avg_bends:.2f}, "
        f"avg_edge_length_px={top.avg_edge_length_px:.2f}, "
        f"avg_canvas_area_px2={top.avg_canvas_area_px2:.2f})"
    )
    print(f"Wrote: {(out_dir / 'scoreboard.json').relative_to(REPO_ROOT)}")
    print(f"Wrote: {(out_dir / 'scoreboard.md').relative_to(REPO_ROOT)}")
    return 0


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def _load_cases(manifest: Path) -> tuple[dict[str, Any], ...]:
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    raw_cases = payload.get("cases") if isinstance(payload, dict) else None
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError(f"Manifest has no cases: {manifest}")

    cases: list[dict[str, Any]] = []
    for raw_case in raw_cases:
        if not isinstance(raw_case, dict):
            continue
        case_id = raw_case.get("id")
        case_input = raw_case.get("input")
        options = raw_case.get("options", {})
        if not isinstance(case_id, str) or not case_id:
            continue
        if not isinstance(case_input, str) or not case_input:
            continue
        if not isinstance(options, dict):
            continue
        cases.append({"id": case_id, "input": case_input, "options": options})

    if not cases:
        raise ValueError(f"Manifest has no valid cases: {manifest}")
    return tuple(cases)


def _run_matrix(cases: tuple[dict[str, Any], ...]) -> tuple[StrategyEvaluation, ...]:
    strategies = tuple(
        Strategy(
            partition_mode=partition_mode,
            port_constraints=port_constraints,
            helper_anchors=helper_anchors,
            spacing_profile=spacing_profile,
        )
        for partition_mode, port_constraints, helper_anchors, spacing_profile in itertools.product(
            PARTITION_MODES,
            PORT_CONSTRAINTS,
            HELPER_ANCHORS,
            SPACING_PROFILES,
        )
    )

    evaluations: list[StrategyEvaluation] = []
    for strategy in strategies:
        case_results = [_evaluate_case(case=case, strategy=strategy) for case in cases]
        passed_cases = sum(1 for case_result in case_results if case_result.passed)
        total_failures = sum(len(case_result.failures) for case_result in case_results)
        avg_weighted_crossings = fmean(
            case_result.weighted_crossings for case_result in case_results
        )
        avg_p95_bends = fmean(case_result.p95_bends for case_result in case_results)
        avg_p95_edge_length_px = fmean(
            case_result.p95_edge_length_px for case_result in case_results
        )
        avg_bends = fmean(case_result.total_bends for case_result in case_results)
        avg_edge_length_px = fmean(
            case_result.total_edge_length_px for case_result in case_results
        )
        avg_canvas_area_px2 = fmean(
            case_result.canvas_area_px2 for case_result in case_results
        )
        avg_diagnostic_warning_count = fmean(
            case_result.diagnostic_warning_count for case_result in case_results
        )
        avg_diagnostic_error_count = fmean(
            case_result.diagnostic_error_count for case_result in case_results
        )
        avg_diagnostic_warning_burden = fmean(
            case_result.diagnostic_warning_burden for case_result in case_results
        )
        partial_output_cases = sum(
            1 for case_result in case_results if case_result.partial_output
        )
        evaluations.append(
            StrategyEvaluation(
                strategy=strategy,
                total_cases=len(case_results),
                passed_cases=passed_cases,
                failed_cases=len(case_results) - passed_cases,
                total_failures=total_failures,
                case_results=tuple(case_results),
                avg_weighted_crossings=avg_weighted_crossings,
                avg_p95_bends=avg_p95_bends,
                avg_p95_edge_length_px=avg_p95_edge_length_px,
                avg_bends=avg_bends,
                avg_edge_length_px=avg_edge_length_px,
                avg_canvas_area_px2=avg_canvas_area_px2,
                avg_diagnostic_warning_count=avg_diagnostic_warning_count,
                avg_diagnostic_error_count=avg_diagnostic_error_count,
                avg_diagnostic_warning_burden=avg_diagnostic_warning_burden,
                partial_output_cases=partial_output_cases,
            )
        )
    return tuple(evaluations)


def _evaluate_case(*, case: dict[str, Any], strategy: Strategy) -> CaseEvaluation:
    with _strategy_environment(strategy):
        request, result, options = _request_and_result(case)
        determinism_hashes = [_layout_result_hash(result)]
        for _ in range(2):
            _, rerun_result, _ = _request_and_result(case)
            determinism_hashes.append(_layout_result_hash(rerun_result))
    determinism_hash = determinism_hashes[0]
    diagnostics_report = result.diagnostics_report(
        diagram="sppm",
        backend="elk",
        artifact_kind="layout_result",
        strict=options.layout_fit == "fit-strict",
    )

    failures: list[str] = []
    failures.extend(
        _invariant_diagnostics_clean(diagnostics_report, case_id=str(case["id"]))
    )
    failures.extend(_invariant_mainline_progress(request, result))
    failures.extend(_invariant_rework_separation(request, result))
    failures.extend(_invariant_rework_attachments(request, result))
    failures.extend(_invariant_determinism(determinism_hashes, case_id=str(case["id"])))
    failures.extend(_invariant_no_node_overlap(result))
    failures.extend(_invariant_nodes_within_lanes(result))
    failures.extend(_invariant_edge_through_node(request, result))
    total_bends, total_edge_length_px = _edge_geometry_metrics(result)
    p95_bends, p95_edge_length_px = _edge_tail_metrics(result)
    weighted_crossings = _weighted_edge_crossings(result)
    diagnostic_warning_count = diagnostics_report.warning_count
    diagnostic_error_count = diagnostics_report.error_count
    diagnostic_warning_burden = _diagnostic_warning_burden(diagnostics_report)
    partial_output = diagnostics_report.partial_output
    canvas = result.canvas_bounds
    canvas_area_px2 = max(canvas.width_px, 0.0) * max(canvas.height_px, 0.0)
    return CaseEvaluation(
        case_id=str(case["id"]),
        passed=not failures,
        failures=tuple(failures),
        determinism_hash=determinism_hash,
        total_bends=total_bends,
        total_edge_length_px=total_edge_length_px,
        canvas_area_px2=canvas_area_px2,
        weighted_crossings=weighted_crossings,
        p95_bends=p95_bends,
        p95_edge_length_px=p95_edge_length_px,
        diagnostic_warning_count=diagnostic_warning_count,
        diagnostic_error_count=diagnostic_error_count,
        diagnostic_warning_burden=diagnostic_warning_burden,
        partial_output=partial_output,
    )


def _invariant_diagnostics_clean(
    report: RenderDiagnosticsReport,
    *,
    case_id: str,
) -> list[str]:
    failures: list[str] = []
    if report.error_count:
        failures.append(
            f"diagnostics_error case={case_id} error_count={report.error_count}"
        )
    if report.partial_output:
        failures.append(
            f"diagnostics_partial_output case={case_id} summary={report.summary}"
        )
    return failures


def _diagnostic_warning_burden(report: RenderDiagnosticsReport) -> float:
    """Weighted warning burden for secondary ranking.

    Higher numbers indicate less trustworthy output, with geometry-loss categories
    weighted above advisory categories.
    """
    category_weights = {
        "namespace_collision": 5.0,
        "missing_geometry": 3.0,
        "lossy_recovery": 2.0,
        "uncategorized": 1.0,
    }
    return sum(
        category_weights.get(category, 1.0) * count
        for category, count in report.category_counts.items()
    )


def _layout_result_hash(result: LayoutResult) -> str:
    payload = serialize_layout_result(result).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _invariant_determinism(hashes: list[str], *, case_id: str) -> list[str]:
    unique_hashes = sorted(set(hashes))
    if len(unique_hashes) <= 1:
        return []
    summary = ",".join(current[:12] for current in unique_hashes)
    return [f"determinism case={case_id} hashes={summary}"]


def _invariant_no_node_overlap(
    result: LayoutResult, *, tolerance_px: float = 1.0
) -> list[str]:
    failures: list[str] = []
    node_ids = sorted(result.node_bounds.keys())
    for index, source_id in enumerate(node_ids):
        source = result.node_bounds[source_id]
        for target_id in node_ids[index + 1 :]:
            target = result.node_bounds[target_id]
            overlap_w = min(
                source.x_px + source.width_px, target.x_px + target.width_px
            ) - max(
                source.x_px,
                target.x_px,
            )
            overlap_h = min(
                source.y_px + source.height_px, target.y_px + target.height_px
            ) - max(
                source.y_px,
                target.y_px,
            )
            if overlap_w > tolerance_px and overlap_h > tolerance_px:
                failures.append(
                    "node_overlap "
                    f"nodes={source_id},{target_id} "
                    f"overlap_w={overlap_w:.2f} overlap_h={overlap_h:.2f}"
                )
    return failures


def _invariant_nodes_within_lanes(
    result: LayoutResult,
    *,
    tolerance_px: float = 2.0,
) -> list[str]:
    failures: list[str] = []
    for lane in result.lanes:
        lane_bounds = lane.bounds
        min_x = lane_bounds.x_px - tolerance_px
        max_x = lane_bounds.x_px + lane_bounds.width_px + tolerance_px
        min_y = lane_bounds.y_px - tolerance_px
        max_y = lane_bounds.y_px + lane_bounds.height_px + tolerance_px
        for node_id in lane.node_ids:
            bounds = result.bounds_for(node_id)
            if bounds is None:
                failures.append(
                    f"lane_containment lane={lane.id} node={node_id} missing-bounds"
                )
                continue
            if (
                bounds.x_px < min_x
                or bounds.y_px < min_y
                or (bounds.x_px + bounds.width_px) > max_x
                or (bounds.y_px + bounds.height_px) > max_y
            ):
                failures.append(
                    "lane_containment "
                    f"lane={lane.id} node={node_id} "
                    f"node=({bounds.x_px:.2f},{bounds.y_px:.2f},{bounds.width_px:.2f},{bounds.height_px:.2f}) "
                    f"lane=({lane_bounds.x_px:.2f},{lane_bounds.y_px:.2f},{lane_bounds.width_px:.2f},{lane_bounds.height_px:.2f})"
                )
    return failures


def _invariant_edge_through_node(
    request: ElkLayoutRequest,
    result: LayoutResult,
    *,
    interior_padding_px: float = 1.0,
) -> list[str]:
    failures: list[str] = []
    node_bounds = result.node_bounds
    for edge in request.edges:
        path = result.path_for(edge.source_id, edge.target_id)
        if path is None or len(path.points) < 2:
            continue
        excluded = {edge.source_id, edge.target_id}
        for index in range(len(path.points) - 1):
            start = path.points[index]
            end = path.points[index + 1]
            for node_id, bounds in node_bounds.items():
                if node_id in excluded:
                    continue
                if _segment_intersects_rect_interior(
                    start,
                    end,
                    bounds,
                    interior_padding_px=interior_padding_px,
                ):
                    failures.append(
                        "edge_through_node "
                        f"edge={edge.source_id}->{edge.target_id} "
                        f"segment={index} node={node_id}"
                    )
    return failures


def _segment_intersects_rect_interior(
    start: LayoutPoint,
    end: LayoutPoint,
    bounds: LayoutBounds,
    *,
    interior_padding_px: float,
) -> bool:
    min_x = bounds.x_px + interior_padding_px
    max_x = bounds.x_px + bounds.width_px - interior_padding_px
    min_y = bounds.y_px + interior_padding_px
    max_y = bounds.y_px + bounds.height_px - interior_padding_px
    if min_x >= max_x or min_y >= max_y:
        return False

    rect_segments = (
        (LayoutPoint(min_x, min_y), LayoutPoint(max_x, min_y)),
        (LayoutPoint(max_x, min_y), LayoutPoint(max_x, max_y)),
        (LayoutPoint(max_x, max_y), LayoutPoint(min_x, max_y)),
        (LayoutPoint(min_x, max_y), LayoutPoint(min_x, min_y)),
    )
    if _point_in_rect(start, min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y):
        return True
    if _point_in_rect(end, min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y):
        return True
    return any(
        _segments_intersect(start, end, seg_start, seg_end)
        for seg_start, seg_end in rect_segments
    )


def _point_in_rect(
    point: LayoutPoint,
    *,
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
) -> bool:
    return min_x <= point.x_px <= max_x and min_y <= point.y_px <= max_y


def _segments_intersect(
    a1: LayoutPoint,
    a2: LayoutPoint,
    b1: LayoutPoint,
    b2: LayoutPoint,
    *,
    epsilon: float = 1e-9,
) -> bool:
    def _orientation(p: LayoutPoint, q: LayoutPoint, r: LayoutPoint) -> int:
        value = ((q.y_px - p.y_px) * (r.x_px - q.x_px)) - (
            (q.x_px - p.x_px) * (r.y_px - q.y_px)
        )
        if abs(value) <= epsilon:
            return 0
        return 1 if value > 0 else 2

    def _on_segment(p: LayoutPoint, q: LayoutPoint, r: LayoutPoint) -> bool:
        return (
            min(p.x_px, r.x_px) - epsilon <= q.x_px <= max(p.x_px, r.x_px) + epsilon
            and min(p.y_px, r.y_px) - epsilon <= q.y_px <= max(p.y_px, r.y_px) + epsilon
        )

    o1 = _orientation(a1, a2, b1)
    o2 = _orientation(a1, a2, b2)
    o3 = _orientation(b1, b2, a1)
    o4 = _orientation(b1, b2, a2)

    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and _on_segment(a1, b1, a2):
        return True
    if o2 == 0 and _on_segment(a1, b2, a2):
        return True
    if o3 == 0 and _on_segment(b1, a1, b2):
        return True
    if o4 == 0 and _on_segment(b1, a2, b2):
        return True
    return False


def _edge_geometry_metrics(result: LayoutResult) -> tuple[int, float]:
    total_bends = 0
    total_edge_length_px = 0.0
    for path in result.edge_paths.values():
        point_count = len(path.points)
        if point_count >= 3:
            total_bends += point_count - 2
        for index in range(point_count - 1):
            start = path.points[index]
            end = path.points[index + 1]
            total_edge_length_px += math.hypot(
                end.x_px - start.x_px, end.y_px - start.y_px
            )
    return total_bends, total_edge_length_px


def _edge_tail_metrics(result: LayoutResult) -> tuple[float, float]:
    bends: list[float] = []
    lengths: list[float] = []
    for path in result.edge_paths.values():
        bends.append(float(max(len(path.points) - 2, 0)))
        length = 0.0
        for index in range(len(path.points) - 1):
            start = path.points[index]
            end = path.points[index + 1]
            length += math.hypot(end.x_px - start.x_px, end.y_px - start.y_px)
        lengths.append(length)
    return _percentile(bends, 0.95), _percentile(lengths, 0.95)


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile
    lower = int(math.floor(rank))
    upper = int(math.ceil(rank))
    if lower == upper:
        return ordered[lower]
    ratio = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * ratio


def _weighted_edge_crossings(result: LayoutResult) -> float:
    paths = sorted(
        result.edge_paths.values(),
        key=lambda current: (current.edge[0], current.edge[1]),
    )
    total = 0.0
    for index, left in enumerate(paths):
        left_segments = list(_path_segments(left.points))
        left_nodes = set(left.edge)
        for right in paths[index + 1 :]:
            if left_nodes.intersection(right.edge):
                continue
            right_segments = list(_path_segments(right.points))
            crosses = any(
                _segments_cross_strict(l_start, l_end, r_start, r_end)
                for l_start, l_end in left_segments
                for r_start, r_end in right_segments
            )
            if crosses:
                if left.is_rework or right.is_rework:
                    total += 2.0
                else:
                    total += 1.0
    return total


def _path_segments(
    points: tuple[LayoutPoint, ...],
) -> Iterator[tuple[LayoutPoint, LayoutPoint]]:
    for index in range(len(points) - 1):
        yield points[index], points[index + 1]


def _segments_cross_strict(
    a1: LayoutPoint,
    a2: LayoutPoint,
    b1: LayoutPoint,
    b2: LayoutPoint,
    *,
    epsilon: float = 1e-9,
) -> bool:
    def _orientation(p: LayoutPoint, q: LayoutPoint, r: LayoutPoint) -> float:
        return ((q.y_px - p.y_px) * (r.x_px - q.x_px)) - (
            (q.x_px - p.x_px) * (r.y_px - q.y_px)
        )

    o1 = _orientation(a1, a2, b1)
    o2 = _orientation(a1, a2, b2)
    o3 = _orientation(b1, b2, a1)
    o4 = _orientation(b1, b2, a2)

    return ((o1 > epsilon and o2 < -epsilon) or (o1 < -epsilon and o2 > epsilon)) and (
        (o3 > epsilon and o4 < -epsilon) or (o3 < -epsilon and o4 > epsilon)
    )


@contextmanager
def _strategy_environment(strategy: Strategy) -> Iterator[None]:
    updates = {
        ENV_PARTITION_MODE: strategy.partition_mode,
        ENV_PORT_CONSTRAINTS: strategy.port_constraints,
        ENV_HELPER_ANCHORS: strategy.helper_anchors,
        ENV_SPACING_PROFILE: strategy.spacing_profile,
    }
    previous = {name: os.environ.get(name) for name in updates}
    os.environ.update(updates)
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _request_and_result(
    case: dict[str, Any],
) -> tuple[ElkLayoutRequest, LayoutResult, RenderOptions]:
    source_path = _resolve_path(Path(str(case["input"])))
    model = parse_adapter(
        source_path.read_text(encoding="utf-8"),
        source_path=str(source_path),
    )
    options_map = {"diagram": "sppm", **dict(case.get("options", {}))}
    options = RenderOptions.from_mapping(options_map)
    request = build_sppm_elk_layout_request(model, options=options)
    result = execute_elk_layout(request, engine=run_elkjs_layout)
    return request, result, options


def _major_center(bounds: LayoutBounds, direction: str) -> float:
    return (
        bounds.y_px + (bounds.height_px / 2.0)
        if direction == "DOWN"
        else bounds.x_px + (bounds.width_px / 2.0)
    )


def _cross_center(bounds: LayoutBounds, direction: str) -> float:
    return (
        bounds.x_px + (bounds.width_px / 2.0)
        if direction == "DOWN"
        else bounds.y_px + (bounds.height_px / 2.0)
    )


def _mainline_node_ids(request: ElkLayoutRequest) -> set[str]:
    return {node.id for node in request.nodes} - _rework_node_ids(request)


def _rework_node_ids(request: ElkLayoutRequest) -> set[str]:
    branch_targets = {
        edge.target_id for edge in request.edges if edge.rework_variant == "branch"
    }
    return_sources = {
        edge.source_id for edge in request.edges if edge.rework_variant == "return"
    }
    adjacency: dict[str, list[str]] = {node.id: [] for node in request.nodes}
    for edge in request.edges:
        if edge.is_rework:
            continue
        if edge.source_id in adjacency:
            adjacency[edge.source_id].append(edge.target_id)

    rework: set[str] = set()
    frontier = list(branch_targets)
    while frontier:
        current = frontier.pop()
        if current in rework:
            continue
        rework.add(current)
        if current in return_sources:
            continue
        for nxt in adjacency.get(current, []):
            if nxt not in rework:
                frontier.append(nxt)
    return rework


def _interval_distance(value: float, lower: float, upper: float) -> float:
    if value < lower:
        return lower - value
    if value > upper:
        return value - upper
    return 0.0


def _distance_to_side(
    point: LayoutPoint, bounds: LayoutBounds, side: str | None
) -> float:
    if side == "NORTH":
        return abs(point.y_px - bounds.y_px) + _interval_distance(
            point.x_px,
            bounds.x_px,
            bounds.x_px + bounds.width_px,
        )
    if side == "SOUTH":
        y = bounds.y_px + bounds.height_px
        return abs(point.y_px - y) + _interval_distance(
            point.x_px,
            bounds.x_px,
            bounds.x_px + bounds.width_px,
        )
    if side == "WEST":
        return abs(point.x_px - bounds.x_px) + _interval_distance(
            point.y_px,
            bounds.y_px,
            bounds.y_px + bounds.height_px,
        )
    if side == "EAST":
        x = bounds.x_px + bounds.width_px
        return abs(point.x_px - x) + _interval_distance(
            point.y_px,
            bounds.y_px,
            bounds.y_px + bounds.height_px,
        )
    return 0.0


def _invariant_mainline_progress(
    request: ElkLayoutRequest,
    result: LayoutResult,
    *,
    min_major_step_px: float = 20.0,
) -> list[str]:
    failures: list[str] = []
    mainline = _mainline_node_ids(request)
    node_by_id = {node.id: node for node in request.nodes}
    for edge in request.edges:
        if edge.is_rework:
            continue
        if edge.source_id not in mainline or edge.target_id not in mainline:
            continue
        source_node = node_by_id.get(edge.source_id)
        target_node = node_by_id.get(edge.target_id)
        if source_node is None or target_node is None:
            continue
        if source_node.partition_index is None or target_node.partition_index is None:
            continue
        if target_node.partition_index <= source_node.partition_index:
            continue
        source_bounds = result.bounds_for(edge.source_id)
        target_bounds = result.bounds_for(edge.target_id)
        if source_bounds is None or target_bounds is None:
            continue
        delta = _major_center(target_bounds, request.direction) - _major_center(
            source_bounds,
            request.direction,
        )
        if abs(delta) < min_major_step_px:
            failures.append(
                "mainline_progress "
                f"edge={edge.source_id}->{edge.target_id} "
                f"partition={source_node.partition_index}->{target_node.partition_index} "
                f"delta_major={delta:.2f}"
            )
    return failures


def _invariant_rework_separation(
    request: ElkLayoutRequest,
    result: LayoutResult,
    *,
    min_cross_separation_px: float = 40.0,
) -> list[str]:
    rework = _rework_node_ids(request)
    if not rework:
        return []
    mainline = _mainline_node_ids(request)
    if not mainline:
        return []

    rework_cross = [
        _cross_center(bounds, request.direction)
        for node_id in sorted(rework)
        if (bounds := result.bounds_for(node_id)) is not None
    ]
    mainline_cross = [
        _cross_center(bounds, request.direction)
        for node_id in sorted(mainline)
        if (bounds := result.bounds_for(node_id)) is not None
    ]
    if not rework_cross or not mainline_cross:
        return []

    delta = abs(fmean(rework_cross) - fmean(mainline_cross))
    if delta < min_cross_separation_px:
        return [
            "rework_separation "
            f"cross_delta={delta:.2f} "
            f"min_required={min_cross_separation_px:.2f}"
        ]
    return []


def _invariant_rework_attachments(
    request: ElkLayoutRequest,
    result: LayoutResult,
    *,
    max_side_distance_px: float = 8.0,
) -> list[str]:
    failures: list[str] = []
    for edge in request.edges:
        if edge.rework_variant not in {"branch", "return"}:
            continue
        path = result.path_for(edge.source_id, edge.target_id)
        if path is None or not path.points:
            failures.append(
                f"rework_attachment edge={edge.source_id}->{edge.target_id} missing-path"
            )
            continue
        source_bounds = result.bounds_for(edge.source_id)
        target_bounds = result.bounds_for(edge.target_id)
        if source_bounds is None or target_bounds is None:
            continue
        source_side = path.source_port_side or edge.source_port_side
        target_side = path.target_port_side or edge.target_port_side
        source_distance = _distance_to_side(path.points[0], source_bounds, source_side)
        target_distance = _distance_to_side(path.points[-1], target_bounds, target_side)
        if source_distance > max_side_distance_px:
            failures.append(
                "rework_attachment "
                f"edge={edge.source_id}->{edge.target_id} "
                f"source_side={source_side} distance={source_distance:.2f}"
            )
        if target_distance > max_side_distance_px:
            failures.append(
                "rework_attachment "
                f"edge={edge.source_id}->{edge.target_id} "
                f"target_side={target_side} distance={target_distance:.2f}"
            )
    return failures


def _evaluation_json(evaluation: StrategyEvaluation) -> dict[str, Any]:
    return {
        "strategy": asdict(evaluation.strategy),
        "strategy_id": evaluation.strategy.id,
        "total_cases": evaluation.total_cases,
        "passed_cases": evaluation.passed_cases,
        "failed_cases": evaluation.failed_cases,
        "total_failures": evaluation.total_failures,
        "secondary": {
            "avg_weighted_crossings": round(evaluation.avg_weighted_crossings, 4),
            "avg_p95_bends": round(evaluation.avg_p95_bends, 4),
            "avg_p95_edge_length_px": round(evaluation.avg_p95_edge_length_px, 4),
            "avg_bends": round(evaluation.avg_bends, 4),
            "avg_edge_length_px": round(evaluation.avg_edge_length_px, 4),
            "avg_canvas_area_px2": round(evaluation.avg_canvas_area_px2, 4),
            "avg_diagnostic_warning_count": round(
                evaluation.avg_diagnostic_warning_count, 4
            ),
            "avg_diagnostic_error_count": round(
                evaluation.avg_diagnostic_error_count, 4
            ),
            "avg_diagnostic_warning_burden": round(
                evaluation.avg_diagnostic_warning_burden, 4
            ),
            "partial_output_cases": evaluation.partial_output_cases,
        },
        "case_results": [
            {
                "case_id": case_result.case_id,
                "passed": case_result.passed,
                "failures": list(case_result.failures),
                "determinism_hash": case_result.determinism_hash,
                "secondary": {
                    "weighted_crossings": round(case_result.weighted_crossings, 4),
                    "p95_bends": round(case_result.p95_bends, 4),
                    "p95_edge_length_px": round(case_result.p95_edge_length_px, 4),
                    "total_bends": case_result.total_bends,
                    "total_edge_length_px": round(case_result.total_edge_length_px, 4),
                    "canvas_area_px2": round(case_result.canvas_area_px2, 4),
                    "diagnostic_warning_count": case_result.diagnostic_warning_count,
                    "diagnostic_error_count": case_result.diagnostic_error_count,
                    "diagnostic_warning_burden": round(
                        case_result.diagnostic_warning_burden, 4
                    ),
                    "partial_output": case_result.partial_output,
                },
            }
            for case_result in evaluation.case_results
        ],
    }


def _scoreboard_markdown(evaluations: list[StrategyEvaluation]) -> str:
    lines = [
        "# SPPM Strategy Matrix Scoreboard",
        "",
        "| Rank | Strategy | Passed Cases | Failed Cases | Invariant Failures | Avg Diag Warning Burden | Avg Diag Warnings | Partial Output Cases | Avg Weighted Crossings | Avg P95 Bends | Avg P95 Edge Length (px) | Avg Bends | Avg Edge Length (px) | Avg Canvas Area (px^2) |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for rank, evaluation in enumerate(evaluations, start=1):
        lines.append(
            "| "
            f"{rank} | {evaluation.strategy.id} | {evaluation.passed_cases}/{evaluation.total_cases} | "
            f"{evaluation.failed_cases} | {evaluation.total_failures} | "
            f"{evaluation.avg_diagnostic_warning_burden:.2f} | "
            f"{evaluation.avg_diagnostic_warning_count:.2f} | "
            f"{evaluation.partial_output_cases} | "
            f"{evaluation.avg_weighted_crossings:.2f} | {evaluation.avg_p95_bends:.2f} | "
            f"{evaluation.avg_p95_edge_length_px:.2f} | "
            f"{evaluation.avg_bends:.2f} | {evaluation.avg_edge_length_px:.2f} | "
            f"{evaluation.avg_canvas_area_px2:.2f} |"
        )
    lines.append("")
    lines.append("## Top Strategy Details")
    top = evaluations[0]
    lines.append("")
    lines.append(f"- Strategy: `{top.strategy.id}`")
    lines.append(
        f"- Result: {top.passed_cases}/{top.total_cases} cases passed with {top.total_failures} invariant failures"
    )
    lines.append(
        "- Secondary score: "
        f"avg_diag_warning_burden={top.avg_diagnostic_warning_burden:.2f}, "
        f"avg_diag_warnings={top.avg_diagnostic_warning_count:.2f}, "
        f"partial_output_cases={top.partial_output_cases}, "
        f"avg_weighted_crossings={top.avg_weighted_crossings:.2f}, "
        f"avg_p95_bends={top.avg_p95_bends:.2f}, "
        f"avg_p95_edge_length_px={top.avg_p95_edge_length_px:.2f}, "
        f"avg_bends={top.avg_bends:.2f}, "
        f"avg_edge_length_px={top.avg_edge_length_px:.2f}, "
        f"avg_canvas_area_px2={top.avg_canvas_area_px2:.2f}"
    )
    lines.append("")
    lines.append("## Notes")
    lines.append(
        "- Invariants scored: diagnostic error exclusion, partial-output exclusion, mainline progression, rework row separation, rework attachment sides, determinism hash stability, node overlap exclusion, lane containment, and edge-through-node exclusion."
    )
    lines.append(
        "- Secondary metrics scored: diagnostic warning burden, diagnostic warning counts, weighted edge crossings, p95 bends, p95 edge length, average bends, total routed edge length, and canvas area."
    )
    lines.append(
        "- Tie-break order: invariant pass rate, invariant failure count, avg diagnostic warning burden, avg diagnostic warnings, avg weighted crossings, avg p95 bends, avg p95 edge length, avg bends, avg edge length, avg canvas area, strategy ID."
    )
    lines.append(
        "- Strategy dimensions: partition mode, port constraints, helper anchors, spacing profile."
    )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
