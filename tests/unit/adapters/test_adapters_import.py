from flo.source import parse_adapter


def test_parse_adapter_mapping():
    assert parse_adapter("process: {name: Example}") == {"process": {"name": "Example"}}
