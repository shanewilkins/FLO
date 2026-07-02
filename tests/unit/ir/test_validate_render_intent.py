from __future__ import annotations

import pytest

from flo.compiler.ir.models import IR, Node, Edge
from flo.compiler.ir.validate import ensure_schema_aligned, validate_ir
from flo.compiler.ir.validate_render_intent import validate_render_intent
from flo.services.errors import ValidationError


def _base_ir_with_render(render_payload: object) -> IR:
    return IR(
        name="render_intent_test",
        nodes=[
            Node(id="start", type="start", attrs={}),
            Node(id="task", type="task", attrs={}),
            Node(id="end", type="end", attrs={}),
        ],
        edges=[Edge(source="start", target="task"), Edge(source="task", target="end")],
        process_metadata={"render": render_payload},
    )


def test_validate_render_intent_no_process_metadata_is_noop() -> None:
    ir = IR(name="x", nodes=[Node(id="n", type="task")], edges=[])
    validate_render_intent(ir)


@pytest.mark.parametrize(
    ("render_payload", "expected_message"),
    [
        ("bad", "process.metadata.render must be an object"),
        ({"views": "bad"}, "process.metadata.render.views must be an object"),
    ],
)
def test_validate_render_intent_rejects_invalid_top_level_shapes(
    render_payload: object,
    expected_message: str,
) -> None:
    with pytest.raises(ValidationError, match=expected_message):
        validate_render_intent(_base_ir_with_render(render_payload))


@pytest.mark.parametrize(
    ("view_id", "view_config", "expected_message"),
    [
        ("", {}, "view id must be non-empty string"),
        ("main", "bad", "render.views.main must be an object"),
    ],
)
def test_validate_render_intent_rejects_invalid_view_entries(
    view_id: object,
    view_config: object,
    expected_message: str,
) -> None:
    ir = _base_ir_with_render({"views": {view_id: view_config}})

    with pytest.raises(ValidationError, match=expected_message):
        validate_render_intent(ir)


@pytest.mark.parametrize(
    ("view_fragment", "expected_message"),
    [
        ({"diagram": 1}, "render.defaults.diagram must be string"),
        (
            {"diagram": "flowchart"},
            r"render.defaults.diagram='flowchart' not supported",
        ),
        ({"publication": "bad"}, "render.defaults.publication must be object"),
        (
            {"publication": {"page_format": "broadsheet"}},
            r"render.defaults.publication.page_format='broadsheet' not supported",
        ),
        (
            {"publication": {"margins": {"outside": 5}}},
            r"render.defaults.publication.margins: unknown key 'outside'",
        ),
        (
            {"publication": {"margins": {"top": -1}}},
            "render.defaults.publication.margins.top must be non-negative integer",
        ),
        ({"layout": "bad"}, "render.defaults.layout must be object"),
        (
            {"layout": {"wrap": "weird"}},
            r"render.defaults.layout.wrap='weird' not supported",
        ),
        (
            {"layout": {"max_width": 0}},
            "render.defaults.layout.max_width must be positive integer",
        ),
        ({"sppm": "bad"}, "render.defaults.sppm must be object"),
        (
            {"sppm": {"label_density": "ultra"}},
            r"render.defaults.sppm.label_density='ultra' not supported",
        ),
        (
            {"sppm": {"node_numbering": "all"}},
            r"render.defaults.sppm.node_numbering='all' not supported",
        ),
        ({"spaghetti": "bad"}, "render.defaults.spaghetti must be object"),
        (
            {"spaghetti": {"channel": "all"}},
            r"render.defaults.spaghetti.channel='all' not supported",
        ),
        (
            {"spaghetti": {"people_mode": "team"}},
            r"render.defaults.spaghetti.people_mode='team' not supported",
        ),
    ],
)
def test_validate_render_intent_rejects_invalid_defaults_fragments(
    view_fragment: dict[str, object],
    expected_message: str,
) -> None:
    ir = _base_ir_with_render({"defaults": view_fragment})

    with pytest.raises(ValidationError, match=expected_message):
        validate_render_intent(ir)


def test_validate_render_intent_accepts_valid_defaults_and_views() -> None:
    ir = _base_ir_with_render(
        {
            "defaults": {
                "diagram": "sppm",
                "publication": {
                    "page_format": "letter",
                    "margins": {"top": 10, "right": 10, "bottom": 10, "left": 10},
                },
                "layout": {"wrap": "auto", "max_width": 1200, "target_columns": 4},
                "sppm": {"label_density": "compact", "node_numbering": "visible"},
                "spaghetti": {"channel": "people", "people_mode": "aggregate"},
            },
            "views": {
                "overview": {
                    "diagram": "spaghetti",
                    "layout": {"wrap": "none"},
                }
            },
        }
    )

    validate_render_intent(ir)


def test_ensure_schema_aligned_invokes_render_intent_validation() -> None:
    ir = _base_ir_with_render(
        {
            "defaults": {
                "diagram": "sppm",
                "layout": {"wrap": "auto"},
            },
            "views": {
                "": {"diagram": "sppm"},
            },
        }
    )

    with pytest.raises(ValidationError, match=r"view id must be non-empty string"):
        ensure_schema_aligned(ir)


def test_validate_ir_accepts_valid_render_intent_metadata() -> None:
    ir = _base_ir_with_render(
        {
            "defaults": {
                "diagram": "sppm",
                "publication": {"page_format": "a4"},
                "layout": {"wrap": "manual", "max_width": 900, "target_columns": 3},
                "sppm": {"label_density": "full", "edge_numbering": "hidden"},
            }
        }
    )

    validate_ir(ir)
