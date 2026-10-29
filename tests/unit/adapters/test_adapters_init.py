import pytest

from flo.source import parse_adapter


def test_parse_adapter_preserves_yaml_mapping():
    assert parse_adapter("process: {id: p, name: Process}") == {
        "process": {"id": "p", "name": "Process"}
    }


def test_parse_adapter_rejects_plain_text():
    with pytest.raises(ValueError, match="YAML mapping"):
        parse_adapter("rawtext")


def test_parse_adapter_rejects_sequence():
    with pytest.raises(ValueError, match="YAML mapping"):
        parse_adapter("- item")
