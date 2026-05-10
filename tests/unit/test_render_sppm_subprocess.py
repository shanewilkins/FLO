import pytest

from flo.render import render_dot
from flo.services.errors import RenderError


def test_sppm_default_top_level_collapses_subprocess_children():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "prep", "kind": "subprocess", "name": "Prep"},
            {"id": "gather", "kind": "task", "name": "Gather", "subprocess_parent": "prep"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "prep"},
            {"source": "prep", "target": "gather"},
            {"source": "gather", "target": "end"},
        ],
    }

    out = render_dot(ir_like, options={"diagram": "sppm"})

    assert '"gather"' not in out
    assert '"prep"' in out
    assert '"prep" -> "end"' in out


def test_sppm_parent_only_hides_subprocess_children_and_collapses_path():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "prep", "kind": "subprocess", "name": "Prep"},
            {"id": "gather", "kind": "task", "name": "Gather", "subprocess_parent": "prep"},
            {"id": "mix", "kind": "task", "name": "Mix", "subprocess_parent": "prep"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "prep"},
            {"source": "prep", "target": "gather"},
            {"source": "gather", "target": "mix"},
            {"source": "mix", "target": "end"},
        ],
    }
    out = render_dot(ir_like, options={"diagram": "sppm", "subprocess_view": "parent-only"})
    assert '"gather"' not in out
    assert '"mix"' not in out
    assert '"prep"' in out
    assert '"start" -> "prep"' in out
    assert '"prep" -> "end"' in out


def test_sppm_child_map_focuses_one_subprocess_with_entry_and_exit_context():
    ir_like = {
        "process": {"id": "demo", "name": "Demo Process"},
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "prep", "kind": "subprocess", "name": "Prep"},
            {"id": "gather", "kind": "task", "name": "Gather", "subprocess_parent": "prep"},
            {"id": "mix", "kind": "task", "name": "Mix", "subprocess_parent": "prep"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "prep"},
            {"source": "prep", "target": "gather"},
            {"source": "gather", "target": "mix"},
            {"source": "mix", "target": "end"},
        ],
    }

    out = render_dot(
        ir_like,
        options={
            "diagram": "sppm",
            "sppm_projection": "child-map",
            "sppm_focus_subprocess": "prep",
        },
    )

    assert '"start"' in out
    assert '"prep"' in out
    assert '"gather"' in out
    assert '"mix"' in out
    assert '"end"' in out
    assert "Projection:" in out
    assert "child-map" in out
    assert "Focus:" in out
    assert "prep" in out
    assert "Entry Context:" in out
    assert "start" in out
    assert "Exit Context:" in out
    assert "end" in out


def test_sppm_inline_projection_falls_back_to_child_map_when_budget_exceeded():
    ir_like = {
        "process": {"id": "demo", "name": "Demo Process"},
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "prep", "kind": "subprocess", "name": "Prep"},
            {"id": "a", "kind": "task", "name": "A", "subprocess_parent": "prep"},
            {"id": "b", "kind": "task", "name": "B", "subprocess_parent": "prep"},
            {"id": "c", "kind": "task", "name": "C", "subprocess_parent": "prep"},
            {"id": "d", "kind": "task", "name": "D", "subprocess_parent": "prep"},
            {"id": "e", "kind": "task", "name": "E", "subprocess_parent": "prep"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "prep"},
            {"source": "prep", "target": "a"},
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
            "sppm_projection": "inline",
            "sppm_focus_subprocess": "prep",
            "layout_fit": "fit-preferred",
            "layout_target_columns": 3,
        },
    )

    assert "Projection Fallback:" in out
    assert "inline budget exceeded" in out
    assert "Readability Warning:" in out
    assert "Projection:" in out
    assert "child-map" in out


def test_sppm_inline_projection_strict_mode_fails_when_budget_exceeded():
    ir_like = {
        "process": {"id": "demo", "name": "Demo Process"},
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "prep", "kind": "subprocess", "name": "Prep"},
            {"id": "a", "kind": "task", "name": "A", "subprocess_parent": "prep"},
            {"id": "b", "kind": "task", "name": "B", "subprocess_parent": "prep"},
            {"id": "c", "kind": "task", "name": "C", "subprocess_parent": "prep"},
            {"id": "d", "kind": "task", "name": "D", "subprocess_parent": "prep"},
            {"id": "e", "kind": "task", "name": "E", "subprocess_parent": "prep"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "prep"},
            {"source": "prep", "target": "a"},
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "d"},
            {"source": "d", "target": "e"},
            {"source": "e", "target": "end"},
        ],
    }

    with pytest.raises(RenderError, match="fell back to 'child_map'"):
        render_dot(
            ir_like,
            options={
                "diagram": "sppm",
                "sppm_projection": "inline",
                "sppm_focus_subprocess": "prep",
                "layout_fit": "fit-strict",
                "layout_target_columns": 3,
            },
        )


def test_sppm_subprocess_nodes_include_marker_and_detail_map_reference():
    ir_like = {
        "nodes": [
            {
                "id": "prep",
                "kind": "subprocess",
                "name": "Prep",
                "metadata": {"detail_map_ref": "SP-01", "value_class": "RNVA"},
            }
        ],
        "edges": [],
    }
    out = render_dot(ir_like, options={"diagram": "sppm"})
    assert '"prep" [label="Prep\\n[prep]", shape=ellipse, style="filled,dotted"' in out
    assert "Subprocess" in out
    assert "Detail map: SP-01" in out


def test_sppm_renders_process_title_and_header_metadata():
    ir_like = {
        "process": {
            "id": "wash_n_fold",
            "name": "Wash n' Fold",
            "metadata": {"owner": "Laundry Ops", "revision": "R2"},
        },
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [{"source": "start", "target": "end"}],
    }
    out = render_dot(ir_like, options={"diagram": "sppm", "sppm_output_profile": "print"})
    assert "Wash n' Fold" in out
    assert "Process:" in out
    assert "wash_n_fold" in out
    assert "Owner:" in out
    assert "Laundry Ops" in out
    assert "Revision:" in out
    assert "R2" in out
    assert "Profile:" in out
    assert "print" in out


def test_sppm_header_coexists_with_queue_rework_and_notes_in_default_output():
    ir_like = {
        "process": {
            "id": "header_demo",
            "name": "Header Demo",
            "metadata": {"owner": "Ops", "revision": "R1"},
        },
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {
                "id": "queue",
                "kind": "queue",
                "name": "Inbox",
                "metadata": {"wait_time": {"value": 7, "unit": "min"}},
            },
            {"id": "check", "kind": "decision", "name": "Ready?"},
            {
                "id": "work",
                "kind": "task",
                "name": "Do Work",
                "note": "Requires manager signoff",
                "metadata": {"value_class": "VA", "cycle_time": {"value": 4, "unit": "min"}},
            },
            {
                "id": "rework",
                "kind": "task",
                "name": "Fix Input",
                "metadata": {"value_class": "RNVA", "cycle_time": {"value": 3, "unit": "min"}},
            },
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "queue"},
            {"source": "queue", "target": "check"},
            {"source": "check", "target": "work", "outcome": "yes"},
            {
                "source": "check",
                "target": "rework",
                "outcome": "no",
                "edge_type": "rework",
                "rework": True,
                "metadata": {"rate": 0.12, "reason": "Missing details"},
            },
            {"source": "rework", "target": "queue", "edge_type": "rework", "rework": True},
            {"source": "work", "target": "end"},
        ],
    }

    out = render_dot(ir_like, options={"diagram": "sppm", "show_notes": True})

    assert "Header Demo" in out
    assert "Process:" in out
    assert "header_demo" in out
    assert "Owner:" in out
    assert "Ops" in out
    assert "Inbox" in out
    assert "Note: Requires manager signoff" in out
    assert "Rate: 12%" in out
    assert "Reason: Missing details" in out