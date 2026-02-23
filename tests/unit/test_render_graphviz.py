from flo.render.graphviz_dot import render_flowchart_dot, render_swimlane_dot


def test_render_flowchart_dot():
    out = render_flowchart_dot({})
    assert "digraph" in out


def test_render_swimlane_dot():
    out = render_swimlane_dot({})
    assert "digraph" in out
