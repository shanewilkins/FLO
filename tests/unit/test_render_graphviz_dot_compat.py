from flo.render import graphviz_backend, graphviz_dot


def test_graphviz_dot_exports_match_backend_entrypoints():
    assert graphviz_dot.render_flowchart_dot is graphviz_backend.render_flowchart_dot
    assert graphviz_dot.render_swimlane_dot is graphviz_backend.render_swimlane_dot
    assert graphviz_dot.render_spaghetti_dot is graphviz_backend.render_spaghetti_dot
    assert graphviz_dot.render_sppm_dot is graphviz_backend.render_sppm_dot


def test_graphviz_dot_declares_expected_public_symbols():
    assert graphviz_dot.__all__ == [
        "render_flowchart_dot",
        "render_swimlane_dot",
        "render_spaghetti_dot",
        "render_sppm_dot",
    ]
