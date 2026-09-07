"""RenderIntent domain model and view-aware resolver.

Introduces RenderIntent as a first-class domain model that separates what the
source intends (from compiled IR metadata) from what the user overrides (CLI args).

Implements strict precedence: CLI override > view intent > profile defaults > hard defaults.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar


@dataclass(frozen=True)
class RenderIntent:
    """Immutable representation of a single view's rendering intent.

    Captures the intention of the source (from IR metadata) after applying
    strict precedence resolution. Each view has one RenderIntent that merges:
    1. Hard defaults (library defaults)
    2. Profile defaults (user-selected rendering style)
    3. View intent (from IR process.metadata.render.views[name])
    4. CLI overrides (explicit command-line arguments)
    """

    # Diagram type
    diagram: str | None = None

    # Publication config
    publication_page_format: str | None = None
    publication_margins_top: int | None = None
    publication_margins_right: int | None = None
    publication_margins_bottom: int | None = None
    publication_margins_left: int | None = None
    publication_header_enabled: bool | None = None
    publication_footer_enabled: bool | None = None

    # Shared presentation theme
    theme: str | None = None
    background_color: str | None = None
    font_family: Any = None
    typography_scale: float | None = None

    # Layout config
    layout_wrap: str | None = None
    layout_max_width: int | None = None
    layout_target_columns: int | None = None
    layout_width: Any = None
    layout_height: Any = None
    layout_overflow: str | None = None

    # SPPM config
    sppm_label_density: str | None = None
    sppm_node_numbering: str | None = None
    sppm_edge_numbering: str | None = None

    # Spaghetti config
    spaghetti_channel: str | None = None
    spaghetti_people_mode: str | None = None
    spaghetti_strict_spatial: bool | None = None


class RenderIntentResolver:
    """Resolves render intent from compiled IR with strict precedence.

    Precedence (highest to lowest):
    1. CLI overrides (explicit command-line arguments)
    2. View intent (from IR.process.metadata.render.views[view_name])
    3. Profile defaults (from configuration profile)
    4. Hard defaults (library defaults)

    Pure resolver with no side effects. Separate from execution pipeline.
    """

    # Hard defaults (library-defined fallbacks)
    _HARD_DEFAULTS: ClassVar[dict[str, str | None]] = {
        "diagram": "sppm",
        "publication_page_format": None,
        "layout_wrap": "none",
        "layout_overflow": "error",
        "sppm_label_density": "full",
        "spaghetti_channel": "material",
        "spaghetti_people_mode": "aggregate",
    }

    # Profile defaults (user-facing styles)
    _PROFILE_DEFAULTS: ClassVar[dict[str, dict[str, Any]]] = {
        "default": {
            "diagram": "sppm",
            "publication_page_format": None,
            "layout_wrap": "none",
            "sppm_label_density": "full",
        },
        "analysis": {
            "diagram": "sppm",
            "publication_page_format": None,
            "layout_wrap": "auto",
            "sppm_label_density": "compact",
        },
    }

    @classmethod
    def resolve(
        cls,
        render_metadata: dict[str, Any] | None,
        cli_overrides: Any,
        profile: str = "default",
        view_name: str = "default",
    ) -> RenderIntent:
        """Resolve a RenderIntent for the specified view.

        Args:
            render_metadata: IR.process.metadata.render from compiled IR
            cli_overrides: Command-line override arguments
            profile: Selected rendering profile ("default", "analysis", etc.)
            view_name: Name of view in render_metadata.views (or "default")

        Returns:
            RenderIntent with resolved values following strict precedence.
        """
        # Start with hard defaults
        resolved = dict(cls._HARD_DEFAULTS)

        # Apply profile defaults
        profile_defaults = cls._PROFILE_DEFAULTS.get(profile, {})
        for key, value in profile_defaults.items():
            if value is not None:
                resolved[key] = value

        # Apply view intent from IR metadata
        view_intent = cls._extract_view_intent(render_metadata, view_name)
        resolved.update(view_intent)

        # Apply CLI overrides (nullifies view intent)
        cli_intent = cls._extract_cli_intent(cli_overrides)
        resolved.update(cli_intent)

        return cls._build_render_intent(resolved)

    @classmethod
    def resolve_view(
        cls,
        render_metadata: dict[str, Any] | None,
        view_name: str = "default",
    ) -> RenderIntent:
        """Resolve RenderIntent for a view without CLI overrides.

        Useful for extracting the source's view intent independent of user input.

        Args:
            render_metadata: IR.process.metadata.render from compiled IR
            view_name: Name of view in render_metadata.views (or "default")

        Returns:
            RenderIntent with view intent only (no CLI overrides).
        """
        return cls.resolve(
            render_metadata=render_metadata,
            cli_overrides=None,
            profile="default",
            view_name=view_name,
        )

    @classmethod
    def _extract_view_intent(
        cls,
        render_metadata: dict[str, Any] | None,
        view_name: str,
    ) -> dict[str, Any]:
        """Extract intent from IR.process.metadata.render.views[view_name]."""
        if not render_metadata or not isinstance(render_metadata, dict):
            return {}

        intent: dict[str, Any] = {}
        defaults = render_metadata.get("defaults")
        if defaults and isinstance(defaults, dict):
            intent.update(cls._flatten_view_structure(defaults))

        # A named view overrides process render defaults field by field.
        views = render_metadata.get("views", {})
        if isinstance(views, dict):
            view = views.get(view_name)
            if view and isinstance(view, dict):
                intent.update(cls._flatten_view_structure(view))
        return intent

    @classmethod
    def _extract_cli_intent(
        cls, cli_overrides: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Extract intent from CLI arguments, mapping UI names to intent keys."""
        if not cli_overrides or not isinstance(cli_overrides, dict):
            return {}

        intent: dict[str, Any] = {}
        cls._copy_cli_intent_values(
            cli_overrides,
            {
                "diagram": "diagram",
                "publication_page_format": "publication_page_format",
                "layout_max_width_px": "layout_max_width",
                "layout_width": "layout_width",
                "layout_height": "layout_height",
                "layout_overflow": "layout_overflow",
                "theme": "theme",
                "background_color": "background_color",
                "font_family": "font_family",
                "typography_scale": "typography_scale",
                "layout_wrap": "layout_wrap",
                "layout_target_columns": "layout_target_columns",
                "sppm_label_density": "sppm_label_density",
                "sppm_step_numbering": "sppm_node_numbering",
                "spaghetti_channel": "spaghetti_channel",
                "spaghetti_people_mode": "spaghetti_people_mode",
                "spaghetti_strict_spatial": "spaghetti_strict_spatial",
            },
            intent,
        )
        return intent

    @staticmethod
    def _copy_cli_intent_values(
        cli_overrides: dict[str, Any],
        key_mapping: dict[str, str],
        intent: dict[str, Any],
    ) -> None:
        for source_key, intent_key in key_mapping.items():
            if source_key in cli_overrides:
                intent[intent_key] = cli_overrides.get(source_key)

    @classmethod
    def _flatten_view_structure(cls, view: dict[str, Any]) -> dict[str, Any]:
        """Flatten nested view structure (publication, layout, sppm, spaghetti)."""
        intent = {}

        # Top-level diagram
        if "diagram" in view:
            intent["diagram"] = view.get("diagram")
        for key in ("theme", "background_color", "font_family", "typography_scale"):
            if key in view:
                intent[key] = view.get(key)

        canvas = view.get("canvas")
        if isinstance(canvas, dict) and "background" in canvas:
            intent["background_color"] = canvas.get("background")
        typography = view.get("typography")
        if isinstance(typography, dict):
            if "font_family" in typography:
                intent["font_family"] = typography.get("font_family")
            if "scale" in typography:
                intent["typography_scale"] = typography.get("scale")
        style = view.get("style")
        if isinstance(style, dict):
            canvas = style.get("canvas")
            if isinstance(canvas, dict) and "background" in canvas:
                intent["background_color"] = canvas.get("background")
            typography = style.get("typography")
            if isinstance(typography, dict):
                if "font_family" in typography:
                    intent["font_family"] = typography.get("font_family")
                if "scale" in typography:
                    intent["typography_scale"] = typography.get("scale")

        # Configuration sections
        intent.update(cls._extract_publication_config(view.get("publication")))
        intent.update(cls._extract_layout_config(view.get("layout")))
        intent.update(cls._extract_sppm_config(view.get("sppm")))
        intent.update(cls._extract_spaghetti_config(view.get("spaghetti")))

        return intent

    @classmethod
    def _extract_publication_config(cls, publication: Any) -> dict[str, Any]:
        """Extract publication configuration."""
        intent = {}
        if not publication or not isinstance(publication, dict):
            return intent

        if "page_format" in publication:
            intent["publication_page_format"] = publication.get("page_format")

        intent.update(cls._extract_publication_margins(publication.get("margins")))
        intent.update(cls._extract_publication_header(publication.get("header")))
        intent.update(cls._extract_publication_footer(publication.get("footer")))

        return intent

    @classmethod
    def _extract_publication_margins(cls, margins: Any) -> dict[str, Any]:
        """Extract publication margins."""
        intent = {}
        if not margins or not isinstance(margins, dict):
            return intent

        if "top" in margins:
            intent["publication_margins_top"] = margins.get("top")
        if "right" in margins:
            intent["publication_margins_right"] = margins.get("right")
        if "bottom" in margins:
            intent["publication_margins_bottom"] = margins.get("bottom")
        if "left" in margins:
            intent["publication_margins_left"] = margins.get("left")

        return intent

    @classmethod
    def _extract_publication_header(cls, header: Any) -> dict[str, Any]:
        """Extract publication header config."""
        if header and isinstance(header, dict) and "enabled" in header:
            return {"publication_header_enabled": header.get("enabled")}
        return {}

    @classmethod
    def _extract_publication_footer(cls, footer: Any) -> dict[str, Any]:
        """Extract publication footer config."""
        if footer and isinstance(footer, dict) and "enabled" in footer:
            return {"publication_footer_enabled": footer.get("enabled")}
        return {}

    @classmethod
    def _extract_layout_config(cls, layout: Any) -> dict[str, Any]:
        """Extract layout configuration."""
        intent = {}
        if not layout or not isinstance(layout, dict):
            return intent

        if "wrap" in layout:
            intent["layout_wrap"] = layout.get("wrap")
        if "max_width" in layout:
            intent["layout_max_width"] = layout.get("max_width")
        if "target_columns" in layout:
            intent["layout_target_columns"] = layout.get("target_columns")
        for key in ("width", "height", "overflow"):
            if key in layout:
                intent[f"layout_{key}"] = layout.get(key)

        return intent

    @classmethod
    def _extract_sppm_config(cls, sppm: Any) -> dict[str, Any]:
        """Extract SPPM configuration."""
        intent = {}
        if not sppm or not isinstance(sppm, dict):
            return intent

        if "label_density" in sppm:
            intent["sppm_label_density"] = sppm.get("label_density")
        if "node_numbering" in sppm:
            intent["sppm_node_numbering"] = sppm.get("node_numbering")
        if "edge_numbering" in sppm:
            intent["sppm_edge_numbering"] = sppm.get("edge_numbering")

        return intent

    @classmethod
    def _extract_spaghetti_config(cls, spaghetti: Any) -> dict[str, Any]:
        """Extract spaghetti configuration."""
        intent = {}
        if not spaghetti or not isinstance(spaghetti, dict):
            return intent

        if "channel" in spaghetti:
            intent["spaghetti_channel"] = spaghetti.get("channel")
        if "people_mode" in spaghetti:
            intent["spaghetti_people_mode"] = spaghetti.get("people_mode")
        if "strict_spatial" in spaghetti:
            intent["spaghetti_strict_spatial"] = spaghetti.get("strict_spatial")

        return intent

    @classmethod
    def _build_render_intent(cls, resolved: dict[str, Any]) -> RenderIntent:
        """Build RenderIntent dataclass from resolved intent dict."""
        return RenderIntent(
            diagram=resolved.get("diagram"),
            publication_page_format=resolved.get("publication_page_format"),
            publication_margins_top=resolved.get("publication_margins_top"),
            publication_margins_right=resolved.get("publication_margins_right"),
            publication_margins_bottom=resolved.get("publication_margins_bottom"),
            publication_margins_left=resolved.get("publication_margins_left"),
            publication_header_enabled=resolved.get("publication_header_enabled"),
            publication_footer_enabled=resolved.get("publication_footer_enabled"),
            theme=resolved.get("theme"),
            background_color=resolved.get("background_color"),
            font_family=resolved.get("font_family"),
            typography_scale=resolved.get("typography_scale"),
            layout_wrap=resolved.get("layout_wrap"),
            layout_max_width=resolved.get("layout_max_width"),
            layout_target_columns=resolved.get("layout_target_columns"),
            layout_width=resolved.get("layout_width"),
            layout_height=resolved.get("layout_height"),
            layout_overflow=resolved.get("layout_overflow"),
            sppm_label_density=resolved.get("sppm_label_density"),
            sppm_node_numbering=resolved.get("sppm_node_numbering"),
            sppm_edge_numbering=resolved.get("sppm_edge_numbering"),
            spaghetti_channel=resolved.get("spaghetti_channel"),
            spaghetti_people_mode=resolved.get("spaghetti_people_mode"),
            spaghetti_strict_spatial=resolved.get("spaghetti_strict_spatial"),
        )
