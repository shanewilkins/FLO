from __future__ import annotations

from types import SimpleNamespace

import pytest

from flo.render._svg_sppm_nodes import _node_svg
from flo.render.options import RenderOptions


@pytest.mark.parametrize(
    ("kind", "expected_snippets", "forbidden_snippets"),
    [
        (
            "task",
            ('data-node-kind="task"', 'data-node-header="top-rounded"'),
            ('data-node-queue-body="true"',),
        ),
        (
            "decision",
            ('data-node-kind="decision"', "<polygon"),
            ('data-node-header="top-rounded"',),
        ),
        (
            "queue",
            (
                'data-node-kind="queue"',
                'data-node-queue-body="true"',
                'data-node-queue-label-band="true"',
            ),
            (),
        ),
        (
            "subprocess",
            ('data-node-kind="subprocess"', "<ellipse"),
            ('data-node-header="top-rounded"',),
        ),
        (
            "start",
            ('data-node-kind="start"', '<rect x="10.0" y="20.0" width="180.0"'),
            ('data-node-header="top-rounded"',),
        ),
    ],
)
def test_node_svg_renders_kind_specific_geometry(
    kind: str,
    expected_snippets: tuple[str, ...],
    forbidden_snippets: tuple[str, ...],
) -> None:
    node = SimpleNamespace(id="n1", kind=kind, label="Node Label")
    raw_node = {
        "metadata": {"cycle_time": {"value": 5, "unit": "min"}},
        "workers": ["Alex"],
        "note": "Check this",
    }

    parts = _node_svg(
        node=node,
        raw_node=raw_node,
        options=RenderOptions(diagram="sppm", show_notes=True),
        x=10.0,
        y=20.0,
        width=180.0,
        height=120.0,
    )
    svg = "".join(parts)

    for snippet in expected_snippets:
        assert snippet in svg
    for snippet in forbidden_snippets:
        assert snippet not in svg


def test_node_svg_task_includes_info_lines_and_note() -> None:
    node = SimpleNamespace(id="t1", kind="task", label="Mix Dough")
    raw_node = {
        "metadata": {
            "cycle_time": {"value": 7, "unit": "min"},
            "description": "Combine ingredients",
        },
        "workers": ["Baker"],
        "note": "Use cold water",
    }

    parts = _node_svg(
        node=node,
        raw_node=raw_node,
        options=RenderOptions(diagram="sppm", show_notes=True),
        x=0.0,
        y=0.0,
        width=220.0,
        height=140.0,
    )
    svg = "".join(parts)

    assert "Combine ingredients" in svg
    assert "CT: 7 min" in svg
    assert "Workers: Baker" in svg
    assert "Note: Use cold water" in svg


def test_node_svg_decision_omits_info_lines_even_when_metadata_present() -> None:
    node = SimpleNamespace(id="d1", kind="decision", label="Quality OK?")
    raw_node = {
        "metadata": {
            "cycle_time": {"value": 12, "unit": "min"},
            "description": "Review output",
        },
        "workers": ["Inspector"],
        "note": "Escalate if needed",
    }

    parts = _node_svg(
        node=node,
        raw_node=raw_node,
        options=RenderOptions(diagram="sppm", show_notes=True),
        x=0.0,
        y=0.0,
        width=180.0,
        height=120.0,
    )
    svg = "".join(parts)

    assert "Quality OK?" in svg
    assert "CT:" not in svg
    assert "Workers:" not in svg
    assert "Note:" not in svg


def test_node_svg_queue_renders_wait_time_line() -> None:
    node = SimpleNamespace(id="q1", kind="queue", label="Prep Queue")
    raw_node = {"metadata": {"wait_time": {"value": 9, "unit": "min"}}}

    parts = _node_svg(
        node=node,
        raw_node=raw_node,
        options=RenderOptions(diagram="sppm"),
        x=20.0,
        y=30.0,
        width=160.0,
        height=160.0,
    )
    svg = "".join(parts)

    assert "Prep Queue" in svg
    assert "WT: 9 min" in svg
