import pytest
from flo.compiler.ir.validate import validate_ir
from flo.compiler.ir.models import IR, Node, Edge
from flo.services.errors import ValidationError


def test_validate_ir_wrong_type():
    with pytest.raises(ValidationError):
        validate_ir(object())


def test_validate_ir_empty_nodes(ir_factory):
    ir = ir_factory(name="x", nodes=[])
    with pytest.raises(ValidationError):
        validate_ir(ir)


@pytest.mark.parametrize("ids", [["dup", "dup"], ["a", "a", "a"]])
def test_validate_ir_duplicate_ids(ir_factory, node_factory, ids):
    nodes = [node_factory(i) for i in ids]
    ir = ir_factory(name="dup", nodes=nodes)
    with pytest.raises(ValidationError):
        validate_ir(ir)


def test_validate_ir_unresolved_edge_raises():
    ir = IR(
        name="x",
        nodes=[Node(id="start", type="start"), Node(id="end", type="end")],
        edges=[Edge(source="start", target="missing")],
    )
    with pytest.raises(ValidationError):
        validate_ir(ir)


def test_validate_ir_decision_requires_two_outgoing_edges():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="gate", type="decision"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="gate"),
            Edge(source="gate", target="end"),
        ],
    )
    with pytest.raises(ValidationError):
        validate_ir(ir)


def test_validate_ir_non_start_node_requires_predecessor():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="mid", type="task"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="end"),
            Edge(source="mid", target="end"),
        ],
    )
    with pytest.raises(ValidationError, match="E1006"):
        validate_ir(ir)


def test_validate_ir_non_end_node_requires_successor():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="mid", type="task"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="mid"),
        ],
    )
    with pytest.raises(ValidationError, match="E1007"):
        validate_ir(ir)


def test_validate_ir_decision_error_precedes_generic_successor_rule():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="gate", type="decision"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="gate"),
            Edge(source="gate", target="end"),
        ],
    )
    with pytest.raises(ValidationError, match="E1005"):
        validate_ir(ir)


def test_validate_ir_node_unreachable_from_start_raises():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="a", type="task"),
            Node(id="end", type="end"),
            Node(id="x", type="task"),
            Node(id="y", type="task"),
            Node(id="z", type="end"),
        ],
        edges=[
            Edge(source="start", target="a"),
            Edge(source="a", target="end"),
            Edge(source="x", target="y"),
            Edge(source="y", target="x"),
            Edge(source="y", target="z"),
        ],
    )
    with pytest.raises(ValidationError, match="E1008"):
        validate_ir(ir)


def test_validate_ir_node_cannot_reach_any_end_raises():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="loop", type="task"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="loop"),
            Edge(source="loop", target="loop"),
            Edge(source="start", target="end"),
        ],
    )
    with pytest.raises(ValidationError, match="E1009"):
        validate_ir(ir)


def test_validate_ir_requires_at_least_one_end_node():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="task", type="task"),
        ],
        edges=[
            Edge(source="start", target="task"),
            Edge(source="task", target="start"),
        ],
    )
    with pytest.raises(ValidationError, match="E1010"):
        validate_ir(ir)


def test_validate_ir_material_count_requires_integer_value():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="end"),
        ],
        process_metadata={
            "materials": [
                {
                    "id": "egg",
                    "name": "Egg",
                    "quantity": {"kind": "count", "value": 2.5, "unit": "each"},
                }
            ]
        },
    )
    with pytest.raises(ValidationError, match="E1206"):
        validate_ir(ir)


def test_validate_ir_material_measure_requires_supported_unit():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="end"),
        ],
        process_metadata={
            "materials": [
                {
                    "id": "flour",
                    "name": "Flour",
                    "quantity": {"kind": "measure", "value": 250, "unit": "cups"},
                }
            ]
        },
    )
    with pytest.raises(ValidationError, match="E1210"):
        validate_ir(ir)


def test_validate_ir_accepts_material_count_and_measure_shapes():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="end"),
        ],
        process_metadata={
            "materials": [
                {
                    "id": "egg",
                    "name": "Egg",
                    "quantity": {"kind": "count", "value": 2, "unit": "each", "qualifier": "large"},
                },
                {
                    "id": "flour",
                    "name": "Flour",
                    "quantity": {
                        "kind": "measure",
                        "value": 250,
                        "unit": "g",
                        "canonical_value": 0.25,
                        "canonical_unit": "kg",
                    },
                },
            ],
            "equipment": [
                {
                    "id": "oven",
                    "name": "Oven",
                    "quantity": {"kind": "count", "value": 1, "unit": "each"},
                }
            ],
            "locations": [
                {
                    "id": "kitchen",
                    "name": "Kitchen",
                }
            ],
            "workers": [
                {
                    "id": "baker",
                    "name": "Baker",
                    "quantity": {"kind": "count", "value": 1, "unit": "each"},
                }
            ],
        },
    )

    # should not raise
    validate_ir(ir)


def test_validate_ir_accepts_mm_and_cm_measure_units():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="end"),
        ],
        process_metadata={
            "materials": [
                {
                    "id": "wire_segment",
                    "name": "Wire Segment",
                    "quantity": {"kind": "measure", "value": 25, "unit": "cm"},
                }
            ],
            "equipment": [
                {
                    "id": "spacer",
                    "name": "Spacer",
                    "quantity": {"kind": "measure", "value": 3, "unit": "mm"},
                }
            ],
        },
    )

    # should not raise
    validate_ir(ir)


def test_validate_ir_locations_must_be_list_when_present():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="end"),
        ],
        process_metadata={
            "locations": {"id": "kitchen", "name": "Kitchen"},
        },
    )

    with pytest.raises(ValidationError, match="E1201"):
        validate_ir(ir)


def test_validate_ir_accepts_location_spatial_metadata():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="end"),
        ],
        process_metadata={
            "locations": [
                {
                    "id": "prep_bench",
                    "name": "Prep Bench",
                    "metadata": {
                        "spatial": {
                            "x": 3.0,
                            "y": 2.0,
                            "unit": "m",
                        }
                    },
                }
            ],
        },
    )

    validate_ir(ir)


def test_validate_ir_rejects_location_spatial_missing_coordinates():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="end"),
        ],
        process_metadata={
            "locations": [
                {
                    "id": "prep_bench",
                    "name": "Prep Bench",
                    "metadata": {
                        "spatial": {
                            "x": 3.0,
                            "unit": "m",
                        }
                    },
                }
            ],
        },
    )

    with pytest.raises(ValidationError, match="E1215"):
        validate_ir(ir)


def test_validate_ir_rejects_location_spatial_with_invalid_unit():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="end"),
        ],
        process_metadata={
            "locations": [
                {
                    "id": "prep_bench",
                    "name": "Prep Bench",
                    "metadata": {
                        "spatial": {
                            "x": 3.0,
                            "y": 2.0,
                            "unit": "yards",
                        }
                    },
                }
            ],
        },
    )

    with pytest.raises(ValidationError, match="E1216"):
        validate_ir(ir)


def test_validate_ir_accepts_grouped_and_nested_materials():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="end"),
        ],
        process_metadata={
            "materials": {
                "dry": {
                    "name": "Dry Ingredients",
                    "items": [
                        {
                            "id": "flour",
                            "name": "Flour",
                            "quantity": {"kind": "measure", "value": 250, "unit": "g"},
                        },
                    ],
                },
                "wet": {
                    "name": "Wet Ingredients",
                    "dairy": {
                        "name": "Dairy",
                        "items": [
                            {
                                "id": "butter",
                                "name": "Butter",
                                "quantity": {"kind": "measure", "value": 100, "unit": "g"},
                            }
                        ],
                    },
                },
            },
        },
    )

    # should not raise
    validate_ir(ir)


def test_validate_ir_rejects_group_with_non_collection_value():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="end"),
        ],
        process_metadata={
            "materials": {
                "dry": "not-a-list",
            },
        },
    )

    with pytest.raises(ValidationError, match="E1201"):
        validate_ir(ir)


def test_validate_ir_rejects_group_with_non_string_name():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="end"),
        ],
        process_metadata={
            "materials": {
                "dry": {
                    "name": 123,
                    "items": [{"id": "flour", "name": "Flour"}],
                },
            },
        },
    )

    with pytest.raises(ValidationError, match="E1201"):
        validate_ir(ir)


def test_validate_ir_accepts_node_time_metadata_units():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="mix", type="task", attrs={"metadata": {"cycle_time": {"value": 15, "unit": "m"}}}),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="mix"),
            Edge(source="mix", target="end"),
        ],
    )

    # should not raise
    validate_ir(ir)


def test_validate_ir_rejects_invalid_node_time_unit():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="mix", type="task", attrs={"metadata": {"cycle_time": {"value": 15, "unit": "weeks"}}}),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="mix"),
            Edge(source="mix", target="end"),
        ],
    )

    with pytest.raises(ValidationError, match="E1303"):
        validate_ir(ir)


def test_validate_ir_rejects_non_object_node_time_metadata_value():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="mix", type="task", attrs={"metadata": {"cycle_time": 15}}),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="mix"),
            Edge(source="mix", target="end"),
        ],
    )

    with pytest.raises(ValidationError, match="E1301"):
        validate_ir(ir)


def test_validate_ir_accepts_node_inputs_outputs_lists():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(
                id="mix",
                type="task",
                attrs={
                    "inputs": ["flour", "water"],
                    "outputs": ["dough"],
                },
            ),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="mix"),
            Edge(source="mix", target="end"),
        ],
    )

    # should not raise
    validate_ir(ir)


def test_validate_ir_rejects_non_list_node_inputs():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="mix", type="task", attrs={"inputs": "flour"}),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="mix"),
            Edge(source="mix", target="end"),
        ],
    )

    with pytest.raises(ValidationError, match="E1310"):
        validate_ir(ir)


def test_validate_ir_rejects_empty_string_node_output_item():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="mix", type="task", attrs={"outputs": [""]}),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="mix"),
            Edge(source="mix", target="end"),
        ],
    )

    with pytest.raises(ValidationError, match="E1311"):
        validate_ir(ir)


def test_validate_ir_accepts_valid_value_class_values():
    for vc in ("VA", "RNVA", "NVA", "unknown"):
        ir = IR(
            name="x",
            nodes=[
                Node(id="start", type="start"),
                Node(id="step", type="task", attrs={"metadata": {"value_class": vc}}),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="step"),
                Edge(source="step", target="end"),
            ],
        )
        validate_ir(ir)  # must not raise


def test_validate_ir_rejects_invalid_value_class():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="step", type="task", attrs={"metadata": {"value_class": "A"}}),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="step"),
            Edge(source="step", target="end"),
        ],
    )

    with pytest.raises(ValidationError, match="E1320"):
        validate_ir(ir)


def test_validate_ir_node_without_value_class_passes():
    ir = IR(
        name="x",
        nodes=[
            Node(id="start", type="start"),
            Node(id="step", type="task", attrs={"metadata": {"cycle_time": {"value": 5, "unit": "min"}}}),
            Node(id="end", type="end"),
        ],
        edges=[
            Edge(source="start", target="step"),
            Edge(source="step", target="end"),
        ],
    )
    validate_ir(ir)  # must not raise
