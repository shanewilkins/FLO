from flo.adapters.models import AdapterModel


def test_adapter_model_fallback_from_dict(adapter_data):
    model = AdapterModel.model_validate(adapter_data)
    assert model.name == adapter_data["name"]
    assert model.content == adapter_data["content"]
    dumped = model.model_dump()
    assert dumped["name"] == adapter_data["name"]
    assert dumped["content"] == adapter_data["content"]


def test_adapter_model_accepts_instance(adapter_data):
    inst = AdapterModel(name=adapter_data["name"], content=adapter_data["content"])
    out = AdapterModel.model_validate(inst)
    assert out is inst
