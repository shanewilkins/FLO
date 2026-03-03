from pathlib import Path
from flo.compiler.ir.models import Edge, IR


def test_ir_to_from_dict_and_json(tmp_path: Path, ir_factory, node_factory):
    nodes = [node_factory("n1", attrs={"foo": "bar"}), node_factory("n2", type="end")]
    ir = ir_factory(name="test", nodes=nodes)

    d = ir.to_dict()
    assert d["name"] == "test"
    assert isinstance(d["nodes"], list)

    s = ir.to_json()
    assert '"name": "test"' in s

    # write to file and read via from_dict
    p = tmp_path / "ir.json"
    ir.to_json(path=str(p))
    loaded = IR.from_dict({"name": "x", "nodes": d["nodes"]})
    assert loaded.name == "x"
    assert any(n.id == "n1" for n in loaded.nodes)


def test_ir_edge_optional_fields_roundtrip(tmp_path: Path):
    ir = IR(
        name="edges",
        nodes=[],
        edges=[
            Edge(
                source="a",
                target="b",
                id="e1",
                outcome="yes",
                label="approve",
                metadata={"k": "v"},
            ),
            Edge(source="b", target="c"),
        ],
    )

    data = ir.to_dict()
    assert data["edges"][0]["id"] == "e1"
    assert data["edges"][0]["outcome"] == "yes"
    assert data["edges"][0]["label"] == "approve"
    assert data["edges"][0]["metadata"] == {"k": "v"}
    assert "id" not in data["edges"][1]

    p = tmp_path / "edges.json"
    text = ir.to_json(path=p)
    assert p.exists()
    assert "\"edges\"" in text


def test_ir_from_dict_defaults_for_missing_fields():
    data = {
        "name": "demo",
        "nodes": [{"id": "n1", "type": "task"}],
        "edges": [{"source": "n1", "target": "n2"}],
    }
    ir = IR.from_dict(data)
    assert ir.name == "demo"
    assert ir.nodes[0].attrs == {}
    assert ir.edges[0].id is None
    assert ir.edges[0].outcome is None
