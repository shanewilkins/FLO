from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from flo.app import _resolve_render_options_for_output
from flo.render.sppm.themes import SPPM_THEMES
from flo.render.spaghetti import render_spaghetti_svg_artifact
from flo.render.sppm.nodes import _node_svg
from flo.render.swimlane import render_swimlane_svg_artifact
from flo.render.value_stream import render_value_stream_svg_artifact
from flo.render._svg_theme import apply_svg_typography
from flo.render.layout_core.models import LayoutBounds, LayoutLaneFrame, LayoutResult
from flo.render.options import RenderOptions
from flo.process.ir.models import Edge, IR, Node
from flo.render.themes import (
    BUILTIN_THEMES,
    ThemeValidationError,
    resolve_render_theme,
    theme_contrast_risks,
)
from flo.errors import CLIError, EXIT_USAGE

_GOLDEN = Path("tests/golden/themes/configured_theme_signatures.json")


def _theme_definitions() -> dict:
    return {
        "book_house": {
            "extends": "default",
            "canvas": {"background": "#F4F0FF"},
            "typography": {
                "font_family": ["Avenir Next", "Arial", "sans-serif"],
                "scale": 1.1,
            },
            "roles": {
                "va": {"fill": "#B8E6C1", "border": "#216E39"},
                "lane": {
                    "fill": "#EEE9FF",
                    "border": "#6D5BD0",
                    "title_text": "#241A5A",
                },
                "material_route": {"border": "#A33A20"},
                "information_route": {"border": "#235789"},
                "location_storage": {"fill": "#FFF0C2", "border": "#9A6700"},
            },
        }
    }


def _options(diagram: str) -> RenderOptions:
    return RenderOptions.from_mapping(
        {"diagram": diagram, "theme": "book_house", "themes": _theme_definitions()}
    )


def test_theme_inheritance_is_partial_and_immutable() -> None:
    theme = resolve_render_theme(
        selected_name="book_house", definitions=_theme_definitions()
    )

    assert theme.canvas_background == "#F4F0FF"
    assert theme.font_family == ("Avenir Next", "Arial", "sans-serif")
    assert theme.role("va").fill == "#B8E6C1"
    assert theme.role("rnva").fill == "#FFF176"
    with pytest.raises(TypeError):
        theme.roles["va"] = theme.role("rnva")  # type: ignore[index]


@pytest.mark.parametrize(
    ("definitions", "message"),
    [
        (
            {"a": {"extends": "b"}, "b": {"extends": "a"}},
            "Theme inheritance cycle",
        ),
        ({"a": {"extends": "missing"}}, "unknown theme 'missing'"),
        (
            {"a": {"roles": {"invented": {"fill": "#FFFFFF"}}}},
            "not a registered role",
        ),
        (
            {"a": {"typography": {"scale": 2.0}}},
            "must be from 0.75 through 1.5",
        ),
        (
            {"a": {"canvas": {"background": "definitely-not-a-color"}}},
            "must use #RGB",
        ),
    ],
)
def test_theme_validation_reports_actionable_paths(
    definitions: dict, message: str
) -> None:
    with pytest.raises(ThemeValidationError, match=message):
        resolve_render_theme(selected_name="a", definitions=definitions)


def test_legacy_sppm_theme_is_adapted_into_shared_contract() -> None:
    theme = resolve_render_theme(
        selected_name="house",
        legacy_sppm_themes={"house": SPPM_THEMES["flatly"]},
    )

    assert theme.role("va").fill == "#D1F2EB"
    assert theme.canvas_background == "#fffdf8"


def test_builtin_semantic_roles_meet_normal_text_contrast_floor() -> None:
    assert {
        name: theme_contrast_risks(theme) for name, theme in BUILTIN_THEMES.items()
    } == {"default": (), "flatly": (), "print": (), "monochrome": ()}


def test_invalid_shared_theme_is_a_usage_stage_cli_error() -> None:
    with pytest.raises(CLIError) as caught:
        _resolve_render_options_for_output(
            resolved_options={"theme": "missing"}, output_format="svg"
        )

    assert caught.value.code == EXIT_USAGE
    assert caught.value.error_stage == "option_validation"
    assert "Unknown render theme 'missing'" in str(caught.value)


def test_print_output_profile_selects_theme_below_explicit_selection() -> None:
    profiled = RenderOptions.from_mapping(
        {"diagram": "sppm", "sppm_output_profile": "print"}
    )
    explicit = RenderOptions.from_mapping(
        {
            "diagram": "sppm",
            "sppm_output_profile": "print",
            "theme": "flatly",
        }
    )

    assert profiled.resolved_theme.name == "print"
    assert explicit.resolved_theme.name == "flatly"


def test_configured_theme_cross_renderer_golden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_layout(_request, *, engine):
        return LayoutResult(
            orientation="lr",
            canvas_bounds=LayoutBounds(0, 0, 220, 100),
            lanes=(
                LayoutLaneFrame(
                    id="ops",
                    label="Operations",
                    bounds=LayoutBounds(0, 0, 220, 100),
                    node_ids=("work",),
                ),
            ),
            node_bounds={"work": LayoutBounds(50, 25, 120, 52)},
            edge_paths={},
            diagnostics=(),
        )

    monkeypatch.setattr("flo.render.swimlane.renderer.execute_elk_layout", fake_layout)
    swimlane_process = {
        "lanes": [{"id": "ops", "name": "Operations"}],
        "nodes": [
            {
                "id": "work",
                "kind": "task",
                "name": "Do work",
                "lane": "ops",
                "metadata": {"value_class": "VA"},
            }
        ],
        "edges": [],
    }
    swimlane, _ = render_swimlane_svg_artifact(swimlane_process, _options("swimlane"))
    swimlane_rerun, _ = render_swimlane_svg_artifact(
        swimlane_process, _options("swimlane")
    )

    spaghetti_process = {
        "nodes": [
            {
                "id": "pick",
                "kind": "task",
                "name": "Pick",
                "location": "store",
                "outputs": ["part"],
            },
            {
                "id": "use",
                "kind": "task",
                "name": "Use",
                "location": "bench",
                "inputs": ["part"],
            },
        ],
        "edges": [{"source": "pick", "target": "use"}],
        "process": {
            "metadata": {
                "locations": [
                    {
                        "id": "store",
                        "name": "Store",
                        "kind": "storage",
                        "metadata": {"spatial": {"x": 0, "y": 0}},
                    },
                    {
                        "id": "bench",
                        "name": "Bench",
                        "kind": "processing",
                        "metadata": {"spatial": {"x": 2, "y": 0}},
                    },
                ]
            }
        },
    }
    spaghetti, _ = render_spaghetti_svg_artifact(
        spaghetti_process, _options("spaghetti")
    )
    spaghetti_rerun, _ = render_spaghetti_svg_artifact(
        spaghetti_process, _options("spaghetti")
    )

    sppm_options = _options("sppm")
    sppm = apply_svg_typography(
        "\n".join(
            _node_svg(
                node=SimpleNamespace(id="work", kind="task", label="Do work"),
                raw_node={"metadata": {"value_class": "VA"}},
                options=sppm_options,
                x=0,
                y=0,
                width=180,
                height=92,
            )
        ),
        sppm_options,
    )
    sppm_rerun = apply_svg_typography(
        "\n".join(
            _node_svg(
                node=SimpleNamespace(id="work", kind="task", label="Do work"),
                raw_node={"metadata": {"value_class": "VA"}},
                options=_options("sppm"),
                x=0,
                y=0,
                width=180,
                height=92,
            )
        ),
        _options("sppm"),
    )

    assert swimlane.content == swimlane_rerun.content
    assert spaghetti.content == spaghetti_rerun.content
    assert sppm == sppm_rerun

    value_stream_process = IR(
        name="Themed value stream",
        items=[
            {"id": "order", "name": "Order", "kind": "information"},
            {"id": "part", "name": "Part", "kind": "material"},
        ],
        nodes=[
            Node("start", "start"),
            Node(
                "work",
                "task",
                {"name": "Do work", "consumes": ["order", "part"]},
            ),
            Node("end", "end"),
        ],
        edges=[Edge("start", "work"), Edge("work", "end")],
    )
    value_stream, _ = render_value_stream_svg_artifact(
        value_stream_process, _options("value_stream")
    )
    value_stream_rerun, _ = render_value_stream_svg_artifact(
        value_stream_process, _options("value_stream")
    )

    assert value_stream.content == value_stream_rerun.content

    signature = {
        "spaghetti": {
            "background": 'width="100%" height="100%" fill="#F4F0FF"'
            in spaghetti.content,
            "font": 'font-family="Avenir Next, Arial, sans-serif"' in spaghetti.content,
            "font_size": 'font-size="15.4"' in spaghetti.content,
            "material_route": 'stroke="#A33A20"' in spaghetti.content,
            "storage": 'fill="#FFF0C2" stroke="#9A6700"' in spaghetti.content,
        },
        "sppm": {
            "font": 'font-family="Avenir Next, Arial, sans-serif"' in sppm,
            "font_size": 'font-size="15.4"' in sppm,
            "va": 'fill="#B8E6C1"' in sppm and 'stroke="#216E39"' in sppm,
        },
        "swimlane": {
            "background": 'width="100%" height="100%" fill="#F4F0FF"'
            in swimlane.content,
            "font": 'font-family="Avenir Next, Arial, sans-serif"' in swimlane.content,
            "font_size": 'font-size="13.2"' in swimlane.content,
            "lane": 'fill="#EEE9FF" stroke="#6D5BD0"' in swimlane.content,
            "va": 'fill="#B8E6C1"' in swimlane.content,
        },
        "value_stream": {
            "background": 'width="100%" height="100%" fill="#F4F0FF"'
            in value_stream.content,
            "font": 'font-family="Avenir Next, Arial, sans-serif"'
            in value_stream.content,
            "information_route": 'stroke="#235789"' in value_stream.content,
            "material_route": 'stroke="#A33A20"' in value_stream.content,
        },
    }
    expected = json.loads(_GOLDEN.read_text(encoding="utf-8"))
    assert signature == expected
