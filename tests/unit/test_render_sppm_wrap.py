from flo.render import render_dot


def _wrapped_lr_demo() -> str:
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "a", "kind": "task", "name": "A", "metadata": {}},
            {"id": "b", "kind": "task", "name": "B", "metadata": {}},
            {"id": "c", "kind": "task", "name": "C", "metadata": {}},
            {"id": "d", "kind": "task", "name": "D", "metadata": {}},
            {"id": "e", "kind": "task", "name": "E", "metadata": {}},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "a"},
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "d"},
            {"source": "d", "target": "e"},
            {"source": "e", "target": "end"},
        ],
    }

    return render_dot(
        ir_like,
        options={
            "diagram": "sppm",
            "orientation": "lr",
            "layout_wrap": "auto",
            "layout_target_columns": 3,
        },
    )


def test_layout_wrap_lr_emits_first_boundary_connector_with_continuation_labels():
    out = _wrapped_lr_demo()
    _assert_wrapped_lr_layout_structure(out)
    _assert_wrapped_lr_boundary_labels(out)


def _assert_wrapped_lr_layout_structure(out: str) -> None:
    assert "splines=ortho" in out
    assert "subgraph wrap_rank_lr_0" in out
    assert "subgraph cluster_wrap_" not in out
    assert "// Overflow policy: planner=placement, wrap=auto, fit=fit-preferred" in out
    assert '"a":e -> "b":w [];' in out
    assert '"__wrap_exit_lr_0" [shape=point, width=0.01, label="", style=invis, height=0.01];' in out
    assert 'group="__wrap_exit_column"' not in out
    assert '"b":"out_0":e -> "__wrap_exit_lr_0" [' in out
    assert 'arrowhead=none' in out
    assert 'constraint=false' in out


def _assert_wrapped_lr_boundary_labels(out: str) -> None:
    assert '"__wrap_exit_lr_0" -> "__sppm_boundary_corridor_b_c_out" [' in out
    assert 'label="P2-C"' in out
    assert '"__sppm_boundary_corridor_b_c_in" -> "c":"boundary_in":s [' in out
    assert 'label="P1-B"' in out
    assert "__sppm_wrap_corridor_" not in out


def test_layout_wrap_lr_emits_trailing_boundary_connector_with_continuation_labels():
    out = _wrapped_lr_demo()

    assert '"e":"out_0":e -> "__wrap_exit_lr_1" [' in out
    assert '"__wrap_exit_lr_1" -> "__sppm_boundary_corridor_e_end_out" [' in out
    assert 'label="P3-E"' in out
    assert '"__sppm_boundary_corridor_e_end_in" -> "end":n [' in out
    assert 'label="P2-E"' in out


def test_layout_wrap_tb_emits_wrap_hints_and_boundary_connector():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "a", "kind": "task", "name": "A", "metadata": {}},
            {"id": "b", "kind": "task", "name": "B", "metadata": {}},
            {"id": "c", "kind": "task", "name": "C", "metadata": {}},
            {"id": "d", "kind": "task", "name": "D", "metadata": {}},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "a"},
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "d"},
            {"source": "d", "target": "end"},
        ],
    }

    out = render_dot(
        ir_like,
        options={
            "diagram": "sppm",
            "orientation": "tb",
            "layout_wrap": "auto",
            "layout_target_columns": 2,
        },
    )

    assert "// Autoformat wrapped layout: orientation=tb" in out
    assert "// Overflow policy: planner=placement, wrap=auto, fit=fit-preferred" in out
    assert "rankdir=LR;" in out
    assert "subgraph wrap_rank_tb_0" in out
    assert 'group="__wrap_exit_column"' in out
    assert '"a":s -> "__sppm_boundary_corridor_a_b_out" [' in out
    assert 'label="P2-B"' in out
    assert '"__sppm_boundary_corridor_a_b_in" -> "b":n [' in out
    assert 'label="P1-A"' in out
    assert '"c":s -> "__sppm_boundary_corridor_c_d_out" [' in out
    assert 'label="P3-D"' in out
    assert '"__sppm_boundary_corridor_c_d_in" -> "d":n [' in out
    assert 'label="P2-C"' in out
    assert "__sppm_wrap_corridor_" not in out


def test_layout_wrap_tb_honors_width_budget_in_fit_strict_mode():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "a", "kind": "task", "name": "A", "metadata": {}},
            {"id": "b", "kind": "task", "name": "B", "metadata": {}},
            {"id": "c", "kind": "task", "name": "C", "metadata": {}},
            {"id": "d", "kind": "task", "name": "D", "metadata": {}},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "a"},
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "d"},
            {"source": "d", "target": "end"},
        ],
    }

    out = render_dot(
        ir_like,
        options={
            "diagram": "sppm",
            "orientation": "tb",
            "layout_wrap": "auto",
            "layout_fit": "fit-strict",
            "layout_max_width_px": 800,
        },
    )

    assert "// Autoformat wrapped layout: orientation=tb" in out
    assert "// Overflow policy: planner=placement, wrap=auto, fit=fit-strict" in out
    assert "minlen=2, penwidth=1.2" in out


def test_layout_wrap_off_preserves_non_wrapped_graph_attrs():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "a", "kind": "task", "name": "A", "metadata": {}},
            {"id": "b", "kind": "task", "name": "B", "metadata": {}},
            {"id": "c", "kind": "task", "name": "C", "metadata": {}},
            {"id": "d", "kind": "task", "name": "D", "metadata": {}},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "a"},
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "d"},
            {"source": "d", "target": "end"},
        ],
    }

    out = render_dot(
        ir_like,
        options={
            "diagram": "sppm",
            "layout_wrap": "off",
            "layout_target_columns": 2,
        },
    )

    assert "splines=ortho" in out
    assert "subgraph wrap_rank_" not in out
    assert "minlen=2" not in out


def test_layout_wrap_activates_from_width_threshold_only():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "a", "kind": "task", "name": "A", "metadata": {}},
            {"id": "b", "kind": "task", "name": "B", "metadata": {}},
            {"id": "c", "kind": "task", "name": "C", "metadata": {}},
            {"id": "d", "kind": "task", "name": "D", "metadata": {}},
            {"id": "e", "kind": "task", "name": "E", "metadata": {}},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "a"},
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "d"},
            {"source": "d", "target": "e"},
            {"source": "e", "target": "end"},
        ],
    }

    out = render_dot(
        ir_like,
        options={
            "diagram": "sppm",
            "layout_wrap": "auto",
            "layout_max_width_px": 650,
        },
    )

    assert "subgraph wrap_rank_lr_0" in out
    assert "splines=ortho" in out
    assert '"b":"out_0":e -> "__wrap_exit_lr_0" [' in out
    assert '"__wrap_exit_lr_0" -> "__sppm_boundary_corridor_b_c_out" [' in out
    assert 'label="P2-C"' in out
    assert '"__sppm_boundary_corridor_b_c_in" -> "c":"boundary_in":s [' in out
    assert 'label="P1-B"' in out
    assert '"e":"out_0":e -> "__wrap_exit_lr_1" [' in out
    assert '"__wrap_exit_lr_1" -> "__sppm_boundary_corridor_e_end_out" [' in out
    assert 'label="P3-E"' in out
    assert '"__sppm_boundary_corridor_e_end_in" -> "end":n [' in out
    assert 'label="P2-E"' in out


def test_layout_wrap_tiny_width_uses_min_chunk_floor_of_three():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "a", "kind": "task", "name": "A", "metadata": {}},
            {"id": "b", "kind": "task", "name": "B", "metadata": {}},
            {"id": "c", "kind": "task", "name": "C", "metadata": {}},
            {"id": "d", "kind": "task", "name": "D", "metadata": {}},
            {"id": "e", "kind": "task", "name": "E", "metadata": {}},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "a"},
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "d"},
            {"source": "d", "target": "e"},
            {"source": "e", "target": "end"},
        ],
    }

    out = render_dot(
        ir_like,
        options={
            "diagram": "sppm",
            "layout_wrap": "auto",
            "layout_max_width_px": 1,
        },
    )

    assert '"b":"out_0":e -> "__wrap_exit_lr_2" [' in out
    assert '"__wrap_exit_lr_2" -> "__sppm_boundary_corridor_b_c_out" [' in out
    assert 'label="P4-C"' in out
    assert '"__sppm_boundary_corridor_b_c_in" -> "c":"boundary_in":s [' in out
    assert 'label="P3-B"' in out
    assert '"e":"out_0":e -> "__wrap_exit_lr_5" [' in out
    assert '"__wrap_exit_lr_5" -> "__sppm_boundary_corridor_e_end_out" [' in out
    assert 'label="P7-E"' in out
    assert '"__sppm_boundary_corridor_e_end_in" -> "end":n [' in out
    assert 'label="P6-E"' in out


def test_layout_wrap_fit_strict_wraps_sooner_than_fit_preferred_for_same_content():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {
                "id": "a",
                "kind": "task",
                "name": "Collect and validate supporting invoice documentation",
                "workers": ["Finance Analyst", "Operations Reviewer"],
                "metadata": {
                    "description": "Gather and inspect all invoice attachments before approval routing.",
                    "cycle_time": {"value": 12, "unit": "min"},
                },
            },
            {
                "id": "b",
                "kind": "task",
                "name": "Review exceptions and annotate discrepancies for requester follow-up",
                "workers": ["Finance Manager"],
                "metadata": {
                    "description": "Flag missing totals, wrong coding, or absent approvals.",
                    "cycle_time": {"value": 9, "unit": "min"},
                },
            },
            {"id": "c", "kind": "task", "name": "Approve", "metadata": {}},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "a"},
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "end"},
        ],
    }

    out_preferred = render_dot(
        ir_like,
        options={
            "diagram": "sppm",
            "layout_wrap": "auto",
            "layout_fit": "fit-preferred",
            "layout_max_width_px": 1200,
        },
    )
    out_strict = render_dot(
        ir_like,
        options={
            "diagram": "sppm",
            "layout_wrap": "auto",
            "layout_fit": "fit-strict",
            "layout_max_width_px": 1200,
        },
    )

    assert '"b":"out_0":e -> "__wrap_exit_lr_0" [' in out_preferred
    assert 'label="P2-C"' in out_preferred
    assert '"a":"out_0":e -> "__wrap_exit_lr_0" [' in out_strict
    assert 'label="P2-B"' in out_strict


def test_layout_wrap_width_estimator_responds_to_dense_label_content():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {
                "id": "a",
                "kind": "task",
                "name": "A very long validation and exception handling step name",
                "workers": ["Senior Finance Analyst", "Accounts Payable Specialist"],
                "metadata": {
                    "description": "Detailed step narrative that should materially increase estimated node width.",
                    "cycle_time": {"value": 14, "unit": "min"},
                    "wait_time": {"value": 8, "unit": "min"},
                },
            },
            {"id": "b", "kind": "task", "name": "B", "metadata": {}},
            {"id": "c", "kind": "task", "name": "C", "metadata": {}},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "a"},
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "end"},
        ],
    }

    out = render_dot(
        ir_like,
        options={
            "diagram": "sppm",
            "layout_wrap": "auto",
            "layout_fit": "fit-strict",
            "layout_max_width_px": 1000,
        },
    )

    assert '"a":"out_0":e -> "__wrap_exit_lr_0" [' in out
    assert 'label="P2-B"' in out