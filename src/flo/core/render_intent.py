"""RenderIntent domain model and view-aware resolver.

Introduces RenderIntent as a first-class domain model that separates what the
source intends (from compiled IR metadata) from what the user overrides (CLI args).

Implements strict precedence: CLI override > view intent > profile defaults > hard defaults.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


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
    diagram: Optional[str] = None

    # Publication config
    publication_page_format: Optional[str] = None
    publication_margins_top: Optional[int] = None
    publication_margins_right: Optional[int] = None
    publication_margins_bottom: Optional[int] = None
    publication_margins_left: Optional[int] = None
    publication_header_enabled: Optional[bool] = None
    publication_footer_enabled: Optional[bool] = None

    # Layout config
    layout_wrap: Optional[str] = None
    layout_max_width: Optional[int] = None
    layout_target_columns: Optional[int] = None

    # SPPM config
    sppm_label_density: Optional[str] = None
    sppm_node_numbering: Optional[str] = None
    sppm_edge_numbering: Optional[str] = None

    # Spaghetti config
    spaghetti_channel: Optional[str] = None
    spaghetti_people_mode: Optional[str] = None


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
    _HARD_DEFAULTS = {
        "diagram": "sppm",
        "publication_page_format": None,
        "layout_wrap": "none",
        "sppm_label_density": "full",
        "spaghetti_channel": "material",
        "spaghetti_people_mode": "aggregate",
    }

    # Profile defaults (user-facing styles)
    _PROFILE_DEFAULTS: dict[str, dict[str, Any]] = {
        "default": {
            "diagram": "sppm",
            "publication_page_format": None,
            "layout_wrap": "none",
            "sppm_label_density": "full",
        },
        "analysis": {
            "diagram": "topdown",
            "publication_page_format": None,
            "layout_wrap": "auto",
            "sppm_label_density": "compact",
        },
    }

    @classmethod
    def resolve(
        cls,
        render_metadata: Optional[dict[str, Any]],
        cli_overrides: Optional[dict[str, Any]],
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
        render_metadata: Optional[dict[str, Any]],
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
        render_metadata: Optional[dict[str, Any]],
        view_name: str,
    ) -> dict[str, Any]:
        """Extract intent from IR.process.metadata.render.views[view_name]."""
        if not render_metadata or not isinstance(render_metadata, dict):
            return {}

        # Try the specific view first
        views = render_metadata.get("views", {})
        if isinstance(views, dict):
            view = views.get(view_name)
            if view and isinstance(view, dict):
                return cls._flatten_view_structure(view)

        # Fall back to defaults if specific view not found
        defaults = render_metadata.get("defaults")
        if defaults and isinstance(defaults, dict):
            return cls._flatten_view_structure(defaults)

        return {}

    @classmethod
    def _extract_cli_intent(
        cls, cli_overrides: Optional[dict[str, Any]]
    ) -> dict[str, Any]:
        """Extract intent from CLI arguments, mapping UI names to intent keys."""
        if not cli_overrides or not isinstance(cli_overrides, dict):
            return {}

        intent = {}

        # Diagram type
        if "diagram" in cli_overrides:
            intent["diagram"] = cli_overrides.get("diagram")

        # Publication config
        if "publication_page_format" in cli_overrides:
            intent["publication_page_format"] = cli_overrides.get(
                "publication_page_format"
            )
        if "layout_max_width_px" in cli_overrides:
            intent["layout_max_width"] = cli_overrides.get("layout_max_width_px")

        # Layout config
        if "layout_wrap" in cli_overrides:
            intent["layout_wrap"] = cli_overrides.get("layout_wrap")
        if "layout_target_columns" in cli_overrides:
            intent["layout_target_columns"] = cli_overrides.get("layout_target_columns")

        # SPPM config
        if "sppm_label_density" in cli_overrides:
            intent["sppm_label_density"] = cli_overrides.get("sppm_label_density")
        if "sppm_step_numbering" in cli_overrides:
            intent["sppm_node_numbering"] = cli_overrides.get("sppm_step_numbering")

        # Spaghetti config
        if "spaghetti_channel" in cli_overrides:
            intent["spaghetti_channel"] = cli_overrides.get("spaghetti_channel")
        if "spaghetti_people_mode" in cli_overrides:
            intent["spaghetti_people_mode"] = cli_overrides.get("spaghetti_people_mode")

        return intent

    @classmethod
    def _flatten_view_structure(cls, view: dict[str, Any]) -> dict[str, Any]:
        """Flatten nested view structure (publication, layout, sppm, spaghetti)."""
        intent = {}

        # Top-level diagram
        if "diagram" in view:
            intent["diagram"] = view.get("diagram")

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
            layout_wrap=resolved.get("layout_wrap"),
            layout_max_width=resolved.get("layout_max_width"),
            layout_target_columns=resolved.get("layout_target_columns"),
            sppm_label_density=resolved.get("sppm_label_density"),
            sppm_node_numbering=resolved.get("sppm_node_numbering"),
            sppm_edge_numbering=resolved.get("sppm_edge_numbering"),
            spaghetti_channel=resolved.get("spaghetti_channel"),
            spaghetti_people_mode=resolved.get("spaghetti_people_mode"),
        )
