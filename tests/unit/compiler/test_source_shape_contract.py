"""Executable contract tests for required authored step identity and kind."""

from __future__ import annotations

from typing import Any, cast

import pytest

from flo.source import compile_adapter


def _model(steps: list[Any]) -> dict[str, Any]:
    return {
        "spec_version": "0.1",
        "process": {"id": "shape_contract", "name": "Shape Contract"},
        "steps": steps,
    }


@pytest.mark.parametrize(
    ("steps", "message"),
    [
        ([], "steps must contain at least one step"),
        (["not-an-object"], r"steps\[0\] must be an object"),
        ([{"kind": "task"}], r"steps\[0\]\.id must be a non-empty string"),
        ([{"id": "work"}], r"steps\[0\]\.kind must be a non-empty string"),
        (
            [{"id": "work", "type": "task"}],
            r"steps\[0\] must use 'kind'; 'type' is not supported",
        ),
        (
            [{"id": "work", "kind": "unknown"}],
            r"steps\[0\]\.kind must be one of:",
        ),
    ],
)
def test_compile_rejects_malformed_step_shape(steps: list[Any], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        compile_adapter(cast(Any, _model(steps)))


def test_compile_rejects_duplicate_ids_across_subprocess_hierarchy() -> None:
    steps = [
        {"id": "work", "kind": "task"},
        {
            "id": "subprocess",
            "kind": "subprocess",
            "subnodes": [{"id": "work", "kind": "task"}],
        },
    ]

    with pytest.raises(ValueError, match="duplicate step id 'work'"):
        compile_adapter(cast(Any, _model(steps)))


def test_compile_rejects_nested_steps_on_non_subprocess() -> None:
    steps = [
        {
            "id": "work",
            "kind": "task",
            "subnodes": [{"id": "nested", "kind": "task"}],
        }
    ]

    with pytest.raises(ValueError, match="only for kind 'subprocess'"):
        compile_adapter(cast(Any, _model(steps)))
