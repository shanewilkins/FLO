from flo.render._autoformat_wrap import build_wrap_plan
from flo.render.options import RenderOptions


def test_chunked_wrap_plan_exposes_shared_overflow_policy_for_generic_renderers():
    nodes = [
        {"id": "start", "kind": "start", "name": "Start"},
        {"id": "a", "kind": "task", "name": "A"},
        {"id": "b", "kind": "task", "name": "B"},
        {"id": "c", "kind": "task", "name": "C"},
    ]
    options = RenderOptions(
        diagram="flowchart",
        orientation="lr",
        layout_wrap="auto",
        layout_fit="fit-strict",
        layout_max_width_px=640,
    )

    plan = build_wrap_plan(nodes, options, planner="chunked")

    assert plan.overflow_policy.planner == "chunked"
    assert plan.overflow_policy.wrap_mode == "auto"
    assert plan.overflow_policy.fit_mode == "fit-strict"
    assert plan.overflow_policy.max_major_px == 640
    assert plan.overflow_policy.margin_px == 180
    assert plan.overflow_policy.min_chunk_size == 2
    assert plan.overflow_policy.break_preference == "sequence-boundary"
    assert plan.overflow_policy.continuation_mode == "boundary-corridor"
    assert plan.overflow_policy.strict is True


def test_placement_wrap_plan_exposes_shared_overflow_policy_for_sppm():
    nodes = [
        {"id": "start", "kind": "start", "name": "Start"},
        {"id": "a", "kind": "task", "name": "A", "metadata": {}},
        {"id": "b", "kind": "task", "name": "B", "metadata": {}},
        {"id": "c", "kind": "task", "name": "C", "metadata": {}},
        {"id": "end", "kind": "end", "name": "End"},
    ]
    options = RenderOptions(
        diagram="sppm",
        orientation="lr",
        layout_wrap="auto",
        layout_fit="fit-preferred",
        layout_target_columns=2,
    )

    plan = build_wrap_plan(nodes, options, planner="placement")

    assert plan.overflow_policy.planner == "placement"
    assert plan.overflow_policy.wrap_mode == "auto"
    assert plan.overflow_policy.fit_mode == "fit-preferred"
    assert plan.overflow_policy.max_major_px is not None
    assert plan.overflow_policy.margin_px == 48
    assert plan.overflow_policy.min_chunk_size == 3
    assert plan.overflow_policy.break_preference == "sequence-boundary"
    assert plan.overflow_policy.continuation_mode == "boundary-corridor"
    assert plan.overflow_policy.strict is False
