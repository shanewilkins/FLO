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
    def _node(id: str, type: str = "task", **fields) -> Node:
        return Node(id=id, type=type, **fields)

    return _node


@pytest.fixture
def ir_factory(node_factory) -> Callable:
    def _ir(name: str, nodes: list[Node], edges=None) -> IR:
        return IR(name=name, nodes=nodes, edges=edges or [])

    return _ir


@pytest.fixture
def adapter_data() -> dict:
    return {
        "spec_version": "0.1",
        "process": {"id": "example", "name": "Example"},
        "steps": [{"id": "start", "kind": "start"}],
    }


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
