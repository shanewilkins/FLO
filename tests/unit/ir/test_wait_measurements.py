"""Repeated waiting evidence is equivalent, additive, and finite."""

from itertools import pairwise
from math import inf, nextafter

import pytest

from flo.errors import ValidationError
from flo.process.ir.models import IR, Edge, Node
from flo.process.ir.validate import validate_ir


def _process(queue_wait, waits):
    nodes = [
        Node("start", "start"),
        Node("queue", "queue", {"metadata": {"wait_time": queue_wait}}),
    ]
    nodes.extend(
        Node(
            f"work{index}",
            "task",
            {
                "metadata": {
                    "cycle_time": {"value": 1, "unit": "s"},
                    "wait_before": wait,
                }
            },
        )
        for index, wait in enumerate(waits)
    )
    nodes.append(Node("end", "end"))
    return IR("Evidence", nodes, [Edge(a.id, b.id) for a, b in pairwise(nodes)])


@pytest.mark.parametrize(
    "unit,value", [("s", 60), ("min", 1), ("m", 1), ("hr", 1 / 60), ("d", 1 / 1440)]
)
def test_shared_measurement_accepts_equivalent_units(unit, value):
    process = _process(
        {"value": value, "unit": unit, "measurement_id": "same"},
        [{"value": 60, "unit": "s", "measurement_id": "same"}],
    )
    validate_ir(process)


@pytest.mark.parametrize("queue_value,work_value", [(100, 1), (0, 1e-300), (1e-300, 0)])
def test_shared_measurement_rejects_unequal_amounts(queue_value, work_value):
    process = _process(
        {"value": queue_value, "unit": "min", "measurement_id": "same"},
        [{"value": work_value, "unit": "min", "measurement_id": "same"}],
    )
    with pytest.raises(ValidationError, match="E1509"):
        validate_ir(process)


def test_zero_is_a_valid_repeated_measurement():
    validate_ir(
        _process(
            {"value": 0, "unit": "hr", "measurement_id": "same"},
            [{"value": 0, "unit": "s", "measurement_id": "same"}],
        )
    )


@pytest.mark.parametrize("aggregate", [False, True])
def test_equivalence_uses_exact_relative_tolerance_boundary(aggregate):
    boundary = 1 - 1e-9
    accepted = nextafter(boundary, inf)
    rejected = nextafter(boundary, -inf)
    link = {"measurement_refs": ["same"]} if aggregate else {"measurement_id": "same"}
    waits = [{"value": 1, "unit": "s", "measurement_id": "same"}]
    validate_ir(_process({"value": accepted, "unit": "s", **link}, waits))
    with pytest.raises(ValidationError, match="E1510" if aggregate else "E1509"):
        validate_ir(_process({"value": rejected, "unit": "s", **link}, waits))


def test_aggregate_is_the_sum_of_distinct_normalized_measurements():
    waits = [
        {"value": 1, "unit": "min", "measurement_id": "one"},
        {"value": 30, "unit": "s", "measurement_id": "two"},
    ]
    validate_ir(
        _process(
            {"value": 1.5, "unit": "min", "measurement_refs": ["one", "two"]}, waits
        )
    )
    with pytest.raises(ValidationError, match="E1510"):
        validate_ir(
            _process(
                {"value": 2, "unit": "min", "measurement_refs": ["one", "two"]}, waits
            )
        )


def test_duplicate_references_are_rejected_after_whitespace_normalization():
    with pytest.raises(ValidationError, match="E1305"):
        validate_ir(
            _process(
                {"value": 2, "unit": "s", "measurement_refs": ["one", " one "]},
                [{"value": 1, "unit": "s", "measurement_id": "one"}],
            )
        )


def test_aggregate_overflow_is_a_validation_error():
    with pytest.raises(ValidationError, match=r"E1510.*finite"):
        validate_ir(
            _process(
                {"value": 1e308, "unit": "s", "measurement_refs": ["one", "two"]},
                [
                    {"value": 1e308, "unit": "s", "measurement_id": "one"},
                    {"value": 1e308, "unit": "s", "measurement_id": "two"},
                ],
            )
        )


def test_unknown_reference_is_not_treated_as_zero():
    with pytest.raises(ValidationError, match="E1507"):
        validate_ir(
            _process({"value": 0, "unit": "s", "measurement_refs": ["missing"]}, [])
        )


def test_shared_work_identity_cannot_also_project_a_different_measurement():
    with pytest.raises(ValidationError, match="E1510"):
        validate_ir(
            _process(
                {
                    "value": 1,
                    "unit": "s",
                    "measurement_id": "one",
                    "measurement_refs": ["two"],
                },
                [
                    {"value": 1, "unit": "s", "measurement_id": "one"},
                    {"value": 1, "unit": "s", "measurement_id": "two"},
                ],
            )
        )


def test_repeated_queue_identity_cannot_hide_a_tolerance_chain():
    waits = [1.0, 1.0 + 0.9e-9, 1.0 + 1.8e-9]
    queues = [
        Node(
            f"queue{index}",
            "queue",
            {
                "metadata": {
                    "wait_time": {
                        "value": seconds,
                        "unit": "s",
                        "measurement_id": "same",
                    }
                }
            },
        )
        for index, seconds in enumerate(waits)
    ]
    nodes = [Node("start", "start"), *queues, Node("end", "end")]
    process = IR("Copies", nodes, [Edge(a.id, b.id) for a, b in pairwise(nodes)])
    with pytest.raises(ValidationError, match="E1509"):
        validate_ir(process)
    process.nodes.reverse()
    with pytest.raises(ValidationError, match="E1509"):
        validate_ir(process)


def test_copies_of_an_aggregate_must_agree_on_the_reference_set():
    process = _process(
        {
            "value": 1,
            "unit": "s",
            "measurement_id": "aggregate",
            "measurement_refs": ["one"],
        },
        [
            {"value": 1, "unit": "s", "measurement_id": "one"},
            {"value": 1, "unit": "s", "measurement_id": "two"},
        ],
    )
    duplicate = Node(
        "copy",
        "queue",
        {
            "metadata": {
                "wait_time": {
                    "value": 1,
                    "unit": "s",
                    "measurement_id": "aggregate",
                    "measurement_refs": ["two"],
                }
            }
        },
    )
    process.nodes.insert(2, duplicate)
    process.edges = [Edge(a.id, b.id) for a, b in pairwise(process.nodes)]
    with pytest.raises(ValidationError, match="E1510"):
        validate_ir(process)
