import pytest

from flo.source import compile_adapter


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


def test_compile_preserves_node_extensions():
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process"},
        "steps": [
            {
                "id": "n1",
                "kind": "task",
                "name": "Task",
                "extensions": {"example:priority": "high"},
            }
        ],
    }
    ir = compile_adapter(parsed)
    assert ir.nodes[0].extensions == {"example:priority": "high"}


def test_compile_preserves_step_consumes_and_produces():
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
            }
        ],
    }
    ir = compile_adapter(parsed)
    assert ir.nodes[0].consumes == ["flour", "water"]
    assert ir.nodes[0].produces == ["dough"]


def test_compile_preserves_step_location_and_resources():
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process"},
        "steps": [
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "location": "prep_bench",
                "performed_by": ["lead_baker"],
                "uses": ["mixer"],
            }
        ],
    }
    ir = compile_adapter(parsed)
    assert ir.nodes[0].location == "prep_bench"
    assert ir.nodes[0].performed_by == ["lead_baker"]
    assert ir.nodes[0].uses == ["mixer"]


def test_compile_promotes_top_level_locations_to_canonical_ir():
    parsed = {
        "spec_version": "0.1",
        "process": {
            "id": "p",
            "name": "Process",
            "extensions": {"example:target": 300},
            "items": [
                {"id": "flour", "name": "Flour", "kind": "material"},
                {"id": "sugar", "name": "Sugar", "kind": "material"},
            ],
            "resources": [
                {"id": "oven", "name": "Oven", "kind": "equipment"},
                {"id": "baker", "name": "Baker", "kind": "person"},
            ],
            "locations": [{"id": "prep_station", "name": "Prep Station"}],
        },
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "transitions": [{"source": "start", "target": "end"}],
    }

    ir = compile_adapter(parsed)
    assert ir.extensions == {"example:target": 300}
    assert ir.items[0]["id"] == "flour"
    assert ir.resources[0]["id"] == "oven"
    assert isinstance(ir.locations, list)
    assert ir.locations[0]["id"] == "prep_station"
    assert ir.resources[1]["id"] == "baker"
    assert ir.process_metadata["process_id"] == "p"
    assert ir.process_metadata["process_name"] == "Process"


def test_compile_preserves_integer_process_version() -> None:
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process", "version": 7},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
    }

    ir = compile_adapter(parsed)

    assert ir.process_version == 7


def test_compile_preserves_string_process_version() -> None:
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process", "version": "2026.1"},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
    }

    ir = compile_adapter(parsed)

    assert ir.process_version == "2026.1"


def test_compile_rejects_non_scalar_process_version() -> None:
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process", "version": [2026, 1]},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
    }

    with pytest.raises(ValueError, match=r"process\.version"):
        compile_adapter(parsed)


def test_compile_preserves_grouped_items():
    parsed = {
        "spec_version": "0.1",
        "process": {
            "id": "p",
            "name": "Process",
            "items": {
                "dry": {
                    "name": "Dry Ingredients",
                    "items": [
                        {"id": "flour", "name": "Flour", "kind": "material"},
                        {"id": "sugar", "name": "Sugar", "kind": "material"},
                    ],
                },
                "wet": {
                    "name": "Wet Ingredients",
                    "dairy": {
                        "name": "Dairy",
                        "items": [
                            {"id": "butter", "name": "Butter", "kind": "material"}
                        ],
                    },
                },
            },
        },
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "transitions": [{"source": "start", "target": "end"}],
    }

    ir = compile_adapter(parsed)
    assert ir.items["dry"]["name"] == "Dry Ingredients"
    assert ir.items["dry"]["items"][0]["id"] == "flour"
    assert ir.items["wet"]["name"] == "Wet Ingredients"
    assert ir.items["wet"]["dairy"]["name"] == "Dairy"
    assert ir.items["wet"]["dairy"]["items"][0]["id"] == "butter"


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
    assert by_id["prep"].subprocess_parent is None
    assert by_id["gather"].subprocess_parent == "prep"
    assert by_id["mix"].subprocess_parent == "prep"


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
    assert by_id["outer"].subprocess_parent is None
    assert by_id["inner"].subprocess_parent == "outer"
    assert by_id["inner_task"].subprocess_parent == "inner"


def test_compile_promotes_canonical_items_and_resources_to_ir_fields():
    parsed = {
        "spec_version": "0.1",
        "process": {
            "id": "p",
            "name": "Process",
            "items": [
                {"id": "order", "name": "Order", "kind": "information"},
                {"id": "dough", "name": "Dough", "kind": "material"},
            ],
            "resources": [
                {"id": "baker", "name": "Baker", "kind": "person"},
                {"id": "mixer", "name": "Mixer", "kind": "equipment"},
            ],
        },
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "transitions": [{"source": "start", "target": "end"}],
    }

    ir = compile_adapter(parsed)
    assert isinstance(ir.items, list)
    assert isinstance(ir.resources, list)
    assert ir.items[0]["id"] == "order"
    assert ir.resources[0]["id"] == "baker"
    assert ir.process_metadata is not None
    assert "items" not in ir.process_metadata
    assert "resources" not in ir.process_metadata


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
    assert ir.nodes[0].consumes == ["flour", "water"]
    assert ir.nodes[0].produces == ["dough"]
    assert ir.nodes[0].performed_by == ["lead_baker"]
    assert ir.nodes[0].uses == ["mixer"]


def test_compile_rejects_legacy_step_relation_aliases():
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

    with pytest.raises(ValueError, match="inputs"):
        compile_adapter(parsed)


def test_compile_preserves_explicit_handoff_on_transition():
    parsed = {
        "spec_version": "0.1",
        "process": {"id": "p", "name": "Process"},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "transitions": [
            {"source": "start", "target": "end", "handoff": {}},
        ],
    }

    ir = compile_adapter(parsed)
    assert len(ir.edges) == 1
    assert ir.edges[0].handoff == {}
