from flo.adapters import parse_adapter


def test_parse_adapter_stub():
    parsed = parse_adapter("some content")
    assert isinstance(parsed, dict)
    assert parsed.get("content") == "some content"
