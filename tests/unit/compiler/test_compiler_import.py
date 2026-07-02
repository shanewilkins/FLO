import pytest

from flo.compiler import compile_adapter


def test_compile_requires_spec_version_process_and_steps() -> None:
    with pytest.raises(ValueError, match="spec_version"):
        compile_adapter(
            {
                "process": {"id": "p", "name": "Process"},
                "steps": [{"id": "start", "kind": "start", "name": "Start"}],
            }
        )


def test_compile_accepts_transitions_key_for_explicit_connections() -> None:
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process"},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "transitions": [
            {"source": "start", "target": "end"},
        ],
    }

    ir = compile_adapter(parsed)
    assert len(ir.edges) == 1
    assert ir.edges[0].source == "start"
    assert ir.edges[0].target == "end"


def test_compile_rejects_edges_alias() -> None:
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process"},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "end"},
        ],
    }

    with pytest.raises(ValueError, match="transitions"):
        compile_adapter(parsed)


def test_compile_rejects_nodes_alias_for_steps() -> None:
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process"},
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
    }

    with pytest.raises(ValueError, match="steps"):
        compile_adapter(parsed)


def test_compile_rejects_from_to_transition_alias() -> None:
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process"},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "transitions": [
            {"from": "start", "to": "end"},
        ],
    }

    with pytest.raises(ValueError, match="source"):
        compile_adapter(parsed)


def test_compile_preserves_node_metadata():
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process"},
        "steps": [
            {
                "id": "n1",
                "kind": "task",
                "name": "Task",
                "metadata": {"cycle_time_seconds": 120},
            }
        ],
    }
    ir = compile_adapter(parsed)
    assert ir.nodes[0].attrs is not None
    assert ir.nodes[0].attrs.get("metadata") == {"cycle_time_seconds": 120}


def test_compile_preserves_step_inputs_and_outputs():
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process"},
        "steps": [
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "inputs": ["flour", "water"],
                "outputs": ["dough"],
            }
        ],
    }
    ir = compile_adapter(parsed)
    assert ir.nodes[0].attrs is not None
    assert ir.nodes[0].attrs.get("inputs") == ["flour", "water"]
    assert ir.nodes[0].attrs.get("outputs") == ["dough"]


def test_compile_preserves_step_location_workers_and_equipment():
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process"},
        "steps": [
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "location": "prep_bench",
                "workers": ["lead_baker"],
                "equipment": ["mixer"],
            }
        ],
    }
    ir = compile_adapter(parsed)
    assert ir.nodes[0].attrs is not None
    assert ir.nodes[0].attrs.get("location") == "prep_bench"
    assert ir.nodes[0].attrs.get("workers") == ["lead_baker"]
    assert ir.nodes[0].attrs.get("equipment") == ["mixer"]


def test_compile_promotes_top_level_resources_to_process_metadata():
    parsed = {
        "spec_version": "0.1",
        "process": {
            "id": "p",
            "name": "Process",
            "metadata": {"cycle_time_seconds": {"target": 300}},
        },
        "materials": [
            {"id": "flour", "name": "Flour"},
            {"id": "sugar", "name": "Sugar"},
        ],
        "equipment": [
            {"id": "oven", "name": "Oven"},
        ],
        "locations": [
            {"id": "prep_station", "name": "Prep Station"},
        ],
        "workers": [
            {"id": "baker", "name": "Baker"},
        ],
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "transitions": [
            {"source": "start", "target": "end"},
        ],
    }

    ir = compile_adapter(parsed)
    assert ir.process_metadata is not None
    assert ir.process_metadata["cycle_time_seconds"]["target"] == 300
    assert ir.process_metadata["materials"][0]["id"] == "flour"
    assert ir.process_metadata["equipment"][0]["id"] == "oven"
    assert ir.process_metadata["locations"][0]["id"] == "prep_station"
    assert ir.process_metadata["workers"][0]["id"] == "baker"
    assert ir.process_metadata["process_id"] == "p"
    assert ir.process_metadata["process_name"] == "Process"


def test_compile_promotes_grouped_materials_to_process_metadata():
    parsed = {
        "spec_version": "0.1",
        "process": {
            "id": "p",
            "name": "Process",
        },
        "materials": {
            "dry": {
                "name": "Dry Ingredients",
                "items": [
                    {"id": "flour", "name": "Flour"},
                    {"id": "sugar", "name": "Sugar"},
                ],
            },
            "wet": {
                "name": "Wet Ingredients",
                "dairy": {
                    "name": "Dairy",
                    "items": [
                        {"id": "butter", "name": "Butter"},
                    ],
                },
            },
        },
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "transitions": [
            {"source": "start", "target": "end"},
        ],
    }

    ir = compile_adapter(parsed)
    assert ir.process_metadata is not None
    assert ir.process_metadata["materials"]["dry"]["name"] == "Dry Ingredients"
    assert ir.process_metadata["materials"]["dry"]["items"][0]["id"] == "flour"
    assert ir.process_metadata["materials"]["wet"]["name"] == "Wet Ingredients"
    assert ir.process_metadata["materials"]["wet"]["dairy"]["name"] == "Dairy"
    assert (
        ir.process_metadata["materials"]["wet"]["dairy"]["items"][0]["id"] == "butter"
    )


def test_compile_flattens_subprocess_subnodes():
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process"},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {
                "id": "prep",
                "kind": "subprocess",
                "name": "Prep",
                "subnodes": [
                    {"id": "gather", "kind": "task", "name": "Gather"},
                    {"id": "mix", "kind": "task", "name": "Mix"},
                ],
            },
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "transitions": [
            {"source": "start", "target": "prep"},
            {"source": "prep", "target": "gather"},
            {"source": "gather", "target": "mix"},
            {"source": "mix", "target": "end"},
        ],
    }

    ir = compile_adapter(parsed)
    node_ids = [node.id for node in ir.nodes]
    assert node_ids == ["start", "prep", "gather", "mix", "end"]
    by_id = {node.id: node for node in ir.nodes}
    assert by_id["prep"].attrs.get("subprocess_parent") is None
    assert by_id["gather"].attrs.get("subprocess_parent") == "prep"
    assert by_id["mix"].attrs.get("subprocess_parent") == "prep"


def test_compile_flattens_nested_subprocess_subnodes():
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process"},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {
                "id": "outer",
                "kind": "subprocess",
                "name": "Outer",
                "subnodes": [
                    {
                        "id": "inner",
                        "kind": "subprocess",
                        "name": "Inner",
                        "steps": [
                            {"id": "inner_task", "kind": "task", "name": "Inner Task"},
                        ],
                    }
                ],
            },
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "transitions": [
            {"source": "start", "target": "outer"},
            {"source": "outer", "target": "inner"},
            {"source": "inner", "target": "inner_task"},
            {"source": "inner_task", "target": "end"},
        ],
    }

    ir = compile_adapter(parsed)
    node_ids = [node.id for node in ir.nodes]
    assert node_ids == ["start", "outer", "inner", "inner_task", "end"]
    by_id = {node.id: node for node in ir.nodes}
    assert by_id["outer"].attrs.get("subprocess_parent") is None
    assert by_id["inner"].attrs.get("subprocess_parent") == "outer"
    assert by_id["inner_task"].attrs.get("subprocess_parent") == "inner"


def test_compile_promotes_canonical_items_and_resources_to_process_metadata():
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process"},
        "items": [
            {"id": "order", "name": "Order", "kind": "information"},
            {"id": "dough", "name": "Dough", "kind": "material"},
        ],
        "resources": [
            {"id": "baker", "name": "Baker", "kind": "person"},
            {"id": "mixer", "name": "Mixer", "kind": "equipment"},
        ],
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "transitions": [
            {"source": "start", "target": "end"},
        ],
    }

    ir = compile_adapter(parsed)
    assert ir.process_metadata is not None
    assert ir.process_metadata["items"][0]["id"] == "order"
    assert ir.process_metadata["resources"][0]["id"] == "baker"


def test_compile_preserves_canonical_step_relations():
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process"},
        "steps": [
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "consumes": ["flour", "water"],
                "produces": ["dough"],
                "performed_by": ["lead_baker"],
                "uses": ["mixer"],
            }
        ],
    }

    ir = compile_adapter(parsed)
    assert ir.nodes[0].attrs is not None
    assert ir.nodes[0].attrs.get("consumes") == ["flour", "water"]
    assert ir.nodes[0].attrs.get("produces") == ["dough"]
    assert ir.nodes[0].attrs.get("performed_by") == ["lead_baker"]
    assert ir.nodes[0].attrs.get("uses") == ["mixer"]


def test_compile_maps_legacy_step_relations_to_canonical_aliases():
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process"},
        "steps": [
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "inputs": ["flour", "water"],
                "outputs": ["dough"],
                "workers": ["lead_baker"],
                "equipment": ["mixer"],
            }
        ],
    }

    ir = compile_adapter(parsed)
    assert ir.nodes[0].attrs is not None
    assert ir.nodes[0].attrs.get("consumes") == ["flour", "water"]
    assert ir.nodes[0].attrs.get("produces") == ["dough"]
    assert ir.nodes[0].attrs.get("performed_by") == ["lead_baker"]
    assert ir.nodes[0].attrs.get("uses") == ["mixer"]


def test_compile_preserves_explicit_handoff_on_transition():
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process"},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "transitions": [
            {"source": "start", "target": "end", "handoff": True},
        ],
    }

    ir = compile_adapter(parsed)
    assert len(ir.edges) == 1
    assert ir.edges[0].handoff is True
