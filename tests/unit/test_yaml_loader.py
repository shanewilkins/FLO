import pytest

from flo.adapters.yaml_loader import load_adapter_from_yaml


def test_load_adapter_valid():
    y = """
name: test
content: ok
"""
    model = load_adapter_from_yaml(y)
    assert model.name == "test"
    assert model.content == "ok"


def test_load_adapter_invalid_raises():
    y = "- just\n- a\n- list"
    with pytest.raises(ValueError):
        load_adapter_from_yaml(y)
