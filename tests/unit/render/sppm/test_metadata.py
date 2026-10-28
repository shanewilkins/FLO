import pytest

from flo.render.sppm.metadata import (
    SppmMetadataValue,
    get_metadata_changeover_time,
    get_metadata_cycle_time,
    get_metadata_wait_time_minutes,
)


def _profile(value, unit="min"):
    return {
        "basis": "observed",
        "results": {"mean": {"method": "mean", "value": value, "unit": unit}},
        "primary": "mean",
        "analysis_input": "mean",
    }


def test_wait_time_primary_result_is_available_for_display() -> None:
    assert get_metadata_wait_time_minutes({"wait_time": _profile(7.5)}) == 7.5


@pytest.mark.parametrize(
    "value", [None, True, -1, "0", float("nan"), float("inf"), 10**400]
)
def test_invalid_timing_accessors_never_invent_zero(value):
    duration = _profile(value)
    assert get_metadata_cycle_time({"cycle_time": duration}) is None
    assert get_metadata_wait_time_minutes({"wait_time": duration}) is None
    assert SppmMetadataValue(value, "min").numeric_value is None


def test_changeover_time_has_one_canonical_field():
    result = get_metadata_changeover_time({"changeover_time": _profile(5)})
    assert result == SppmMetadataValue(5, "min")


def test_missing_unit_is_not_invented_by_accessors():
    profile = _profile(0, unit=None)
    assert get_metadata_cycle_time({"cycle_time": profile}) is None
    assert get_metadata_wait_time_minutes({"wait_time": profile}) is None
    assert SppmMetadataValue(0).numeric_value is None
