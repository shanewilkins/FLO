import pytest

from flo.source.yaml_loader import load_adapter_from_yaml


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
    with pytest.raises(
        ValueError,
        match=r"^YAML content must be a mapping with keys 'name' and 'content'$",
    ):
        load_adapter_from_yaml(y)
