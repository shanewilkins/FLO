import pytest

from flo.render.sppm.metadata import (
    SppmMetadataValue,
    get_metadata_crossover_time,
    get_metadata_cycle_time,
    get_metadata_wait_time_minutes,
)


def test_wait_before_takes_precedence_for_work_node_display() -> None:
    metadata = {
        "wait_before": {"value": 7.5, "unit": "min"},
        "wait_time": {"value": 99, "unit": "min"},
    }

    assert get_metadata_wait_time_minutes(metadata) == 7.5


def test_queue_wait_time_remains_available_for_display() -> None:
    assert (
        get_metadata_wait_time_minutes({"wait_time": {"value": 0, "unit": "min"}}) == 0
    )


@pytest.mark.parametrize(
    "value", [None, True, -1, "0", float("nan"), float("inf"), 10**400]
)
def test_invalid_timing_accessors_never_invent_zero(value):
    duration = {"value": value, "unit": "min"}
    assert get_metadata_cycle_time({"cycle_time": duration}) is None
    assert get_metadata_wait_time_minutes({"wait_time": duration}) is None
    assert SppmMetadataValue(value, "min").numeric_value is None


def test_invalid_higher_precedence_timing_is_not_replaced_by_an_alias():
    metadata = {
        "crossover_time": {"value": None, "unit": "min"},
        "changeover_time": {"value": 5, "unit": "min"},
    }
    assert get_metadata_crossover_time(metadata) is None
    assert (
        get_metadata_wait_time_minutes(
            {"wait_before": None, "wait_time": {"value": 5, "unit": "min"}}
        )
        is None
    )


def test_missing_unit_is_not_invented_by_accessors():
    assert get_metadata_cycle_time({"cycle_time": {"value": 0}}) is None
    assert get_metadata_wait_time_minutes({"wait_time": {"value": 0}}) is None
    assert SppmMetadataValue(0).numeric_value is None
