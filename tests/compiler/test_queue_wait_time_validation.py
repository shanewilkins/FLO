"""Tests for queue/task semantic constraint validation.

Enforces:
  - wait_time ONLY on queue nodes
  - cycle_time and crossover_time ONLY on task nodes
"""

from __future__ import annotations

import pytest
from flo.compiler.ir.models import IR, Node, Edge
from flo.compiler.ir.validate import validate_ir
from flo.services.errors import ValidationError


class TestQueueWaitTimeSemantics:
    """Test queue/wait_time semantic constraint validation."""

    def test_queue_node_with_wait_time_valid(self) -> None:
        """Queue node with wait_time metadata is valid."""
        ir = IR(
            name="test_queue_with_wait_time",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="queue1",
                    type="queue",
                    attrs={"metadata": {"wait_time": {"value": 5, "unit": "min"}}},
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="queue1"),
                Edge(source="queue1", target="end"),
            ],
        )
        # Should not raise
        validate_ir(ir)

    def test_task_node_with_cycle_time_valid(self) -> None:
        """Task node with cycle_time metadata is valid."""
        ir = IR(
            name="test_task_with_cycle_time",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="task1",
                    type="task",
                    attrs={"metadata": {"cycle_time": {"value": 10, "unit": "min"}}},
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="task1"),
                Edge(source="task1", target="end"),
            ],
        )
        # Should not raise
        validate_ir(ir)

    def test_task_node_with_crossover_time_valid(self) -> None:
        """Task node with crossover_time metadata is valid."""
        ir = IR(
            name="test_task_with_crossover_time",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="task1",
                    type="task",
                    attrs={"metadata": {"crossover_time": {"value": 2, "unit": "min"}}},
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="task1"),
                Edge(source="task1", target="end"),
            ],
        )
        # Should not raise
        validate_ir(ir)

    def test_task_node_with_both_cycle_and_crossover_time_valid(self) -> None:
        """Task node with both cycle_time and crossover_time is valid."""
        ir = IR(
            name="test_task_with_both_cycle_and_crossover",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="task1",
                    type="task",
                    attrs={
                        "metadata": {
                            "cycle_time": {"value": 10, "unit": "min"},
                            "crossover_time": {"value": 2, "unit": "min"},
                        }
                    },
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="task1"),
                Edge(source="task1", target="end"),
            ],
        )
        # Should not raise
        validate_ir(ir)

    def test_system_task_with_cycle_time_valid(self) -> None:
        """System task node with cycle_time is valid."""
        ir = IR(
            name="test_system_task_with_cycle_time",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="sys_task",
                    type="system_task",
                    attrs={"metadata": {"cycle_time": {"value": 5, "unit": "min"}}},
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="sys_task"),
                Edge(source="sys_task", target="end"),
            ],
        )
        # Should not raise
        validate_ir(ir)

    def test_subprocess_with_cycle_time_valid(self) -> None:
        """Subprocess node with cycle_time is valid."""
        ir = IR(
            name="test_subprocess_with_cycle_time",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="subprocess",
                    type="subprocess",
                    attrs={"metadata": {"cycle_time": {"value": 15, "unit": "min"}}},
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="subprocess"),
                Edge(source="subprocess", target="end"),
            ],
        )
        # Should not raise
        validate_ir(ir)

    def test_task_with_wait_time_invalid(self) -> None:
        """Task node with wait_time is invalid."""
        ir = IR(
            name="test_task_with_wait_time_invalid",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="task1",
                    type="task",
                    attrs={"metadata": {"wait_time": {"value": 5, "unit": "min"}}},
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="task1"),
                Edge(source="task1", target="end"),
            ],
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_ir(ir)
        assert "E1503" in str(exc_info.value)
        assert "wait_time is only valid on queue nodes" in str(exc_info.value)

    def test_system_task_with_wait_time_invalid(self) -> None:
        """System task node with wait_time is invalid."""
        ir = IR(
            name="test_system_task_with_wait_time_invalid",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="sys_task",
                    type="system_task",
                    attrs={"metadata": {"wait_time": {"value": 3, "unit": "min"}}},
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="sys_task"),
                Edge(source="sys_task", target="end"),
            ],
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_ir(ir)
        assert "E1503" in str(exc_info.value)

    def test_subprocess_with_wait_time_invalid(self) -> None:
        """Subprocess node with wait_time is invalid."""
        ir = IR(
            name="test_subprocess_with_wait_time_invalid",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="subprocess",
                    type="subprocess",
                    attrs={"metadata": {"wait_time": {"value": 7, "unit": "min"}}},
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="subprocess"),
                Edge(source="subprocess", target="end"),
            ],
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_ir(ir)
        assert "E1503" in str(exc_info.value)

    def test_queue_with_cycle_time_invalid(self) -> None:
        """Queue node with cycle_time is invalid."""
        ir = IR(
            name="test_queue_with_cycle_time_invalid",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="queue1",
                    type="queue",
                    attrs={"metadata": {"cycle_time": {"value": 10, "unit": "min"}}},
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="queue1"),
                Edge(source="queue1", target="end"),
            ],
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_ir(ir)
        assert "E1501" in str(exc_info.value)
        assert "Queues represent delays only" in str(exc_info.value)

    def test_queue_with_crossover_time_invalid(self) -> None:
        """Queue node with crossover_time is invalid."""
        ir = IR(
            name="test_queue_with_crossover_time_invalid",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="queue1",
                    type="queue",
                    attrs={"metadata": {"crossover_time": {"value": 2, "unit": "min"}}},
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="queue1"),
                Edge(source="queue1", target="end"),
            ],
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_ir(ir)
        assert "E1502" in str(exc_info.value)

    def test_queue_with_transfer_time_invalid(self) -> None:
        """Queue node with transfer_time is invalid."""
        ir = IR(
            name="test_queue_with_transfer_time_invalid",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="queue1",
                    type="queue",
                    attrs={"metadata": {"transfer_time": {"value": 1, "unit": "min"}}},
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="queue1"),
                Edge(source="queue1", target="end"),
            ],
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_ir(ir)
        assert "E1502" in str(exc_info.value)

    def test_queue_with_changeover_time_invalid(self) -> None:
        """Queue node with changeover_time is invalid."""
        ir = IR(
            name="test_queue_with_changeover_time_invalid",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="queue1",
                    type="queue",
                    attrs={
                        "metadata": {"changeover_time": {"value": 3, "unit": "min"}}
                    },
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="queue1"),
                Edge(source="queue1", target="end"),
            ],
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_ir(ir)
        assert "E1502" in str(exc_info.value)

    def test_mixed_workflow_with_queue_and_task_valid(self) -> None:
        """Complex workflow with queue then task is valid."""
        ir = IR(
            name="test_mixed_workflow",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="queue1",
                    type="queue",
                    attrs={"metadata": {"wait_time": {"value": 5, "unit": "min"}}},
                ),
                Node(
                    id="task1",
                    type="task",
                    attrs={
                        "metadata": {
                            "cycle_time": {"value": 10, "unit": "min"},
                            "crossover_time": {"value": 2, "unit": "min"},
                        }
                    },
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="queue1"),
                Edge(source="queue1", target="task1"),
                Edge(source="task1", target="end"),
            ],
        )
        # Should not raise
        validate_ir(ir)

    def test_multiple_queues_valid(self) -> None:
        """Multiple queue nodes each with wait_time is valid."""
        ir = IR(
            name="test_multiple_queues",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="queue1",
                    type="queue",
                    attrs={"metadata": {"wait_time": {"value": 5, "unit": "min"}}},
                ),
                Node(
                    id="task1",
                    type="task",
                    attrs={"metadata": {"cycle_time": {"value": 10, "unit": "min"}}},
                ),
                Node(
                    id="queue2",
                    type="queue",
                    attrs={"metadata": {"wait_time": {"value": 3, "unit": "min"}}},
                ),
                Node(
                    id="task2",
                    type="task",
                    attrs={"metadata": {"cycle_time": {"value": 15, "unit": "min"}}},
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="queue1"),
                Edge(source="queue1", target="task1"),
                Edge(source="task1", target="queue2"),
                Edge(source="queue2", target="task2"),
                Edge(source="task2", target="end"),
            ],
        )
        # Should not raise
        validate_ir(ir)

    def test_error_message_is_actionable_task_with_wait_time(self) -> None:
        """Error message for task with wait_time is actionable."""
        ir = IR(
            name="test_error_task_wait_time",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="problematic_task",
                    type="task",
                    attrs={"metadata": {"wait_time": {"value": 5, "unit": "min"}}},
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="problematic_task"),
                Edge(source="problematic_task", target="end"),
            ],
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_ir(ir)
        error_msg = str(exc_info.value)
        assert "problematic_task" in error_msg
        assert "insert a queue node before this task" in error_msg

    def test_error_message_is_actionable_queue_with_cycle_time(self) -> None:
        """Error message for queue with cycle_time is actionable."""
        ir = IR(
            name="test_error_queue_cycle_time",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="problematic_queue",
                    type="queue",
                    attrs={"metadata": {"cycle_time": {"value": 10, "unit": "min"}}},
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="problematic_queue"),
                Edge(source="problematic_queue", target="end"),
            ],
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_ir(ir)
        error_msg = str(exc_info.value)
        assert "problematic_queue" in error_msg
        assert "Cycle time belongs on task nodes" in error_msg
