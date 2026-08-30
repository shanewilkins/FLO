from __future__ import annotations

from copy import deepcopy

import pytest

from flo.process.analysis import analyze_process_structure
from flo.process.ir._internal_shape import ir_to_internal_dict
from flo.process.ir.models import Edge, IR, Node


def test_structure_reports_handoffs_paths_and_step_classification() -> None:
    process = _branched_process()
    before = deepcopy(ir_to_internal_dict(process))

    result = analyze_process_structure(process)
    payload = result.as_dict()

    assert payload["analysis_version"] == "0.1"
    assert payload["process"] == {
        "id": "claims",
        "name": "Claims",
        "version": 3,
    }
    assert [finding.as_dict() for finding in result.handoffs] == [
        {
            "source_id": "review",
            "target_id": "route",
            "classification": "explicit",
            "edge_id": "handoff-review",
            "handoff_type": "responsibility",
            "source_lane": "intake",
            "target_lane": "intake",
        }
    ]
    assert [finding.as_dict() for finding in result.handoff_candidates] == [
        {
            "source_id": "route",
            "target_id": "approve",
            "classification": "candidate",
            "edge_id": None,
            "handoff_type": None,
            "source_lane": "intake",
            "target_lane": "quality",
        }
    ]
    assert [path.node_ids for path in result.paths] == [
        ("start", "review", "route", "approve", "end"),
        ("start", "review", "route", "reject", "end"),
    ]
    assert payload["path_summary"] == {
        "path_count": 2,
        "minimum_edge_count": 4,
        "maximum_edge_count": 4,
    }
    assert result.node_type_counts == {
        "decision": 1,
        "end": 1,
        "start": 1,
        "subprocess": 1,
        "task": 2,
    }
    assert result.value_class_counts == {"NVA": 1, "RNVA": 1, "VA": 1}
    assert result.unclassified_node_ids == ()
    assert ir_to_internal_dict(process) == before


def test_structure_separates_explicit_and_inferred_rework() -> None:
    process = IR(
        name="Rework",
        nodes=[
            Node(id="start", type="start"),
            Node(id="review", type="task"),
            Node(id="fix", type="task"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="review"),
            Edge(source="review", target="end"),
            Edge(
                id="branch",
                source="review",
                target="fix",
                rework=True,
                metadata={"rate": 0.2, "reason": "Incomplete"},
            ),
            Edge(id="return", source="fix", target="review"),
        ],
    )

    result = analyze_process_structure(process)

    assert [finding.classification for finding in result.rework_edges] == [
        "inferred",
        "explicit",
    ]
    assert result.rework_edges[1].rate == 0.2
    assert result.rework_edges[1].reason == "Incomplete"
    assert [path.node_ids for path in result.paths] == [("start", "review", "end")]
    assert "structure-inferred-rework" in _diagnostic_codes(result)


@pytest.mark.parametrize(
    "back_edge",
    [
        Edge(source="work", target="start", rework=False),
        Edge(source="work", target="start", edge_type="sequence"),
    ],
)
def test_explicit_ordinary_back_edge_suppresses_rework_inference(
    back_edge: Edge,
) -> None:
    process = IR(
        name="Ordinary cycle",
        nodes=[
            Node(id="start", type="start"),
            Node(id="work", type="task"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="work"),
            Edge(source="work", target="end"),
            back_edge,
        ],
    )

    result = analyze_process_structure(process)

    assert result.rework_edges == ()
    assert result.paths == ()
    assert "structure-cycle-unsupported" in _diagnostic_codes(result)
    assert "structure-inferred-rework" not in _diagnostic_codes(result)


def test_explicit_false_handoff_suppresses_lane_change_candidate() -> None:
    process = IR(
        name="No handoff",
        nodes=[
            Node(id="start", type="start", attrs={"lane": "a"}),
            Node(id="end", type="end", attrs={"lane": "b"}),
        ],
        edges=[Edge(source="start", target="end", handoff=False)],
    )

    result = analyze_process_structure(process)

    assert result.handoffs == ()
    assert result.handoff_candidates == ()
    assert "structure-unmarked-lane-change" not in _diagnostic_codes(result)


def test_parallel_flow_keeps_findings_but_refuses_path_length() -> None:
    process = IR(
        name="Parallel",
        nodes=[
            Node(id="start", type="start"),
            Node(id="split", type="parallel_split"),
            Node(id="join", type="parallel_join"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="split"),
            Edge(source="split", target="join", handoff=True),
            Edge(source="join", target="end"),
        ],
    )

    result = analyze_process_structure(process)

    assert len(result.handoffs) == 1
    assert result.paths == ()
    assert "structure-parallel-paths-unsupported" in _diagnostic_codes(result)


def test_path_enumeration_is_bounded() -> None:
    process = _many_path_process(level_count=9)

    result = analyze_process_structure(process)

    assert result.paths == ()
    assert "structure-path-limit" in _diagnostic_codes(result)


def test_structure_requires_canonical_ir() -> None:
    with pytest.raises(TypeError, match="requires canonical IR"):
        analyze_process_structure({})  # type: ignore[arg-type]


def _branched_process() -> IR:
    return IR(
        name="Claims",
        process_version=3,
        process_metadata={"process_id": "claims", "process_name": "Claims"},
        nodes=[
            Node(id="start", type="start", attrs={"lane": "intake"}),
            Node(
                id="review",
                type="task",
                attrs={"lane": "intake", "metadata": {"value_class": "VA"}},
            ),
            Node(id="route", type="decision", attrs={"lane": "intake"}),
            Node(
                id="approve",
                type="subprocess",
                attrs={"lane": "quality", "metadata": {"value_class": "RNVA"}},
            ),
            Node(
                id="reject",
                type="task",
                attrs={"lane": "intake", "metadata": {"value_class": "NVA"}},
            ),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="review"),
            Edge(
                id="handoff-review",
                source="review",
                target="route",
                handoff=True,
                metadata={"handoff_type": "responsibility"},
            ),
            Edge(source="route", target="approve", outcome="yes"),
            Edge(source="approve", target="end"),
            Edge(source="route", target="reject", outcome="no"),
            Edge(source="reject", target="end"),
        ],
    )


def _many_path_process(*, level_count: int) -> IR:
    nodes = [Node(id="start", type="start")]
    edges: list[Edge] = []
    previous_ids = ["start"]
    for level in range(level_count):
        current_ids = [f"level_{level}_a", f"level_{level}_b"]
        nodes.extend(Node(id=node_id, type="task") for node_id in current_ids)
        edges.extend(
            Edge(source=source_id, target=target_id)
            for source_id in previous_ids
            for target_id in current_ids
        )
        previous_ids = current_ids
    nodes.append(Node(id="end", type="end"))
    edges.extend(Edge(source=source_id, target="end") for source_id in previous_ids)
    return IR(name="Many paths", nodes=nodes, edges=edges)


def _diagnostic_codes(result) -> set[str]:
    return {diagnostic.code for diagnostic in result.diagnostics}
