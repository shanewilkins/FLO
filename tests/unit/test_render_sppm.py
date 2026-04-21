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
