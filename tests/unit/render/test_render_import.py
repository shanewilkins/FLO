from flo.render import render_dot


def test_render_dot_stub(ir_factory, node_factory):
    ir = ir_factory(name="r", nodes=[node_factory("n", type="t")])
    dot = render_dot(ir)
    assert isinstance(dot, str)
    assert "digraph" in dot
