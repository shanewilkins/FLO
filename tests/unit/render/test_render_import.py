from flo.render import render_artifact, render_dot


def test_render_artifact_stub(ir_factory, node_factory):
    ir = ir_factory(name="r", nodes=[node_factory("n", type="t")])
    artifact = render_artifact(ir)
    assert artifact.kind == "dot"
    assert artifact.backend == "graphviz"
    assert "digraph" in artifact.content


def test_render_dot_stub(ir_factory, node_factory):
    ir = ir_factory(name="r", nodes=[node_factory("n", type="t")])
    dot = render_dot(ir)
    assert isinstance(dot, str)
    assert "digraph" in dot
