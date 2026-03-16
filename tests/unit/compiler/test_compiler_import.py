from flo.compiler import compile_adapter
from flo.compiler.ir import IR


def test_compile_adapter_stub():
    parsed = {"name": "x", "content": "c"}
    ir = compile_adapter(parsed)
    assert isinstance(ir, IR)
    assert ir.name == "x"


def test_compile_accepts_transitions_key_for_explicit_connections():
    parsed = {
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


def test_compile_preserves_edges_alias_for_backwards_compatibility():
    parsed = {
        "process": {"id": "p", "name": "Process"},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "end"},
        ],
    }

    ir = compile_adapter(parsed)
    assert len(ir.edges) == 1
    assert ir.edges[0].source == "start"
    assert ir.edges[0].target == "end"


def test_compile_prefers_transitions_over_edges_when_both_provided():
    parsed = {
        "process": {"id": "p", "name": "Process"},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "task_a", "kind": "task", "name": "Task A"},
            {"id": "task_b", "kind": "task", "name": "Task B"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "transitions": [
            {"source": "start", "target": "task_b"},
            {"source": "task_b", "target": "end"},
        ],
        "edges": [
            {"source": "start", "target": "task_a"},
            {"source": "task_a", "target": "end"},
        ],
    }

    ir = compile_adapter(parsed)
    pairs = [(edge.source, edge.target) for edge in ir.edges]
    assert pairs == [("start", "task_b"), ("task_b", "end")]


def test_compile_accepts_from_to_transition_keys():
    parsed = {
        "process": {"id": "p", "name": "Process"},
        "steps": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "transitions": [
            {"from": "start", "to": "end"},
        ],
    }

    ir = compile_adapter(parsed)
    assert len(ir.edges) == 1
    assert ir.edges[0].source == "start"
    assert ir.edges[0].target == "end"


def test_compile_preserves_node_metadata():
    parsed = {
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


def test_compile_promotes_top_level_resources_to_process_metadata():
    parsed = {
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
        "edges": [
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


def test_compile_promotes_grouped_materials_to_process_metadata():
    parsed = {
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
        "edges": [
            {"source": "start", "target": "end"},
        ],
    }

    ir = compile_adapter(parsed)
    assert ir.process_metadata is not None
    assert ir.process_metadata["materials"]["dry"]["name"] == "Dry Ingredients"
    assert ir.process_metadata["materials"]["dry"]["items"][0]["id"] == "flour"
    assert ir.process_metadata["materials"]["wet"]["name"] == "Wet Ingredients"
    assert ir.process_metadata["materials"]["wet"]["dairy"]["name"] == "Dairy"
    assert ir.process_metadata["materials"]["wet"]["dairy"]["items"][0]["id"] == "butter"
