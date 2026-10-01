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


@pytest.mark.parametrize(
    ("step", "error_code"),
    [
        ({"id": "assign", "kind": "branch"}, "E0215"),
        (
            {"id": "assign", "kind": "branch", "branch": {"mode": "least_loaded"}},
            "E0216",
        ),
        (
            {
                "id": "assign",
                "kind": "branch",
                "branch": {"mode": "dispatch", "policy": ""},
            },
            "E0217",
        ),
        (
            {
                "id": "assign",
                "kind": "branch",
                "branch": {
                    "mode": "dispatch",
                    "eligible_resources": ["worker", "worker"],
                },
            },
            "E0218",
        ),
        (
            {
                "id": "work",
                "kind": "task",
                "routes": {"left": "a", "right": "b"},
            },
            "E0211",
        ),
    ],
)
def test_compile_rejects_invalid_branch_contract(
    step: dict[str, Any], error_code: str
) -> None:
    with pytest.raises(ValueError, match=error_code):
        compile_adapter(cast(Any, _model([step])))


def test_compile_normalizes_task_wait_time_to_wait_before() -> None:
    process = compile_adapter(
        cast(
            Any,
            _model(
                [
                    {"id": "start", "kind": "start"},
                    {
                        "id": "work",
                        "kind": "task",
                        "metadata": {
                            "wait_time": {
                                "value": 0,
                                "unit": "min",
                                "measurement_id": "work_wait",
                            }
                        },
                    },
                    {"id": "end", "kind": "end"},
                ]
            ),
        )
    )

    metadata = process.nodes[1].attrs["metadata"]
    assert "wait_time" not in metadata
    assert metadata["wait_before"] == {
        "value": 0,
        "unit": "min",
        "measurement_id": "work_wait",
    }


def test_compile_rejects_both_task_wait_alias_and_canonical_field() -> None:
    with pytest.raises(ValueError, match="E0219"):
        compile_adapter(
            cast(
                Any,
                _model(
                    [
                        {
                            "id": "work",
                            "kind": "task",
                            "metadata": {
                                "wait_time": {"value": 1, "unit": "min"},
                                "wait_before": {"value": 1, "unit": "min"},
                            },
                        }
                    ]
                ),
            )
        )


def test_compile_preserves_invalid_null_task_wait_for_validation() -> None:
    process = compile_adapter(
        cast(
            Any,
            _model(
                [
                    {
                        "id": "work",
                        "kind": "task",
                        "metadata": {"wait_time": None},
                    }
                ]
            ),
        )
    )

    assert process.nodes[0].attrs["metadata"] == {"wait_before": None}
