from flo.compiler.analysis import (
    infer_people_movements,
    aggregate_people_movements,
    aggregate_people_movements_by_worker,
    extract_location_spatial_index,
)
from flo.compiler.ir.models import Edge, IR


def test_infer_people_movements_requires_shared_workers_and_location_change(node_factory):
    ir = IR(
        name="people",
        nodes=[
            node_factory(
                "gather",
                type="task",
                attrs={"location": "pantry", "workers": ["lead_baker", "assistant_baker"]},
            ),
            node_factory(
                "mix",
                type="task",
                attrs={"location": "prep_bench", "workers": ["assistant_baker"]},
            ),
            node_factory(
                "bake",
                type="task",
                attrs={"location": "oven_station", "workers": ["lead_baker"]},
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
            {"from_location": "pantry", "to_location": "prep_bench", "workers": ["assistant_baker"]},
            {"from_location": "pantry", "to_location": "prep_bench", "workers": ["lead_baker"]},
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
            {"from_location": "pantry", "to_location": "prep_bench", "workers": ["assistant_baker", "lead_baker"]},
            {"from_location": "pantry", "to_location": "prep_bench", "workers": ["assistant_baker"]},
        ]
    )

    assert len(routes) == 2
    by_worker = {tuple(route.get("workers") or []): route for route in routes}
    assert by_worker[("assistant_baker",)]["count"] == 2
    assert by_worker[("lead_baker",)]["count"] == 1


def test_extract_location_spatial_index_includes_location_kind():
    process = {
        "process": {
            "metadata": {
                "locations": [
                    {
                        "id": "pantry",
                        "name": "Pantry",
                        "kind": "storage",
                        "metadata": {"spatial": {"x": 1.0, "y": 2.0, "unit": "m"}},
                    },
                    {
                        "id": "oven_station",
                        "name": "Oven Station",
                        "metadata": {
                            "kind": "heat",
                            "spatial": {"x": 4.0, "y": 3.0, "unit": "m"},
                        },
                    },
                ]
            }
        }
    }

    locations = extract_location_spatial_index(process)
    assert locations["pantry"]["kind"] == "storage"
    assert locations["oven_station"]["kind"] == "heat"
