import pytest

from flo.process.analysis.scc import scc_condense


def test_condense_scc_not_implemented():
    with pytest.raises(TypeError):
        scc_condense({"a": {}})
