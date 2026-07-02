from pathlib import Path
from flo.compiler.ir.models import Edge, IR
from flo.compiler.ir._internal_shape import (
    ir_from_internal_dict,
    ir_to_internal_dict,
    ir_to_internal_json,
)


def test_ir_to_from_dict_and_json(tmp_path: Path, ir_factory, node_factory):
    nodes = [node_factory("n1", attrs={"foo": "bar"}), node_factory("n2", type="end")]
    ir = ir_factory(name="test", nodes=nodes)

    d = ir_to_internal_dict(ir)
    assert d["name"] == "test"
    assert isinstance(d["nodes"], list)

    s = ir_to_internal_json(ir)
    assert '"name": "test"' in s

    # write to file and read via from_internal_dict
    p = tmp_path / "ir.json"
    ir_to_internal_json(ir, path=str(p))
    loaded = ir_from_internal_dict({"name": "x", "nodes": d["nodes"]})
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
                edge_type="rework",
                rework=True,
                metadata={"k": "v"},
            ),
            Edge(source="b", target="c"),
        ],
    )

    data = ir_to_internal_dict(ir)
    assert data["edges"][0]["id"] == "e1"
    assert data["edges"][0]["outcome"] == "yes"
    assert data["edges"][0]["label"] == "approve"
    assert data["edges"][0]["edge_type"] == "rework"
    assert data["edges"][0]["rework"] is True
    assert data["edges"][0]["metadata"] == {"k": "v"}
    assert "id" not in data["edges"][1]

    p = tmp_path / "edges.json"
    text = ir_to_internal_json(ir, path=p)
    assert p.exists()
    assert '"edges"' in text


def test_ir_from_internal_dict_defaults_for_missing_fields():
    data = {
        "name": "demo",
        "nodes": [{"id": "n1", "type": "task"}],
        "edges": [{"source": "n1", "target": "n2"}],
    }
    ir = ir_from_internal_dict(data)
    assert ir.name == "demo"
    assert ir.nodes[0].attrs == {}
    assert ir.edges[0].id is None
    assert ir.edges[0].outcome is None


def test_ir_from_internal_dict_preserves_edge_type_and_rework():
    data = {
        "name": "demo",
        "nodes": [{"id": "n1", "type": "task"}],
        "edges": [
            {"source": "n1", "target": "n2", "edge_type": "rework", "rework": True}
        ],
    }
    ir = ir_from_internal_dict(data)
    assert ir.edges[0].edge_type == "rework"
    assert ir.edges[0].rework is True


def test_ir_normalizes_non_object_attrs_and_metadata_at_construction() -> None:
    ir = IR(
        name="demo",
        nodes=[{"id": "n1", "type": "task", "attrs": "bad"}],
        edges=[{"source": "n1", "target": "n2", "metadata": "bad"}],
        process_metadata="bad",
    )

    assert ir.nodes[0].attrs == {}
    assert ir.edges[0].metadata is None
    assert ir.process_metadata is None
