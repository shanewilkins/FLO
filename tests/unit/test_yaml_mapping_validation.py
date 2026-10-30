import pytest

from flo.source import parse_adapter


def test_load_adapter_valid():
    y = """
name: test
content: ok
"""
    model = parse_adapter(y)
    assert model["name"] == "test"
    assert model["content"] == "ok"


def test_load_adapter_invalid_raises():
    y = "- just\n- a\n- list"
    with pytest.raises(
        ValueError,
        match=r"FLO source must contain a YAML mapping",
    ):
        parse_adapter(y)
