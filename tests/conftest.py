"""conftest fixtures re-exports for pytest discovery."""

from tests.fixtures.sample_fixtures import tmp_flo_file, adapter_model_from_example  # re-export fixtures

__all__ = ["tmp_flo_file", "adapter_model_from_example"]

import pytest
from typing import Callable
from flo.ir.models import Node, IR


@pytest.fixture
def node_factory() -> Callable:
    def _node(id: str, type: str = "task", attrs: dict | None = None) -> Node:
        return Node(id=id, type=type, attrs=attrs or {})

    return _node


@pytest.fixture
def ir_factory(node_factory) -> Callable:
    def _ir(name: str, nodes: list[Node]) -> IR:
        return IR(name=name, nodes=nodes)

    return _ir


@pytest.fixture
def adapter_data() -> dict:
    return {"name": "example", "content": "payload"}
