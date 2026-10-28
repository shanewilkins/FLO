"""Shared scalar-duration and canonical profile presentation checks."""

import subprocess
import sys
from copy import deepcopy

import pytest

from flo.app.inspect import _format_duration
from flo.process.durations import duration_seconds
from flo.process.units import DURATION_UNITS, convert_duration, length_in_metres
from flo.render.sppm.metadata import get_metadata_wait_time_minutes
from flo.render.sppm.publication_support import _format_timing_seconds
from flo.render.value_stream.renderer import _format_seconds


def _measurement_profile(result):
    return {
        "basis": "observed",
        "results": {
            "mean": {"method": "mean", **result}
            if isinstance(result, dict)
            else result,
        },
        "primary": "mean",
        "analysis_input": "mean",
    }


@pytest.mark.parametrize(
    ("unit", "seconds"),
    [("s", 1), ("m", 60), ("min", 60), ("hr", 3600), ("d", 86400)],
)
@pytest.mark.parametrize("value", [0, 0.0, 0.125, 1, 2.5])
def test_duration_normalization_preserves_values_and_authored_records(
    unit, seconds, value
):
    raw = {"method": "mean", "value": value, "unit": unit}
    before = deepcopy(raw)

    assert duration_seconds(raw) == value * seconds
    assert raw == before
    assert type(raw["value"]) is type(value)


@pytest.mark.parametrize("unit", [" M ", " MIN ", " HR ", " D ", " S "])
def test_duration_unit_case_and_whitespace_remain_accepted(unit):
    normalized = unit.strip().lower()
    assert duration_seconds({"value": 1, "unit": unit}) == duration_seconds(
        {"value": 1, "unit": normalized}
    )


@pytest.mark.parametrize(
    "unit", ["ms", "second", "minute", "h", "hour", "day", "fortnight", "m/s", "kg"]
)
def test_duration_grammar_does_not_expand_to_library_unit_names(unit):
    assert duration_seconds({"value": 1, "unit": unit}) is None


@pytest.mark.parametrize(
    "raw",
    [
        None,
        {},
        {"value": 1},
        {"value": True, "unit": "s"},
        {"value": -1, "unit": "min"},
        {"value": "0", "unit": "min"},
        {"value": float("nan"), "unit": "s"},
        {"value": float("inf"), "unit": "s"},
        {"value": 10**400, "unit": "s"},
        {"value": 1e308, "unit": "d"},
    ],
)
def test_missing_invalid_and_overflowing_durations_never_invent_zero(raw):
    assert duration_seconds(raw) is None
    assert (
        get_metadata_wait_time_minutes({"wait_time": _measurement_profile(raw)}) is None
    )


@pytest.mark.parametrize(
    ("seconds", "inspect_and_footer", "value_stream"),
    [
        (0, "0 min", "0 s"),
        (0.5, "0.5 s", "0.5 s"),
        (30, "30 s", "30 s"),
        (60, "1 min", "1 min"),
        (90, "90 s", "90 s"),
        (3600, "60 min", "1 hr"),
        (86400, "1440 min", "24 hr"),
    ],
)
def test_duration_presentation_keeps_existing_unit_selection(
    seconds, inspect_and_footer, value_stream
):
    assert _format_duration(seconds) == inspect_and_footer
    assert _format_timing_seconds(seconds) == inspect_and_footer
    assert _format_seconds(seconds) == value_stream


@pytest.mark.parametrize(
    ("value", "unit", "minutes"),
    [(30, "s", 0.5), (2, "m", 2), (2, "min", 2), (0.5, "hr", 30), (0.25, "d", 360)],
)
def test_wait_display_normalizes_without_changing_authored_units(value, unit, minutes):
    metadata = {"wait_time": _measurement_profile({"value": value, "unit": unit})}
    before = deepcopy(metadata)

    assert get_metadata_wait_time_minutes(metadata) == minutes
    assert metadata == before


@pytest.mark.parametrize("source", sorted(DURATION_UNITS))
@pytest.mark.parametrize("target", sorted(DURATION_UNITS))
def test_duration_conversion_supports_only_the_existing_time_dimension(source, target):
    seconds = {"s": 1, "m": 60, "min": 60, "hr": 3600, "d": 86400}

    assert convert_duration(2.5, source, target) == pytest.approx(
        2.5 * seconds[source] / seconds[target]
    )


@pytest.mark.parametrize("source,target", [("kg", "s"), ("s", "kg"), ("minute", "s")])
def test_duration_conversion_rejects_unsupported_units_explicitly(source, target):
    with pytest.raises(ValueError, match="Unsupported duration unit:"):
        convert_duration(1, source, target)


def test_duration_minute_alias_is_separate_from_spatial_metres():
    assert convert_duration(2, " M ", "s") == 120
    assert convert_duration(120, " S ", " M ") == 2
    assert length_in_metres(2, "m") == 2


def test_ordinary_import_leaves_pint_lazy_and_conversions_share_one_registry():
    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import flo; from flo.process import units; "
                "assert 'pint' not in sys.modules; "
                "assert units._registry.cache_info().currsize == 0; "
                "assert units.convert_duration(1, 'm', 's') == 60; "
                "registry = units._registry(); "
                "assert units.length_in_metres(100, 'cm') == 1; "
                "assert units.convert_measure(250, 'g', 'kg') == 0.25; "
                "assert units._registry() is registry; "
                "assert units._registry.cache_info().currsize == 1"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
