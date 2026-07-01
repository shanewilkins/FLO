from flo.adapters import parse_adapter


def test_parse_adapter_returns_mapping_for_yaml_document():
    payload = parse_adapter("name: demo\ncontent: hello")

    assert payload["name"] == "demo"
    assert payload["content"] == "hello"


def test_parse_adapter_preserves_plain_text_input_via_fallback():
    payload = parse_adapter("plain text input")

    assert payload["name"] == "parsed"
    assert payload["content"] == "plain text input"
