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


def test_compile_preserves_step_location_workers_and_equipment():
    parsed = {
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


def test_compile_flattens_subprocess_subnodes():
    parsed = {
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
