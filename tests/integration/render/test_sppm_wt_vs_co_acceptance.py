"""Integration tests validating WT vs CO pedagogical distinction in SPPM.

Tests ensure that students and practitioners can see and understand the difference
between queue delays (waiting time) and setup delays (changeover time) in process
improvement contexts. Both are non-value-adding, but they require different
solutions (pull/kanban vs 5S/SMED).
"""

from click.testing import CliRunner

from flo.core.cli import cli


def test_sppm_render_shows_waiting_time_in_node_label():
    """Verify SPPM renders wait_time (queue delays) in node labels.

    Students need to see queue delays explicitly so they can diagnose resource
    scheduling problems and apply pull/kanban solutions. Queue nodes and tasks
    both render their wait_time metadata.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/bakery_setup_vs_queue.flo",
            "--export",
            "dot",
            "--diagram",
            "sppm",
        ],
    )
    assert result.exit_code == 0
    # Task nodes show wait times in their labels
    assert "WT:" in result.output or "wait" in result.output
    # Footer aggregates all waiting time
    assert "Waiting Time:" in result.output or "245 min" in result.output


def test_sppm_render_shows_changeover_time_in_node_label():
    """Verify SPPM renders changeover_time (setup delays) in node labels.

    Students need to see setup delays explicitly so they can diagnose process
    design problems and apply SMED/5S solutions.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/bakery_setup_vs_queue.flo",
            "--export",
            "dot",
            "--diagram",
            "sppm",
        ],
    )
    assert result.exit_code == 0
    # Oven setup step shows changeover time
    assert "CO: 30 min crossover" in result.output  # oven_setup node


def test_sppm_footer_aggregates_waiting_time_from_process():
    """Verify SPPM publication footer shows total waiting time.

    Footer should aggregate all queue delays (WT) across the process so users
    can see the total waste due to queueing and understand its magnitude.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/bakery_setup_vs_queue.flo",
            "--export",
            "dot",
            "--diagram",
            "sppm",
        ],
    )
    assert result.exit_code == 0
    # Footer should show aggregated waiting time (total = 245 min)
    # Check for footer metric label and value
    assert "Waiting Time" in result.output
    assert "245" in result.output


def test_sppm_footer_aggregates_changeover_time_from_process():
    """Verify SPPM publication footer shows total changeover time.

    Footer should aggregate all setup delays (CO) across the process so users
    can see the total waste due to setup and understand the scope for
    improvement via SMED.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/bakery_setup_vs_queue.flo",
            "--export",
            "dot",
            "--diagram",
            "sppm",
        ],
    )
    assert result.exit_code == 0
    # Footer should show aggregated changeover time (total = 30 min from oven_setup)
    assert "Changeover Time" in result.output
    assert "30" in result.output


def test_sppm_edge_callout_shows_target_changeover_time():
    """Verify edge callouts render CO from target nodes with step numbering.

    When step numbering is enabled, edges leading to tasks with changeover time
    should show the CO value, helping students trace setup delays through the flow.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/bakery_setup_vs_queue.flo",
            "--export",
            "dot",
            "--diagram",
            "sppm",
            "--sppm-step-numbering",
            "edge",
        ],
    )
    assert result.exit_code == 0
    # Edge callouts should show step numbering and/or CO
    output = result.output
    # Both step refs and CO callout should be present
    assert "->" in output  # Edge numbering format
    assert "CO:" in output or "crossover" in output


def test_waiting_time_and_changeover_time_are_distinct_in_output():
    """Verify WT and CO appear as distinct labels in SPPM output.

    The pedagogical principle requires that WT and CO be visually and
    semantically distinct so students don't confuse queue delays (requiring
    pull/kanban) with setup delays (requiring SMED/5S).
    """
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/bakery_setup_vs_queue.flo",
            "--export",
            "dot",
            "--diagram",
            "sppm",
        ],
    )
    assert result.exit_code == 0
    output = result.output
    # Both metrics should appear with clear labels
    # WT shows as "WT:" in node labels
    assert "WT:" in output or "wait" in output
    # CO shows as "CO:" in node labels
    assert "CO:" in output or "crossover" in output


def test_sppm_compact_density_includes_both_wait_and_changeover():
    """Verify compact label density preserves both WT and CO distinction.

    Even in compact mode (space-constrained), the pedagogical distinction
    between WT and CO must remain clear.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/bakery_setup_vs_queue.flo",
            "--export",
            "dot",
            "--diagram",
            "sppm",
            "--sppm-label-density",
            "compact",
        ],
    )
    assert result.exit_code == 0
    output = result.output
    # Both WT and CO should still be visible in compact mode
    # At minimum, one example of each should appear
    assert "WT:" in output or "wait" in output
    assert "CO:" in output or "crossover" in output


def test_cli_example_renders_without_error():
    """Smoke test: ensure bakery example renders successfully."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            "examples/reference/bakery_setup_vs_queue.flo",
            "--export",
            "dot",
            "--diagram",
            "sppm",
        ],
    )
    assert result.exit_code == 0, f"CLI failed with: {result.output}"
    assert "digraph" in result.output
    assert "Prepare Dough" in result.output or "prepare_dough" in result.output
