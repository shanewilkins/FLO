from flo.analysis import scc_condense


def test_analysis_scc_stub(ir_factory, node_factory):
    ir = ir_factory(name="a", nodes=[node_factory("n", type="t")])
    out = scc_condense(ir)
    assert out is ir
