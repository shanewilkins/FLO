"""conftest fixtures re-exports for pytest discovery."""

from tests.fixtures.sample_fixtures import (
    adapter_model_from_example,
    repo_root,
    tmp_flo_file,
)  # re-export fixtures

__all__ = ["adapter_model_from_example", "repo_root", "tmp_flo_file"]

import contextlib
from collections.abc import Callable

import pytest

from flo.app import get_services
from flo.process.ir.models import IR, Node


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


@pytest.fixture
def services():
    """Provide a `Services` instance for tests and ensure telemetry is shut down.

    Use this fixture in integration tests to guarantee exporters are closed
    during teardown so tests do not see exporter-related I/O warnings.
    """
    svc = get_services(verbose=False)
    try:
        yield svc
    finally:
        with contextlib.suppress(Exception):
            svc.telemetry.shutdown()
