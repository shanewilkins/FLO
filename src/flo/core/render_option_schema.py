"""Shared render option schema used by CLI parsing and validation."""

from __future__ import annotations

from dataclasses import dataclass
import argparse
from typing import Any


@dataclass(frozen=True)
class RenderOptionSpec:
    """Specification for one render-related CLI option."""

    key: str
    flag: str
    help_text: str
    choices: tuple[str, ...] | None = None
    value_type: type | None = None
    is_flag: bool = False
    metavar: str | None = None
    argparse_choices: bool = True


_RENDER_OPTION_SPECS: tuple[RenderOptionSpec, ...] = (
    RenderOptionSpec("diagram", "--diagram", "Diagram type for DOT output", choices=("flowchart", "swimlane", "spaghetti", "sppm")),
    RenderOptionSpec("profile", "--profile", "Projection rule profile", choices=("default", "analysis")),
    RenderOptionSpec("detail", "--detail", "Detail level", choices=("summary", "standard", "verbose")),
    RenderOptionSpec("orientation", "--orientation", "Layout orientation for DOT output", choices=("lr", "tb")),
    RenderOptionSpec("show_notes", "--show-notes", "Include node notes in DOT labels", is_flag=True),
    RenderOptionSpec("no_header", "--no-header", "Hide SPPM publication header block", is_flag=True),
    RenderOptionSpec("no_footer", "--no-footer", "Hide SPPM publication footer block", is_flag=True),
    RenderOptionSpec("subprocess_view", "--subprocess-view", "Subprocess rendering mode", choices=("expanded", "parent-only")),
    RenderOptionSpec("sppm_projection", "--sppm-projection", "SPPM hierarchy projection mode", choices=("top-level", "child-map", "inline")),
    RenderOptionSpec("sppm_focus_subprocess", "--sppm-focus-subprocess", "Subprocess node id to focus for child-map or inline SPPM output"),
    RenderOptionSpec("spaghetti_channel", "--spaghetti-channel", "Movement channel for spaghetti diagrams", choices=("both", "material", "people")),
    RenderOptionSpec("spaghetti_people_mode", "--spaghetti-people-mode", "People trace mode for spaghetti diagrams", choices=("worker", "aggregate")),
    RenderOptionSpec("sppm_theme", "--sppm-theme", "Color theme for SPPM diagrams", choices=("default", "print", "monochrome")),
    RenderOptionSpec("layout_wrap", "--layout-wrap", "Shared autoformat wrapping mode (orientation-aware)", choices=("auto", "off")),
    RenderOptionSpec("layout_fit", "--layout-fit", "Shared autoformat fit mode", choices=("fit-preferred", "fit-strict")),
    RenderOptionSpec("layout_spacing", "--layout-spacing", "Shared graph spacing profile", choices=("standard", "compact")),
    RenderOptionSpec(
        "publication_page_format",
        "--publication-page-format",
        "Named publication page preset (letter, a4, legal, tabloid)",
        choices=("letter", "a4", "legal", "tabloid"),
        argparse_choices=False,
    ),
    RenderOptionSpec("sppm_step_numbering", "--sppm-step-numbering", "SPPM step numbering mode", choices=("off", "node", "edge")),
    RenderOptionSpec("sppm_label_density", "--sppm-label-density", "SPPM label density mode", choices=("full", "compact", "teaching")),
    RenderOptionSpec("sppm_wrap_strategy", "--sppm-wrap-strategy", "Text wrapping strategy for SPPM labels", choices=("word", "balanced", "hard")),
    RenderOptionSpec("sppm_truncation_policy", "--sppm-truncation-policy", "Label truncation policy for SPPM text", choices=("ellipsis", "clip", "none")),
    RenderOptionSpec("layout_max_width_px", "--layout-max-width-px", "Max layout width hint for autoformat wrapping (supports px, in, cm)"),
    RenderOptionSpec("layout_target_columns", "--layout-target-columns", "Target columns/steps per wrapped chunk", value_type=int),
    RenderOptionSpec("sppm_max_label_step_name", "--sppm-max-label-step-name", "Max step-name label length for SPPM", value_type=int),
    RenderOptionSpec("sppm_max_label_workers", "--sppm-max-label-workers", "Max workers label length for SPPM", value_type=int),
    RenderOptionSpec("sppm_max_label_ctwt", "--sppm-max-label-ctwt", "Max CT/WT label length for SPPM", value_type=int),
    RenderOptionSpec("sppm_output_profile", "--sppm-output-profile", "SPPM output profile preset", choices=("default", "book", "web", "print", "slide")),
    RenderOptionSpec("render_to", "--render-to", "Render DOT output to an image file via Graphviz", metavar="FILE"),
)


def iter_render_option_specs(*, include_render_to: bool = True) -> tuple[RenderOptionSpec, ...]:
    """Return ordered render option specifications for CLI wiring."""
    if include_render_to:
        return _RENDER_OPTION_SPECS
    return tuple(spec for spec in _RENDER_OPTION_SPECS if spec.key != "render_to")


def render_option_keys(*, include_render_to: bool = True) -> tuple[str, ...]:
    """Return the canonical list of render option keys."""
    return tuple(spec.key for spec in iter_render_option_specs(include_render_to=include_render_to))


def add_argparse_render_options(parser: argparse.ArgumentParser, *, include_render_to: bool = True) -> None:
    """Register shared render options on an argparse parser."""
    for spec in iter_render_option_specs(include_render_to=include_render_to):
        kwargs: dict[str, Any] = {"help": spec.help_text}
        if spec.is_flag:
            kwargs["action"] = "store_true"
        else:
            if spec.choices is not None and spec.argparse_choices:
                kwargs["choices"] = list(spec.choices)
            if spec.value_type is not None:
                kwargs["type"] = spec.value_type
            if spec.metavar is not None:
                kwargs["metavar"] = spec.metavar
        parser.add_argument(spec.flag, **kwargs)


def build_render_options_from_namespace(parsed: object, *, include_render_to: bool = True) -> dict[str, Any]:
    """Extract shared render options from an argparse namespace-like object."""
    options: dict[str, Any] = {}
    for spec in iter_render_option_specs(include_render_to=include_render_to):
        value = getattr(parsed, spec.key, None)
        if spec.is_flag:
            if bool(value):
                options[spec.key] = True
            continue
        if value is None:
            continue
        if isinstance(value, str) and value == "":
            continue
        options[spec.key] = value
    return options
