from flo.render.sppm.metadata import get_metadata_wait_time_minutes


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
