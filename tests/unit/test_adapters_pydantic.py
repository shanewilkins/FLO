import importlib
import sys
import types


def test_adapters_models_pydantic_branch(monkeypatch):
    # Simulate a minimal pydantic with BaseModel that supports model_validate
    fake_pyd = types.ModuleType("pydantic")

    class FakeBaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

        @classmethod
        def model_validate(cls, data):
            return cls(**data)

    fake_pyd.BaseModel = FakeBaseModel

    orig = sys.modules.get("pydantic")
    sys.modules["pydantic"] = fake_pyd
    try:
        import flo.adapters.models as models
        importlib.reload(models)
        AdapterModel = models.AdapterModel
        inst = AdapterModel.model_validate({"name": "n", "content": "c"})
        assert hasattr(inst, "name") and inst.name == "n"
        # model_dump may not exist on fake; ensure inst has attributes
    finally:
        # restore original module and reload to fallback behaviour
        if orig is not None:
            sys.modules["pydantic"] = orig
        else:
            del sys.modules["pydantic"]
        importlib.reload(sys.modules["flo.adapters.models"])
