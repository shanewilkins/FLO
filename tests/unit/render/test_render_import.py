from flo.render import render_artifact


def test_render_artifact_stub(ir_factory, node_factory):
    ir = ir_factory(name="r", nodes=[node_factory("n", type="t")])
    artifact = render_artifact(ir)
    assert artifact.kind == "svg"
    assert artifact.backend == "svg"
    assert "<svg" in artifact.content
