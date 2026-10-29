"""Executable contract tests for required authored step identity and kind."""

from __future__ import annotations

from typing import Any, cast

import pytest

from flo.source import compile_adapter


def _profile(value=0, unit="min"):
    return {
        "basis": "observed",
        "results": {
            "mean": {"method": "mean", "value": value, "unit": unit},
        },
        "primary": "mean",
        "analysis_input": "mean",
    }


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
            r"steps\[0\]\.kind must be a non-empty string",
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
            "steps": [{"id": "work", "kind": "task"}],
        },
    ]

    with pytest.raises(ValueError, match="duplicate step id 'work'"):
        compile_adapter(cast(Any, _model(steps)))


@pytest.mark.parametrize("children", ["steps", "subnodes"])
def test_compile_rejects_nested_steps_on_non_subprocess(children: str) -> None:
    steps = [
        {
            "id": "work",
            "kind": "task",
            children: [{"id": "nested", "kind": "task"}],
        }
    ]

    with pytest.raises(
        ValueError,
        match="only for kind 'subprocess'"
        if children == "steps"
        else "subnodes is not supported",
    ):
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
            "routes cannot be declared",
        ),
    ],
)
def test_compile_rejects_invalid_branch_contract(
    step: dict[str, Any], error_code: str
) -> None:
    with pytest.raises(ValueError, match=error_code):
        compile_adapter(cast(Any, _model([step])))


def test_compile_preserves_task_wait_time() -> None:
    process = compile_adapter(
        cast(
            Any,
            _model(
                [
                    {"id": "start", "kind": "start"},
                    {
                        "id": "work",
                        "kind": "task",
                        "wait_time": _profile(),
                    },
                    {"id": "end", "kind": "end"},
                ]
            ),
        )
    )

    assert process.nodes[1].wait_time == _profile()


def test_compile_rejects_retired_timing_metadata() -> None:
    with pytest.raises(ValueError, match="metadata"):
        compile_adapter(
            cast(
                Any,
                _model(
                    [
                        {
                            "id": "work",
                            "kind": "task",
                            "metadata": {"wait_before": {"value": 1, "unit": "min"}},
                        }
                    ]
                ),
            )
        )


def test_compile_rejects_explicit_null_task_wait() -> None:
    with pytest.raises(ValueError, match="explicit null"):
        compile_adapter(
            cast(
                Any,
                _model([{"id": "work", "kind": "task", "wait_time": None}]),
            )
        )
