"""Path-local waiting evidence and explicit holds preserve unknown timing."""

from copy import deepcopy

import pytest

from flo.process.analysis import analyze_process_timing, project_value_stream
from flo.process.ir.models import IR, Edge, Node
from flo.process.ir.validate import validate_ir


def _work(node_id, wait):
    return Node(
        node_id,
        "task",
        {
            "metadata": {
                "cycle_time": {"value": 60, "unit": "s"},
                "wait_before": {"value": wait, "unit": "s", "measurement_id": node_id},
                "crossover_time": {"value": 0, "unit": "s"},
            }
        },
    )


def _branching_projection(*, aggregate=False):
    return IR(
        "Branches",
        [
            Node("start", "start"),
            Node(
                "queue",
                "queue",
                {
                    "metadata": {
                        "wait_time": {
                            "value": 900 if aggregate else 600,
                            "unit": "s",
                            "measurement_refs": ["a", "b"] if aggregate else ["a"],
                        }
                    }
                },
            ),
            Node("choice", "decision"),
            _work("a", 600),
            _work("b", 300 if aggregate else 0),
            Node("end", "end"),
        ],
        [
            Edge("start", "queue"),
            Edge("queue", "choice"),
            Edge("choice", "a", outcome="a"),
            Edge("choice", "b", outcome="b"),
            Edge("a", "end"),
            Edge("b", "end"),
        ],
    )


def test_queue_projection_is_not_silently_suppressed_on_an_uncovered_branch():
    process = _branching_projection()
    validate_ir(process)
    before = deepcopy(process)
    result = analyze_process_timing(process)
    covered, uncovered = result.paths
    assert covered.complete and covered.totals.elapsed_time_seconds == 660
    assert not uncovered.complete
    assert uncovered.missing_node_ids == ("queue",)
    assert uncovered.totals.elapsed_time_seconds is None
    assert result.timing_complete is False
    assert result.missing_timing_node_ids == ("queue",)
    assert result.modeled_lead_time_seconds is None
    assert result.minimum_path_lead_time_seconds is None
    assert result.maximum_path_lead_time_seconds is None
    assert process == before


def test_projection_limitation_is_one_stable_warning_per_queue():
    process = _branching_projection(aggregate=True)
    validate_ir(process)
    result = analyze_process_timing(process)
    assert all(not path.complete for path in result.paths)
    warnings = [item for item in result.diagnostics if item.severity == "warning"]
    assert len(warnings) == 1
    assert warnings[0].code == "timing-projection-incomplete"
    assert warnings[0].node_id == "queue" and warnings[0].field == "wait_time"
    process.nodes.reverse()
    process.edges.reverse()
    assert analyze_process_timing(process).as_dict() == result.as_dict()


def test_projection_keeps_the_authored_wait_visible_without_counting_it_again():
    process = _branching_projection()
    result = analyze_process_timing(process)
    queue = next(item for item in result.node_timings if item.node_id == "queue")
    assert queue.declared_wait_time_seconds == 600
    assert queue.totals.wait_time_seconds is None
    projection = project_value_stream(process)
    waits = {item.node_id: item.wait_time_seconds for item in projection.nodes}
    assert waits["queue"] == waits["a"] == 600
    assert waits["b"] == 0
    assert projection.modeled_lead_time_seconds is None


@pytest.mark.parametrize("seconds", [None, 0, 120])
def test_explicit_hold_requires_timing_for_a_complete_lead_time(seconds):
    metadata = {} if seconds is None else {"wait_time": {"value": seconds, "unit": "s"}}
    process = IR(
        "Hold",
        [
            Node("start", "start"),
            _work("work", 0),
            Node("hold", "wait", {"metadata": metadata}),
            Node("end", "end"),
        ],
        [Edge("start", "work"), Edge("work", "hold"), Edge("hold", "end")],
    )
    validate_ir(process)
    result = analyze_process_timing(process)
    assert result.timing_complete is (seconds is not None)
    assert result.modeled_lead_time_seconds == (
        None if seconds is None else 60 + seconds
    )
    assert result.missing_timing_node_ids == (("hold",) if seconds is None else ())
    hold = next(
        item for item in project_value_stream(process).nodes if item.node_id == "hold"
    )
    assert hold.wait_time_seconds == seconds


def test_nonadjacent_shared_measurement_is_still_counted_once():
    process = IR(
        "Nonadjacent",
        [
            Node("start", "start"),
            _work("work", 600),
            Node(
                "queue",
                "queue",
                {
                    "metadata": {
                        "wait_time": {
                            "value": 10,
                            "unit": "min",
                            "measurement_id": "work",
                        }
                    }
                },
            ),
            Node("end", "end"),
        ],
        [Edge("start", "work"), Edge("work", "queue"), Edge("queue", "end")],
    )
    validate_ir(process)
    assert analyze_process_timing(process).modeled_lead_time_seconds == 660


def test_independent_queue_copies_are_deduplicated_on_each_path_not_globally():
    process = IR(
        "Repeated queue",
        [
            Node("start", "start"),
            Node("choice", "decision"),
            Node(
                "a",
                "queue",
                {
                    "metadata": {
                        "wait_time": {
                            "value": 10,
                            "unit": "min",
                            "measurement_id": "same",
                        }
                    }
                },
            ),
            Node(
                "b",
                "queue",
                {
                    "metadata": {
                        "wait_time": {
                            "value": 600,
                            "unit": "s",
                            "measurement_id": "same",
                        }
                    }
                },
            ),
            Node("end", "end"),
        ],
        [
            Edge("start", "choice"),
            Edge("choice", "a", outcome="a"),
            Edge("choice", "b", outcome="b"),
            Edge("a", "end"),
            Edge("b", "end"),
        ],
    )
    validate_ir(process)
    result = analyze_process_timing(process)
    assert result.declared_totals.wait_time_seconds == 600
    assert [path.totals.elapsed_time_seconds for path in result.paths] == [600, 600]
    assert (
        result.minimum_path_lead_time_seconds
        == result.maximum_path_lead_time_seconds
        == 600
    )


def test_copies_of_a_projection_share_its_replacement_evidence():
    wait = {"value": 10, "unit": "min", "measurement_id": "aggregate"}
    nodes = [
        Node("start", "start"),
        Node(
            "queue",
            "queue",
            {"metadata": {"wait_time": {**wait, "measurement_refs": ["work"]}}},
        ),
        Node("copy", "queue", {"metadata": {"wait_time": wait}}),
        _work("work", 600),
        Node("end", "end"),
    ]
    process = IR(
        "Projection copies",
        nodes,
        [
            Edge("start", "queue"),
            Edge("queue", "copy"),
            Edge("copy", "work"),
            Edge("work", "end"),
        ],
    )
    validate_ir(process)
    result = analyze_process_timing(process)
    assert result.modeled_lead_time_seconds == 660
    assert result.declared_totals.wait_time_seconds == 600
