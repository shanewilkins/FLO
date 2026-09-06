from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from flo.process.analysis import analyze_process_timing
from flo.process.ir.models import IR, Edge, Node
from flo.process.ir.validate import validate_ir
from flo.source import compile_adapter, parse_adapter

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _timed_task(node_id: str, seconds: float) -> Node:
    return Node(
        id=node_id,
        type="task",
        attrs={"metadata": {"cycle_time": {"value": seconds, "unit": "s"}}},
    )


def test_washnfold_timing_has_complete_single_path_lead_time() -> None:
    source_path = _REPO_ROOT / "examples" / "reference" / "washnfold.flo"
    adapter = parse_adapter(
        source_path.read_text(encoding="utf-8"),
        source_path=str(source_path),
    )
    process = compile_adapter(adapter)
    validate_ir(process)

    result = analyze_process_timing(process)

    assert result.timing_complete is True
    assert result.process_id == "wash_n_fold"
    assert result.process_name == "Wash n' Fold"
    assert result.declared_totals.cycle_time_seconds == 105 * 60
    assert result.declared_totals.wait_time_seconds == 95 * 60
    assert result.declared_totals.changeover_time_seconds == 0
    assert result.modeled_lead_time_seconds == 200 * 60
    assert result.minimum_path_lead_time_seconds == 200 * 60
    assert result.maximum_path_lead_time_seconds == 200 * 60
    assert len(result.paths) == 1
    assert result.diagnostics == ()


def test_timing_normalizes_units_and_preserves_changeover_source() -> None:
    process = IR(
        name="mixed units",
        nodes=[
            Node(id="start", type="start"),
            Node(
                id="work",
                type="task",
                attrs={
                    "metadata": {
                        "cycle_time": {"value": 0.5, "unit": "min"},
                        "changeover_time": {"value": 30, "unit": "s"},
                    }
                },
            ),
            Node(
                id="queue",
                type="queue",
                attrs={"metadata": {"wait_time": {"value": 0.25, "unit": "hr"}}},
            ),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="work"),
            Edge(source="work", target="queue"),
            Edge(source="queue", target="end"),
        ],
    )
    validate_ir(process)

    result = analyze_process_timing(process)

    assert result.declared_totals.as_dict() == {
        "cycle_time_seconds": 30.0,
        "wait_time_seconds": 900.0,
        "changeover_time_seconds": 30.0,
        "elapsed_time_seconds": 960.0,
    }
    work = next(timing for timing in result.node_timings if timing.node_id == "work")
    assert work.changeover_source_field == "changeover_time"
    assert result.modeled_lead_time_seconds == 960.0


@pytest.mark.parametrize(
    ("value", "unit", "expected_seconds"),
    [
        (2, "s", 2.0),
        (2, "m", 120.0),
        (2, "min", 120.0),
        (2, "hr", 7200.0),
        (2, "d", 172800.0),
    ],
)
def test_timing_normalizes_every_supported_unit(
    value: int,
    unit: str,
    expected_seconds: float,
) -> None:
    process = IR(
        name="units",
        nodes=[
            Node(id="start", type="start"),
            Node(
                id="work",
                type="task",
                attrs={"metadata": {"cycle_time": {"value": value, "unit": unit}}},
            ),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="work"),
            Edge(source="work", target="end"),
        ],
    )

    assert analyze_process_timing(process).modeled_lead_time_seconds == expected_seconds


def test_branching_process_reports_deterministic_path_range() -> None:
    process = IR(
        name="branch",
        nodes=[
            Node(id="start", type="start"),
            Node(id="choice", type="decision"),
            _timed_task("fast", 30),
            _timed_task("slow", 90),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="choice"),
            Edge(source="choice", target="slow", outcome="slow"),
            Edge(source="choice", target="fast", outcome="fast"),
            Edge(source="slow", target="end"),
            Edge(source="fast", target="end"),
        ],
    )
    validate_ir(process)

    result = analyze_process_timing(process)

    assert [path.node_ids for path in result.paths] == [
        ("start", "choice", "fast", "end"),
        ("start", "choice", "slow", "end"),
    ]
    assert result.modeled_lead_time_seconds is None
    assert result.minimum_path_lead_time_seconds == 30
    assert result.maximum_path_lead_time_seconds == 90
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "timing-multiple-paths"
    ]


def test_cycle_refuses_to_guess_iteration_count() -> None:
    process = IR(
        name="cycle",
        nodes=[
            Node(id="start", type="start"),
            _timed_task("work", 60),
            Node(id="choice", type="decision"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="work"),
            Edge(source="work", target="choice"),
            Edge(source="choice", target="end", outcome="done"),
            Edge(source="choice", target="work", outcome="repeat", rework=True),
        ],
    )
    validate_ir(process)

    result = analyze_process_timing(process)

    assert result.paths == ()
    assert result.modeled_lead_time_seconds is None
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "timing-cycle-unsupported"
    ]


def test_missing_expected_timing_marks_path_incomplete() -> None:
    process = IR(
        name="partial",
        nodes=[
            Node(id="start", type="start"),
            Node(id="work", type="task"),
            Node(
                id="queue",
                type="queue",
                attrs={"metadata": {"wait_time": {"value": 2, "unit": "min"}}},
            ),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="work"),
            Edge(source="work", target="queue"),
            Edge(source="queue", target="end"),
        ],
    )
    validate_ir(process)

    result = analyze_process_timing(process)

    assert result.timing_complete is False
    assert result.missing_timing_node_ids == ("work",)
    assert result.paths[0].complete is False
    assert result.paths[0].totals.wait_time_seconds == 120
    assert result.modeled_lead_time_seconds is None
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "timing-incomplete"
    ]


def test_ambiguous_changeover_aliases_use_documented_precedence() -> None:
    process = IR(
        name="aliases",
        nodes=[
            Node(id="start", type="start"),
            Node(
                id="work",
                type="task",
                attrs={
                    "metadata": {
                        "cycle_time": {"value": 1, "unit": "min"},
                        "crossover_time": {"value": 2, "unit": "min"},
                        "changeover_time": {"value": 5, "unit": "min"},
                    }
                },
            ),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="work"),
            Edge(source="work", target="end"),
        ],
    )
    validate_ir(process)

    result = analyze_process_timing(process)

    assert result.declared_totals.changeover_time_seconds == 120
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "timing-ambiguous-changeover-fields"
    ]


def test_parallel_flow_is_explicitly_deferred() -> None:
    process = IR(
        name="parallel",
        nodes=[
            Node(id="start", type="start"),
            Node(id="split", type="parallel_split"),
            _timed_task("a", 10),
            _timed_task("b", 20),
            Node(id="join", type="parallel_join"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="split"),
            Edge(source="split", target="a"),
            Edge(source="split", target="b"),
            Edge(source="a", target="join"),
            Edge(source="b", target="join"),
            Edge(source="join", target="end"),
        ],
    )

    result = analyze_process_timing(process)

    assert result.paths == ()
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "timing-parallel-flow-unsupported"
    ]


def test_path_enumeration_limit_refuses_partial_range() -> None:
    nodes = [Node(id="start", type="start")]
    edges: list[Edge] = []
    previous_exits = ["start"]
    for index in range(9):
        decision_id = f"decision_{index}"
        left_id = f"branch_{index}_a"
        right_id = f"branch_{index}_b"
        nodes.extend(
            [
                Node(id=decision_id, type="decision"),
                _timed_task(left_id, 1),
                _timed_task(right_id, 1),
            ]
        )
        edges.extend(
            Edge(source=source_id, target=decision_id) for source_id in previous_exits
        )
        edges.extend(
            [
                Edge(source=decision_id, target=left_id, outcome="a"),
                Edge(source=decision_id, target=right_id, outcome="b"),
            ]
        )
        previous_exits = [left_id, right_id]

    nodes.append(Node(id="end", type="end"))
    edges.extend(Edge(source=source_id, target="end") for source_id in previous_exits)
    process = IR(name="many paths", nodes=nodes, edges=edges)

    result = analyze_process_timing(process)

    assert result.paths == ()
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "timing-path-limit"
    ]


def test_malformed_timing_is_diagnostic_and_incomplete() -> None:
    process = IR(
        name="invalid timing",
        nodes=[
            Node(id="start", type="start"),
            Node(
                id="work",
                type="task",
                attrs={"metadata": {"cycle_time": {"value": "soon", "unit": "min"}}},
            ),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="work"),
            Edge(source="work", target="end"),
        ],
    )

    result = analyze_process_timing(process)

    assert result.timing_complete is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "timing-invalid-duration",
        "timing-incomplete",
    ]


def test_analysis_shape_is_json_compatible_and_input_must_be_ir() -> None:
    process = IR(
        name="shape",
        process_version=2,
        nodes=[Node(id="start", type="start"), Node(id="end", type="end")],
        edges=[Edge(source="start", target="end")],
    )

    original = deepcopy(process)
    payload = analyze_process_timing(process).as_dict()

    assert payload["analysis_version"] == "0.1"
    assert payload["process"] == {"id": "shape", "name": "shape", "version": 2}
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload
    assert process == original
    with pytest.raises(TypeError, match="canonical IR"):
        analyze_process_timing({})  # type: ignore[arg-type]
