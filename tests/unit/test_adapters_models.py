from flo.adapters.models import AdapterModel


def test_adapter_model_fallback_from_dict():
    data = {"name": "nm", "content": "ct"}
    model = AdapterModel.model_validate(data)
    assert model.name == "nm"
    assert model.content == "ct"
    dumped = model.model_dump()
    assert dumped["name"] == "nm"
    assert dumped["content"] == "ct"


def test_adapter_model_accepts_instance():
    inst = AdapterModel(name="a", content="b")
    out = AdapterModel.model_validate(inst)
    assert out is inst
