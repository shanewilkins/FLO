import flo.adapters.models as models


def test_adapter_model_validate_and_dump(adapter_data):
    # exercise model_validate with dict-like input
    m = models.AdapterModel.model_validate(adapter_data)
    d = m.model_dump() if hasattr(m, "model_dump") else {"name": getattr(m, "name", ""), "content": getattr(m, "content", "")} 
    assert d["name"] == adapter_data["name"]
    assert d["content"] == adapter_data["content"]
