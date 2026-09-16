"""Tests for queue/task waiting semantic validation.

Enforces:
    - wait_time is canonical on queue nodes
    - wait_before is canonical on work nodes
  - cycle_time and crossover_time ONLY on task nodes
"""

from __future__ import annotations

import pytest

from flo.errors import ValidationError
from flo.process.ir.models import IR, Edge, Node
from flo.process.ir.validate import validate_ir


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

    def test_task_node_with_wait_before_valid(self) -> None:
        """Task nodes preserve worksheet wait as canonical wait_before."""
        ir = IR(
            name="test_task_with_wait_before",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="task1",
                    type="task",
                    attrs={"metadata": {"wait_before": {"value": 5, "unit": "min"}}},
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="task1"),
                Edge(source="task1", target="end"),
            ],
        )

        validate_ir(ir)

    def test_task_node_with_null_wait_before_is_invalid(self) -> None:
        ir = IR(
            name="test_task_with_null_wait_before",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="task1",
                    type="task",
                    attrs={"metadata": {"wait_before": None}},
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="task1"),
                Edge(source="task1", target="end"),
            ],
        )

        with pytest.raises(ValidationError, match=r"E1301.*wait_before"):
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
        assert "Canonical work-node metadata uses wait_before" in str(exc_info.value)

    def test_linked_queue_and_task_wait_measurement_is_valid(self) -> None:
        """A promoted queue and task row may project the same measurement."""
        wait = {"value": 5, "unit": "min", "measurement_id": "wash_wait"}
        ir = IR(
            name="linked_wait",
            nodes=[
                Node(id="start", type="start"),
                Node(id="queue", type="queue", attrs={"metadata": {"wait_time": wait}}),
                Node(
                    id="work",
                    type="task",
                    attrs={"metadata": {"wait_before": dict(wait)}},
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="queue"),
                Edge(source="queue", target="work"),
                Edge(source="work", target="end"),
            ],
        )

        validate_ir(ir)

    def test_aggregate_queue_projection_references_task_measurements(self) -> None:
        """A promoted queue may aggregate several task-row wait measurements."""
        ir = IR(
            name="aggregate_wait",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="queue",
                    type="queue",
                    attrs={
                        "metadata": {
                            "wait_time": {
                                "value": 6,
                                "unit": "min",
                                "measurement_refs": ["wash_wait", "dry_wait"],
                            }
                        }
                    },
                ),
                Node(
                    id="wash",
                    type="task",
                    attrs={
                        "metadata": {
                            "wait_before": {
                                "value": 5,
                                "unit": "min",
                                "measurement_id": "wash_wait",
                            }
                        }
                    },
                ),
                Node(
                    id="dry",
                    type="task",
                    attrs={
                        "metadata": {
                            "wait_before": {
                                "value": 1,
                                "unit": "min",
                                "measurement_id": "dry_wait",
                            }
                        }
                    },
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="queue"),
                Edge(source="queue", target="wash"),
                Edge(source="wash", target="dry"),
                Edge(source="dry", target="end"),
            ],
        )

        validate_ir(ir)

    def test_overlapping_queue_and_task_wait_requires_measurement_identity(
        self,
    ) -> None:
        """Potential duplicate waiting fails with an actionable diagnostic."""
        ir = IR(
            name="ambiguous_wait",
            nodes=[
                Node(id="start", type="start"),
                Node(
                    id="queue",
                    type="queue",
                    attrs={"metadata": {"wait_time": {"value": 5, "unit": "min"}}},
                ),
                Node(
                    id="work",
                    type="task",
                    attrs={"metadata": {"wait_before": {"value": 5, "unit": "min"}}},
                ),
                Node(id="end", type="end"),
            ],
            edges=[
                Edge(source="start", target="queue"),
                Edge(source="queue", target="work"),
                Edge(source="work", target="end"),
            ],
        )

        with pytest.raises(ValidationError, match=r"E1505.*measurement_id"):
            validate_ir(ir)

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
        assert "Canonical work-node metadata uses wait_before" in error_msg

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
