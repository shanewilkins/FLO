from pathlib import Path
from flo.compiler.ir.models import IR


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
