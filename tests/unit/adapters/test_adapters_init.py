def test_parse_adapter_uses_model_dump(monkeypatch):
    # Create a dummy model with model_dump
    class DummyModel:
        def model_dump(self):
            return {"a": 1}

    monkeypatch.setattr(
        "flo.adapters.load_adapter_from_yaml",
        lambda content: DummyModel(),
    )

    from flo.adapters import parse_adapter

    assert parse_adapter("irrelevant") == {"a": 1}


def test_parse_adapter_falls_back_on_value_error(monkeypatch):
    monkeypatch.setattr(
        "flo.adapters.load_adapter_from_yaml",
        lambda content: (_ for _ in ()).throw(ValueError("bad yaml")),
    )

    from flo.adapters import parse_adapter

    assert parse_adapter("rawtext") == {"name": "parsed", "content": "rawtext"}


def test_parse_adapter_dict_fallback(monkeypatch):
    # model_dump exists but raises, then dict(model) should be used
    class FallbackModel:
        def model_dump(self):
            raise RuntimeError("no dump")

        def __iter__(self):
            yield ("x", 42)

    monkeypatch.setattr(
        "flo.adapters.load_adapter_from_yaml",
        lambda content: FallbackModel(),
    )

    from flo.adapters import parse_adapter

    assert parse_adapter("irrelevant") == {"x": 42}
