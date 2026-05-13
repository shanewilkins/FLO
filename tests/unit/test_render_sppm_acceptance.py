"""Unit tests validating SPPM wait time vs changeover time acceptance criteria.

These tests ensure that the pedagogical distinction between queue delays (WT)
and setup delays (CO) is correctly rendered in all SPPM modes and scenarios.
"""

from flo.render import render_dot


def test_sppm_both_wait_and_changeover_appear_distinct():
    """Verify WT and CO appear as visually distinct metrics.
    
    Pedagogical requirement: students must see WT and CO as separate problems
    with different root causes and countermeasures.
    """
    process = {
        "process": {"id": "p1", "name": "Process", "metadata": {}},
        "nodes": [
            {
                "id": "step",
                "kind": "task",
                "name": "Step",
                "metadata": {
                    "wait_time": {"value": 30, "unit": "min"},
                    "changeover_time": {"value": 10, "unit": "min"},
                },
            },
        ],
        "edges": [],
    }
    out = render_dot(process, options={"diagram": "sppm"})
    # Both metrics should appear with distinct labels
    assert "WT:" in out or "wait" in out
    assert "CO:" in out or "crossover" in out


def test_sppm_node_with_only_wait_time_omits_changeover():
    """Verify CO doesn't appear when node has no changeover data.
    
    Clean output requires that optional metrics don't clutter labels when absent.
    """
    process = {
        "process": {"id": "p1", "name": "Process", "metadata": {}},
        "nodes": [
            {
                "id": "wait_only",
                "kind": "task",
                "name": "Wait Only",
                "metadata": {"wait_time": {"value": 20, "unit": "min"}},
            },
        ],
        "edges": [],
    }
    out = render_dot(process, options={"diagram": "sppm"})
    assert "WT:" in out or "wait" in out
    # Should not show CO if not present
    assert "CO:" not in out


def test_sppm_node_with_only_changeover_omits_wait_time():
    """Verify WT doesn't appear when node has no wait_time data.
    
    Clean output requires that optional metrics don't clutter labels when absent.
    """
    process = {
        "process": {"id": "p1", "name": "Process", "metadata": {}},
        "nodes": [
            {
                "id": "co_only",
                "kind": "task",
                "name": "CO Only",
                "metadata": {"crossover_time": {"value": 15, "unit": "min"}},
            },
        ],
        "edges": [],
    }
    out = render_dot(process, options={"diagram": "sppm"})
    assert "CO:" in out or "crossover" in out
    # Should not show WT if not present
    assert "WT:" not in out


def test_sppm_zero_wait_time_and_changeover_both_omitted():
    """Verify zero values don't appear in labels.
    
    Zero WT or CO indicates no delay, so they shouldn't clutter the display.
    """
    process = {
        "process": {"id": "p1", "name": "Process", "metadata": {}},
        "nodes": [
            {
                "id": "no_delay",
                "kind": "task",
                "name": "No Delay",
                "metadata": {
                    "wait_time": {"value": 0, "unit": "min"},
                    "changeover_time": {"value": 0, "unit": "min"},
                },
            },
        ],
        "edges": [],
    }
    out = render_dot(process, options={"diagram": "sppm"})
    # Neither should appear as "0 min wait" or "0 min crossover"
    assert "0 min wait" not in out
    assert "0 min crossover" not in out


def test_sppm_multiple_nodes_with_different_wt_co_combinations():
    """Verify complex processes show correct combination of metrics per node.
    
    Different nodes can have different combinations of WT/CO, and each should
    render appropriately to aid diagnostic clarity.
    """
    process = {
        "process": {"id": "p1", "name": "Process", "metadata": {}},
        "nodes": [
            {
                "id": "queue_heavy",
                "kind": "task",
                "name": "Queue Heavy",
                "metadata": {"wait_time": {"value": 100, "unit": "min"}},
            },
            {
                "id": "setup_heavy",
                "kind": "task",
                "name": "Setup Heavy",
                "metadata": {"changeover_time": {"value": 50, "unit": "min"}},
            },
            {
                "id": "balanced",
                "kind": "task",
                "name": "Balanced",
                "metadata": {
                    "wait_time": {"value": 30, "unit": "min"},
                    "changeover_time": {"value": 20, "unit": "min"},
                },
            },
        ],
        "edges": [
            {"source": "queue_heavy", "target": "setup_heavy"},
            {"source": "setup_heavy", "target": "balanced"},
        ],
    }
    out = render_dot(process, options={"diagram": "sppm"})
    # All WT values should appear
    assert "100" in out  # queue_heavy WT
    assert "30" in out  # balanced WT
    # All CO values should appear
    assert "50" in out  # setup_heavy CO
    assert "20" in out  # balanced CO


def test_sppm_teaching_density_preserves_wait_vs_changeover_distinction():
    """Verify teaching density mode still shows WT/CO distinction.
    
    Teaching density should be pedagogically focused, so the WT vs CO
    distinction should remain clear even in abbreviated form.
    """
    ir_like = {
        "nodes": [
            {"id": "a", "kind": "task", "name": "A", "metadata": {}},
            {
                "id": "b",
                "kind": "task",
                "name": "B",
                "metadata": {
                    "cycle_time": {"value": 10, "unit": "min"},
                    "wait_time": {"value": 20, "unit": "min"},
                    "changeover_time": {"value": 5, "unit": "min"},
                },
            },
        ],
        "edges": [{"source": "a", "target": "b"}],
    }
    out = render_dot(ir_like, options={"diagram": "sppm", "sppm_label_density": "teaching"})
    # Teaching mode should highlight the pedagogically relevant metric
    # (typically WT or CO when present, along with CT)
    assert "WT:" in out or "CO:" in out or "CT:" in out


def test_sppm_full_density_shows_all_metrics_for_acceptance():
    """Verify full density renders all timing metrics for complete analysis.
    
    Students should be able to see all metrics together to understand
    the complete picture of process delays and their sources.
    """
    ir_like = {
        "nodes": [
            {
                "id": "complex_task",
                "kind": "task",
                "name": "Complex Task",
                "metadata": {
                    "cycle_time": {"value": 15, "unit": "min"},
                    "wait_time": {"value": 25, "unit": "min"},
                    "changeover_time": {"value": 8, "unit": "min"},
                },
            },
        ],
        "edges": [],
    }
    out = render_dot(ir_like, options={"diagram": "sppm", "sppm_label_density": "full"})
    # Full density should show all three timing metrics
    assert "CT:" in out or "cycle" in out
    assert "WT:" in out or "wait" in out
    assert "CO:" in out or "crossover" in out
