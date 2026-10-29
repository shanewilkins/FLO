import flo.source.models as models


def test_adapter_model_validate_and_dump(adapter_data):
    # exercise model_validate with dict-like input
    m = models.SourceDocument.model_validate(adapter_data)
    d = m.model_dump()
    assert d["process"]["name"] == adapter_data["process"]["name"]
    assert d["process"]["id"] == adapter_data["process"]["id"]
