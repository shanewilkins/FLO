from flo.render import render_dot
from flo.ir import IR, Node


def test_render_dot_stub():
    ir = IR(name="r", nodes=[Node(id="n", type="t")])
    dot = render_dot(ir)
    assert isinstance(dot, str)
    assert "digraph" in dot
