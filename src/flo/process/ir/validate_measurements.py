"""Duration dimensional semantics at the canonical IR boundary."""

from flo.errors import ValidationError
from flo.process.contracts import MEASUREMENT_ADAPTER, MeasurementProfile
from flo.process.durations import duration_seconds
from flo.process.measurements import selected_result

from .models import IR
from .validation_errors import _LocatedValidationError


def _validate_process_measurement(obj: IR) -> None:
    if obj.lead_time is None:
        return
    try:
        MeasurementProfile.model_validate(obj.lead_time)
    except Exception as exc:
        raise _LocatedValidationError(
            "E1301: process lead_time must be a valid measurement profile",
            ("process", "lead_time"),
        ) from exc
    _validate_selected_durations(
        obj.lead_time,
        context="process lead_time",
        location=("process", "lead_time"),
    )


def _validate_selected_durations(
    measurement: object, *, context: str, location: tuple[str | int, ...] = ()
) -> None:
    for selector in ("analysis_input", "primary"):
        result = selected_result(measurement, selector)
        if result is not None and duration_seconds(result) is None:
            raise _LocatedValidationError(
                f"E1303: {context} {selector} must be a valid duration",
                location,
            )


def _validate_node_measurements(obj: IR) -> None:
    for node in obj.nodes:
        for field in ("cycle_time", "wait_time", "changeover_time"):
            value = getattr(node, field)
            if value is None:
                continue
            try:
                if field == "wait_time":
                    MEASUREMENT_ADAPTER.validate_python(value)
                else:
                    MeasurementProfile.model_validate(value)
            except Exception as exc:
                raise ValidationError(
                    f"E1301: node '{node.id}' {field} must be a valid measurement profile or reference"
                ) from exc
            _validate_selected_durations(value, context=f"node '{node.id}' {field}")
