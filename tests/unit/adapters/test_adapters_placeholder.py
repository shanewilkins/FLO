import pytest

from flo.source import parse_adapter


def test_parse_adapter_returns_mapping_for_yaml_document():
    payload = parse_adapter("name: demo\ncontent: hello")

    assert payload["name"] == "demo"
    assert payload["content"] == "hello"


def test_parse_adapter_rejects_plain_text_input():
    with pytest.raises(ValueError, match="YAML mapping"):
        parse_adapter("plain text input")
