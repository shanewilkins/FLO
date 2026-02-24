import pytest

from flo.compiler.analysis.scc import condense_scc


def test_condense_scc_not_implemented():
    with pytest.raises(NotImplementedError):
        condense_scc({"a": {}})
