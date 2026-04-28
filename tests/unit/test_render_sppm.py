from flo.render import render_dot


# ---------------------------------------------------------------------------
# SPPM renderer
# ---------------------------------------------------------------------------


def test_sppm_renders_digraph_lr():
    out = render_dot({}, options={"diagram": "sppm"})
    assert "digraph {" in out
    assert "rankdir=LR;" in out


def test_sppm_tb_orientation():
    out = render_dot({}, options={"diagram": "sppm", "orientation": "tb"})
    assert "rankdir=TB;" in out


def test_sppm_va_node_gets_green_fill():
    ir_like = {
        "nodes": [
            {
                "id": "wash",
                "kind": "task",
                "name": "Wash",
                "metadata": {"value_class": "VA", "cycle_time": {"value": 30, "unit": "min"}},
            }
        ],
        "edges": [],
    }
    out = render_dot(ir_like, options={"diagram": "sppm"})
    assert 'BGCOLOR="#81C784"' in out
    assert 'COLOR="#2E7D32"' in out


def test_sppm_rnva_node_gets_yellow_fill():
    ir_like = {
        "nodes": [
            {
                "id": "sort",
                "kind": "task",
                "name": "Sort and tag",
                "metadata": {"value_class": "RNVA"},
            }
        ],
        "edges": [],
    }
    out = render_dot(ir_like, options={"diagram": "sppm"})
    assert 'BGCOLOR="#FFF176"' in out
    assert 'COLOR="#F9A825"' in out


def test_sppm_nva_node_gets_red_fill():
    ir_like = {
        "nodes": [
            {
                "id": "rework",
                "kind": "task",
                "name": "Rework",
                "metadata": {"value_class": "NVA"},
            }
        ],
        "edges": [],
    }
    out = render_dot(ir_like, options={"diagram": "sppm"})
    assert 'BGCOLOR="#EF9A9A"' in out
    assert 'COLOR="#C62828"' in out


def test_sppm_cycle_time_included_in_node_label():
    ir_like = {
        "nodes": [
            {
                "id": "dry",
                "kind": "task",
                "name": "Dry",
                "metadata": {"value_class": "VA", "cycle_time": {"value": 45, "unit": "min"}},
            }
        ],
        "edges": [],
    }
    out = render_dot(ir_like, options={"diagram": "sppm"})
    assert "45 min" in out


def test_sppm_workers_included_in_task_label():
    ir_like = {
        "nodes": [
            {
                "id": "fold",
                "kind": "task",
                "name": "Fold",
                "workers": ["Staff"],
                "metadata": {"value_class": "VA", "cycle_time": {"value": 15, "unit": "min"}},
            }
        ],
        "edges": [],
    }
    out = render_dot(ir_like, options={"diagram": "sppm"})
    assert "Staff" in out


def test_sppm_start_end_use_rounded_rect():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [{"source": "start", "target": "end"}],
    }
    out = render_dot(ir_like, options={"diagram": "sppm"})
    # Both start and end should use rounded rectangle (shape=rect, style rounded)
    assert out.count('shape=rect') == 2
    assert out.count('style="rounded,filled"') == 2


def test_sppm_wait_time_shown_in_node_info_box():
    ir_like = {
        "nodes": [
            {"id": "dropoff", "kind": "task", "name": "Drop-off", "metadata": {}},
            {
                "id": "sort",
                "kind": "task",
                "name": "Sort",
                "metadata": {"wait_time": {"value": 8, "unit": "min"}},
            },
        ],
        "edges": [{"source": "dropoff", "target": "sort"}],
    }
    out = render_dot(ir_like, options={"diagram": "sppm"})
    assert "8 min wait" in out


def test_sppm_zero_wait_time_omitted_from_info_box():
    ir_like = {
        "nodes": [
            {"id": "a", "kind": "task", "name": "A", "metadata": {}},
            {
                "id": "b",
                "kind": "task",
                "name": "B",
                "metadata": {"wait_time": {"value": 0, "unit": "min"}},
            },
        ],
        "edges": [{"source": "a", "target": "b"}],
    }
    out = render_dot(ir_like, options={"diagram": "sppm"})
    assert "wait" not in out


def test_sppm_workers_omitted_from_start_end_labels():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Begin", "workers": ["Customer"]},
            {"id": "end", "kind": "end", "name": "Done", "workers": ["Staff"]},
        ],
        "edges": [{"source": "start", "target": "end"}],
    }
    out = render_dot(ir_like, options={"diagram": "sppm"})
    # Workers should not appear in start/end labels
    assert "Customer" not in out
    assert "Staff" not in out


def test_sppm_default_theme_is_used_when_no_theme_specified():
    from flo.render._sppm_themes import SPPM_THEMES
    default = SPPM_THEMES["default"]
    ir_like = {
        "nodes": [{"id": "step", "kind": "task", "name": "Step", "metadata": {"value_class": "VA"}}],
        "edges": [],
    }
    out = render_dot(ir_like, options={"diagram": "sppm"})
    assert default.va.fill in out
    assert default.va.border in out


def test_sppm_monochrome_theme_produces_different_colors_than_default():
    ir_like = {
        "nodes": [{"id": "step", "kind": "task", "name": "Step", "metadata": {"value_class": "VA"}}],
        "edges": [],
    }
    out_default = render_dot(ir_like, options={"diagram": "sppm", "sppm_theme": "default"})
    out_mono = render_dot(ir_like, options={"diagram": "sppm", "sppm_theme": "monochrome"})
    assert out_default != out_mono


def test_sppm_print_theme_resolves_correctly():
    from flo.render._sppm_themes import SPPM_THEMES
    print_theme = SPPM_THEMES["print"]
    ir_like = {
        "nodes": [{"id": "step", "kind": "task", "name": "Step", "metadata": {"value_class": "NVA"}}],
        "edges": [],
    }
    out = render_dot(ir_like, options={"diagram": "sppm", "sppm_theme": "print"})
    assert print_theme.nva.fill in out
    assert print_theme.nva.border in out


def test_sppm_unknown_theme_name_falls_back_to_default():
    from flo.render._sppm_themes import resolve_sppm_theme, SPPM_THEMES
    theme = resolve_sppm_theme("nonexistent")
    assert theme == SPPM_THEMES["default"]


def test_sppm_compact_density_omits_description():
    ir_like = {
        "nodes": [
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "workers": ["Lead Baker", "Assistant Baker"],
                "metadata": {
                    "description": "Combine all dry ingredients in bowl",
                    "cycle_time": {"value": 12, "unit": "min"},
                    "wait_time": {"value": 3, "unit": "min"},
                },
            }
        ],
        "edges": [],
    }
    out = render_dot(ir_like, options={"diagram": "sppm", "sppm_label_density": "compact"})
    assert "Combine all dry ingredients" not in out
    assert "CT: 12 min | WT: 3 min wait" in out


def test_sppm_teaching_density_keeps_key_metric_only():
    ir_like = {
        "nodes": [
            {
                "id": "dry",
                "kind": "task",
                "name": "Dry",
                "workers": ["Staff"],
                "metadata": {
                    "description": "Detailed explanation",
                    "cycle_time": {"value": 45, "unit": "min"},
                    "wait_time": {"value": 9, "unit": "min"},
                },
            }
        ],
        "edges": [],
    }
    out = render_dot(ir_like, options={"diagram": "sppm", "sppm_label_density": "teaching"})
    assert "CT: 45 min" in out
    assert "WT: 9 min wait" not in out
    assert "Workers:" not in out
    assert "Detailed explanation" not in out


def test_sppm_max_step_name_truncates_with_ellipsis_policy():
    ir_like = {
        "nodes": [
            {
                "id": "long_name",
                "kind": "task",
                "name": "This is a very long step name that should be truncated",
                "metadata": {"value_class": "VA"},
            }
        ],
        "edges": [],
    }
    out = render_dot(
        ir_like,
        options={
            "diagram": "sppm",
            "sppm_max_label_step_name": 18,
            "sppm_truncation_policy": "ellipsis",
        },
    )
    assert "This is a very" in out
    assert "..." in out


def test_sppm_edge_step_numbering_adds_xlabels():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "a", "kind": "task", "name": "A", "metadata": {}},
            {"id": "b", "kind": "task", "name": "B", "metadata": {}},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "a"},
            {"source": "a", "target": "b"},
            {"source": "b", "target": "end"},
        ],
    }
    out = render_dot(ir_like, options={"diagram": "sppm", "sppm_step_numbering": "edge"})
    assert 'xlabel="1->2"' in out


def test_layout_wrap_lr_emits_wrap_hints_and_boundary_connector():
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
            "orientation": "lr",
            "layout_wrap": "auto",
            "layout_target_columns": 3,
        },
    )

    assert "splines=ortho" in out
    assert "cluster_wrap_lr_0" in out
    assert '"a" -> "b" [tailport=e, headport=w];' in out
    assert '"b" -> "c" [tailport=e, headport=w, minlen=2, penwidth=1.2];' in out
    assert '"e" -> "end" [tailport=e, headport=w, minlen=2, penwidth=1.2];' in out
    assert "__sppm_wrap_corridor_" not in out


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
    assert "rankdir=LR;" in out
    assert "cluster_wrap_tb_0" in out
    assert '"a" -> "b" [tailport=s, headport=n, minlen=2, penwidth=1.2];' in out
    assert '"c" -> "d" [tailport=s, headport=n, minlen=2, penwidth=1.2];' in out
    assert "__sppm_wrap_corridor_" not in out


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

    assert "splines=true" in out
    assert "cluster_wrap_" not in out
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

    assert "cluster_wrap_lr_0" in out
    assert "splines=ortho" in out
    assert '"b" -> "c" [tailport=e, headport=w, minlen=2, penwidth=1.2];' in out
    assert '"e" -> "end" [tailport=e, headport=w, minlen=2, penwidth=1.2];' in out


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

    # width floor => chunk size 3 including start/end, boundaries are b->c and e->end.
    assert '"b" -> "c" [tailport=e, headport=w, minlen=2, penwidth=1.2];' in out
    assert '"e" -> "end" [tailport=e, headport=w, minlen=2, penwidth=1.2];' in out


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
            "layout_max_width_px": 900,
        },
    )
    out_strict = render_dot(
        ir_like,
        options={
            "diagram": "sppm",
            "layout_wrap": "auto",
            "layout_fit": "fit-strict",
            "layout_max_width_px": 900,
        },
    )

    assert "chunk_size=3" in out_preferred
    assert "chunk_size=2" in out_strict


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

    assert "chunk_size=2" in out


def test_sppm_node_numbering_is_deterministic_with_branching():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "a", "kind": "task", "name": "A", "metadata": {}},
            {"id": "b", "kind": "task", "name": "B", "metadata": {}},
            {"id": "c", "kind": "task", "name": "C", "metadata": {}},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "a"},
            {"source": "a", "target": "b"},
            {"source": "a", "target": "c"},
            {"source": "b", "target": "end"},
            {"source": "c", "target": "end"},
        ],
    }

    out_one = render_dot(ir_like, options={"diagram": "sppm", "sppm_step_numbering": "node"})
    out_two = render_dot(ir_like, options={"diagram": "sppm", "sppm_step_numbering": "node"})

    assert out_one == out_two
    assert "1. A" in out_one
    assert "2. B" in out_one
    assert "3. C" in out_one
