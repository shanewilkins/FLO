"""Measured quantities retain authored evidence and enforce canonical equivalence."""

from copy import deepcopy
from itertools import product
from math import nextafter

import pytest

from flo.errors import ValidationError
from flo.process.ir.models import IR, Edge, Node
from flo.process.ir.validate import validate_ir
from flo.process.units import convert_measure


def _process(quantity, *, collection="items"):
    kind = "equipment" if collection == "resources" else "material"
    return IR(
        name="Quantities",
        nodes=[Node(id="start", type="start"), Node(id="end", type="end")],
        edges=[Edge(source="start", target="end")],
        process_metadata={
            collection: [
                {"id": "supply", "name": "Supply", "kind": kind, "quantity": quantity}
            ]
        },
    )


_DIMENSIONS = (
    {"mg": 0.001, "g": 1, "kg": 1000},
    {"ml": 0.001, "l": 1},
    {"mm": 0.001, "cm": 0.01, "m": 1},
)
_EQUIVALENT_PAIRS = [
    (source, target, source_factor / target_factor)
    for units in _DIMENSIONS
    for (source, source_factor), (target, target_factor) in product(
        units.items(), repeat=2
    )
]


@pytest.mark.parametrize(
    "collection",
    ["items", "resources", "locations", "materials", "equipment", "workers"],
)
@pytest.mark.parametrize("source,target,canonical", _EQUIVALENT_PAIRS)
def test_equivalent_measures_preserve_authored_values_and_units(
    collection, source, target, canonical
):
    process = _process(
        {
            "kind": "measure",
            "value": 1,
            "unit": source,
            "canonical_value": canonical,
            "canonical_unit": target,
        },
        collection=collection,
    )
    before = deepcopy(process)

    validate_ir(process)

    assert process == before


@pytest.mark.parametrize(
    "source,target", [("g", "l"), ("ml", "kg"), ("m", "g"), ("kg", "cm")]
)
def test_canonical_units_must_have_the_same_dimension(source, target):
    quantity = {
        "kind": "measure",
        "value": 1,
        "unit": source,
        "canonical_value": 1,
        "canonical_unit": target,
    }

    with pytest.raises(ValidationError, match="E1222"):
        validate_ir(_process(quantity))


@pytest.mark.parametrize(
    "unit,canonical_unit", [("g", "kg"), ("ml", "l"), ("cm", "m"), ("kg", "kg")]
)
def test_canonical_quantity_must_represent_the_same_amount(unit, canonical_unit):
    quantity = {
        "kind": "measure",
        "value": 250,
        "unit": unit,
        "canonical_value": 99,
        "canonical_unit": canonical_unit,
    }

    with pytest.raises(ValidationError, match="E1223"):
        validate_ir(_process(quantity))


@pytest.mark.parametrize("value", [1e-300, 1, 1e300])
@pytest.mark.parametrize("relative_error", [-5e-10, 5e-10])
def test_relative_tolerance_accepts_roundoff_at_every_scale(value, relative_error):
    validate_ir(
        _process(
            {
                "kind": "measure",
                "value": value,
                "unit": "g",
                "canonical_value": value * (1 + relative_error),
                "canonical_unit": "g",
            }
        )
    )


@pytest.mark.parametrize("value", [1e-300, 1, 1e300])
@pytest.mark.parametrize("relative_error", [-2e-9, 2e-9])
def test_relative_tolerance_rejects_unequal_amounts_without_an_absolute_floor(
    value, relative_error
):
    quantity = {
        "kind": "measure",
        "value": value,
        "unit": "g",
        "canonical_value": value * (1 + relative_error),
        "canonical_unit": "g",
    }
    with pytest.raises(ValidationError, match="E1223"):
        validate_ir(_process(quantity))


@pytest.mark.parametrize("canonical", [nextafter(1 + 1e-9, 1), 1 - 1e-9])
def test_values_immediately_inside_the_relative_tolerance_boundary_are_valid(canonical):
    validate_ir(
        _process(
            {
                "kind": "measure",
                "value": 1,
                "unit": "g",
                "canonical_value": canonical,
                "canonical_unit": "g",
            }
        )
    )


@pytest.mark.parametrize("canonical", [1 + 1e-9, nextafter(1 - 1e-9, 0)])
def test_values_immediately_outside_the_relative_tolerance_boundary_are_invalid(
    canonical,
):
    with pytest.raises(ValidationError, match="E1223"):
        validate_ir(
            _process(
                {
                    "kind": "measure",
                    "value": 1,
                    "unit": "g",
                    "canonical_value": canonical,
                    "canonical_unit": "g",
                }
            )
        )


@pytest.mark.parametrize(
    "value,unit,canonical_value,canonical_unit",
    [(1e308, "kg", 1e308, "mg"), (5e-324, "mg", 5e-324, "kg")],
)
def test_canonical_conversion_must_remain_finite_and_positive(
    value, unit, canonical_value, canonical_unit
):
    quantity = {
        "kind": "measure",
        "value": value,
        "unit": unit,
        "canonical_value": canonical_value,
        "canonical_unit": canonical_unit,
    }
    with pytest.raises(ValidationError, match="E1224"):
        validate_ir(_process(quantity))


@pytest.mark.parametrize("unit", ["mg", "g", "kg", "ml", "l", "mm", "cm", "m"])
def test_canonical_quantity_is_optional_and_not_synthesized(unit):
    quantity = {"kind": "measure", "value": 1e308, "unit": unit}
    process = _process(quantity)
    before = deepcopy(process)

    validate_ir(process)

    assert process == before


@pytest.mark.parametrize(
    "patch,code",
    [
        ({"value": 0}, "E1209"),
        ({"value": True}, "E1209"),
        ({"value": float("inf")}, "E1209"),
        ({"unit": "lb"}, "E1210"),
        ({"canonical_unit": None}, "E1211"),
        ({"canonical_value": 0}, "E1212"),
        ({"canonical_value": float("nan")}, "E1212"),
        ({"canonical_unit": "grams"}, "E1213"),
    ],
)
def test_existing_measure_validation_codes_are_preserved(patch, code):
    quantity = {
        "kind": "measure",
        "value": 250,
        "unit": "g",
        "canonical_value": 0.25,
        "canonical_unit": "kg",
    }
    quantity.update(patch)
    with pytest.raises(ValidationError, match=code):
        validate_ir(_process(quantity))


@pytest.mark.parametrize("value", [1, 2, 10**400])
def test_counts_remain_positive_integer_entity_counts(value):
    validate_ir(
        _process(
            {"kind": "count", "value": value, "unit": "each", "qualifier": "large"}
        )
    )


@pytest.mark.parametrize("value", [0, -1, True, 1.5])
def test_count_rules_are_not_replaced_by_dimensionless_measurements(value):
    with pytest.raises(ValidationError, match="E1206"):
        validate_ir(_process({"kind": "count", "value": value, "unit": "each"}))


@pytest.mark.parametrize(
    "source,target", [("cup", "g"), ("g", "lb"), ("each", "g"), ("m", "min")]
)
def test_conversion_boundary_does_not_expand_the_measure_grammar(source, target):
    with pytest.raises(ValueError, match="Unsupported measure unit:"):
        convert_measure(1, source, target)


def test_conversion_boundary_retains_existing_case_and_whitespace_normalization():
    assert convert_measure(250, " G ", " KG ") == 0.25
    assert convert_measure(1, "m", "cm") == 100
