from flo.compiler.ir import IR, Node, ir_to_schema_dict


def test_ir_schema_projection_emits_required_top_level_keys():
    ir = IR(
        name="demo",
        nodes=[
            Node(id="start", type="start", attrs={"name": "Start"}),
            Node(id="end", type="end", attrs={"name": "End"}),
        ],
        edges=[],
        process_metadata={"process_id": "p1", "process_name": "Demo Flow"},
    )

    out = ir_to_schema_dict(ir)

    assert set(out.keys()) == {"process", "nodes", "edges"}
    assert out["process"]["id"] == "p1"
    assert out["process"]["name"] == "Demo Flow"
    assert out["nodes"][0]["kind"] == "start"
