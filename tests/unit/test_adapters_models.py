from flo.source.models import SourceDocument


def test_adapter_model_fallback_from_dict(adapter_data):
    model = SourceDocument.model_validate(adapter_data)
    assert model.process.name == adapter_data["process"]["name"]
    assert model.process.id == adapter_data["process"]["id"]
    dumped = model.model_dump()
    assert dumped["process"]["name"] == adapter_data["process"]["name"]
    assert dumped["process"]["id"] == adapter_data["process"]["id"]


def test_adapter_model_accepts_instance(adapter_data):
    inst = SourceDocument.model_validate(adapter_data)
    out = SourceDocument.model_validate(inst)
    assert out is inst
