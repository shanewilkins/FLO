from flo.analysis import scc_condense
from flo.ir import IR, Node


def test_analysis_scc_stub():
    ir = IR(name="a", nodes=[Node(id="n", type="t")])
    out = scc_condense(ir)
    assert out is ir
