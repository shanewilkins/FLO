from copy import deepcopy
from math import hypot

import pytest

from flo.process.analysis import (
    aggregate_people_movements,
    aggregate_people_movements_by_worker,
    extract_location_spatial_index,
    infer_material_movements,
    infer_people_movements,
)
from flo.process.ir.models import IR, Edge, Node


def _positioned_process(source_unit="m", target_unit="m", target=(3, 4)):
    return {
        "nodes": [
            {"id": "a", "location": "a", "performed_by": ["worker"]},
            {"id": "b", "location": "b", "performed_by": ["worker"]},
        ],
        "edges": [{"source": "a", "target": "b"}],
        "process": {
            "locations": [
                {
                    "id": "a",
                    "spatial": {"x": 0, "y": 0, "unit": source_unit},
                },
                {
                    "id": "b",
                    "spatial": {"x": target[0], "y": target[1], "unit": target_unit},
                },
            ]
        },
    }


@pytest.mark.parametrize(
    ("unit", "target"),
    [("mm", (3000, 4000)), ("cm", (300, 400)), ("in", (30, 40)), ("ft", (3, 4))],
)
def test_mixed_unit_movements_use_one_metre_frame_without_mutating_input(unit, target):
    process = _positioned_process(target_unit=unit, target=target)
    before = deepcopy(process)
    factor = {"mm": 0.001, "cm": 0.01, "in": 0.0254, "ft": 0.3048}[unit]

    for infer in (infer_material_movements, infer_people_movements):
        distance = infer(process)[0]["distance"]
        assert distance["unit"] == "m"
        assert distance["value"] == pytest.approx(hypot(*target) * factor)
    assert process == before


def test_mixed_units_convert_both_nonzero_endpoints_before_subtraction():
    process = _positioned_process(target_unit="ft", target=(10, 20))
    process["process"]["locations"][0]["spatial"].update(x=1, y=2)

    forward = infer_material_movements(process)[0]["distance"]
    process["edges"] = [{"source": "b", "target": "a"}]
    reverse = infer_material_movements(process)[0]["distance"]

    assert forward["unit"] == "m"
    assert forward["value"] == pytest.approx(hypot(3.048 - 1, 6.096 - 2))
    assert reverse == forward


def test_homogeneous_maps_retain_their_unit_and_scale():
    process = _positioned_process(source_unit="ft", target_unit="ft")
    assert infer_material_movements(process)[0]["distance"] == {
        "value": 5,
        "unit": "ft",
    }
    assert extract_location_spatial_index(process)["b"]["x"] == 3


@pytest.mark.parametrize("invalid", [True, float("nan"), float("inf"), 10**400])
def test_invalid_unvalidated_coordinates_have_no_inferred_distance(invalid):
    process = _positioned_process(target=(invalid, 4))
    assert "distance" not in infer_material_movements(process)[0]


@pytest.mark.parametrize("unit", ["kg", "s", "km", "nonsense"])
def test_pint_does_not_expand_the_supported_spatial_unit_contract(unit):
    process = _positioned_process(target_unit=unit)
    assert "distance" not in infer_material_movements(process)[0]


def test_large_finite_distances_do_not_overflow_during_squaring():
    process = _positioned_process(target=(3e200, 4e200))
    assert infer_material_movements(process)[0]["distance"]["value"] == pytest.approx(
        5e200
    )


def test_overflowed_distance_is_unavailable():
    process = _positioned_process(target=(1e308, 0))
    process["process"]["locations"][0]["spatial"]["x"] = -1e308
    assert "distance" not in infer_material_movements(process)[0]


def test_infer_people_movements_requires_shared_workers_and_location_change():
    ir = IR(
        name="people",
        nodes=[
            Node(
                id="gather",
                type="task",
                location="pantry",
                performed_by=["lead_baker", "assistant_baker"],
            ),
            Node(
                id="mix",
                type="task",
                location="prep_bench",
                performed_by=["assistant_baker"],
            ),
            Node(
                id="bake",
                type="task",
                location="oven_station",
                performed_by=["lead_baker"],
            ),
        ],
        edges=[
            Edge(source="gather", target="mix"),
            Edge(source="mix", target="bake"),
        ],
    )

    movements = infer_people_movements(ir)

    assert len(movements) == 1
    assert movements[0]["from_location"] == "pantry"
    assert movements[0]["to_location"] == "prep_bench"
    assert movements[0]["workers"] == ["assistant_baker"]


def test_aggregate_people_movements_merges_worker_sets_by_route():
    routes = aggregate_people_movements(
        [
            {
                "from_location": "pantry",
                "to_location": "prep_bench",
                "workers": ["assistant_baker"],
            },
            {
                "from_location": "pantry",
                "to_location": "prep_bench",
                "workers": ["lead_baker"],
            },
        ]
    )

    assert len(routes) == 1
    assert routes[0]["from_location"] == "pantry"
    assert routes[0]["to_location"] == "prep_bench"
    assert routes[0]["count"] == 2
    assert routes[0]["workers"] == ["assistant_baker", "lead_baker"]


def test_aggregate_people_movements_by_worker_splits_routes_per_worker():
    routes = aggregate_people_movements_by_worker(
        [
            {
                "from_location": "pantry",
                "to_location": "prep_bench",
                "workers": ["assistant_baker", "lead_baker"],
            },
            {
                "from_location": "pantry",
                "to_location": "prep_bench",
                "workers": ["assistant_baker"],
            },
        ]
    )

    assert len(routes) == 2
    by_worker = {tuple(route.get("workers") or []): route for route in routes}
    assert by_worker[("assistant_baker",)]["count"] == 2
    assert by_worker[("lead_baker",)]["count"] == 1


def test_extract_location_spatial_index_includes_location_kind():
    process = {
        "process": {
            "metadata": {},
            "locations": [
                {
                    "id": "pantry",
                    "name": "Pantry",
                    "kind": "storage",
                    "spatial": {"x": 1.0, "y": 2.0, "unit": "m"},
                },
                {
                    "id": "oven_station",
                    "name": "Oven Station",
                    "spatial": {"x": 4.0, "y": 3.0, "unit": "m"},
                    "kind": "heat",
                },
            ],
        }
    }

    locations = extract_location_spatial_index(process)
    assert locations["pantry"]["kind"] == "storage"
    assert locations["oven_station"]["kind"] == "heat"


def test_infer_material_movements_uses_canonical_produces_and_consumes():
    ir = IR(
        name="materials",
        nodes=[
            Node(
                id="mix",
                type="task",
                location="prep_bench",
                produces=["dough"],
            ),
            Node(
                id="bake",
                type="task",
                location="oven_station",
                consumes=["dough"],
            ),
        ],
        edges=[Edge(source="mix", target="bake")],
    )

    movements = infer_material_movements(ir)

    assert len(movements) == 1
    assert movements[0]["from_location"] == "prep_bench"
    assert movements[0]["to_location"] == "oven_station"
    assert movements[0]["items"] == ["dough"]


def test_infer_people_movements_uses_canonical_performed_by():
    ir = IR(
        name="people",
        nodes=[
            Node(
                id="review",
                type="task",
                location="intake",
                performed_by=["reviewer"],
            ),
            Node(
                id="approve",
                type="task",
                location="approval_desk",
                performed_by=["reviewer"],
            ),
        ],
        edges=[Edge(source="review", target="approve")],
    )

    movements = infer_people_movements(ir)

    assert len(movements) == 1
    assert movements[0]["from_location"] == "intake"
    assert movements[0]["to_location"] == "approval_desk"
    assert movements[0]["workers"] == ["reviewer"]
