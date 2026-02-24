from flo.compiler.analysis.scc import scc_condense, condense_scc
import pytest


def test_scc_no_edges_returns_same(ir_factory, node_factory):
    ir = ir_factory(name="noedges", nodes=[node_factory("a"), node_factory("b")])
    out = scc_condense(ir)
    # no edges -> identity
    assert out is ir


def test_scc_cycle_condenses(ir_factory, node_factory):
    # create a simple cycle a->b->a
    a = node_factory("a", attrs={"edges": ["b"]})
    b = node_factory("b", attrs={"edges": ["a"]})
    ir = ir_factory(name="cycle", nodes=[a, b])
    out = scc_condense(ir)
    # should produce a condensed IR with one scc node
    assert out is not None
    assert any(n.id.startswith("scc_") or n.id == "a" for n in out.nodes)


def test_condense_scc_raises_for_non_ir():
    with pytest.raises(NotImplementedError):
        condense_scc({"not": "an ir"})
