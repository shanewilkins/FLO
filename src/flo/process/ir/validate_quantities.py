"""Dimensional quantity validation over locally validated entity amounts."""

import math
from typing import Any

from flo.errors import ValidationError
from flo.process.units import MEASURE_UNITS, convert_measure

from .validation_errors import _QuantityValidationError

_QUANTITY_REL_TOL = 1e-9


def _validate_measure_quantity(path: str, quantity: dict[str, Any]) -> None:
    value, unit = quantity["value"], quantity["unit"]
    if unit.strip().lower() not in MEASURE_UNITS:
        raise _QuantityValidationError(
            f"E1210: {path}.quantity.unit must be one of {sorted(MEASURE_UNITS)} for kind=measure",
            "unit",
        )
    canonical_value, canonical_unit = (
        quantity.get("canonical_value"),
        quantity.get("canonical_unit"),
    )
    if canonical_value is not None:
        _validate_canonical_quantity(
            path, canonical_value, canonical_unit, value=value, unit=unit
        )


def _validate_canonical_quantity(
    path: str,
    canonical_value: Any,
    canonical_unit: Any,
    *,
    value: float,
    unit: str,
) -> None:
    if (
        not isinstance(canonical_unit, str)
        or canonical_unit.strip().lower() not in MEASURE_UNITS
    ):
        raise ValidationError(
            f"E1213: {path}.quantity.canonical_unit must be one of {sorted(MEASURE_UNITS)}"
        )
    try:
        equivalent = convert_measure(float(value), unit, canonical_unit)
    except ValueError as exc:
        raise _QuantityValidationError(
            f"E1222: {path}.quantity.canonical_unit must have the same dimension as unit '{unit}'",
            "canonical_unit",
        ) from exc
    if not math.isfinite(equivalent) or equivalent <= 0:
        raise _QuantityValidationError(
            f"E1224: {path}.quantity.canonical_value conversion must remain finite and > 0 in '{canonical_unit}'",
            "canonical_value",
        )
    if not math.isclose(
        equivalent, canonical_value, rel_tol=_QUANTITY_REL_TOL, abs_tol=0
    ):
        raise _QuantityValidationError(
            f"E1223: {path}.quantity.canonical_value must represent the same amount as {value} {unit} "
            f"({equivalent:g} {canonical_unit}; relative tolerance {_QUANTITY_REL_TOL:g}, absolute tolerance 0)",
            "canonical_value",
        )
