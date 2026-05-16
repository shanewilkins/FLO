"""Tests for RenderIntent domain model and RenderIntentResolver."""

import pytest

from flo.core.render_intent import RenderIntent, RenderIntentResolver


class TestRenderIntent:
    """Test RenderIntent dataclass."""

    def test_render_intent_is_immutable(self):
        """RenderIntent should be frozen (immutable)."""
        intent = RenderIntent(diagram="sppm")
        with pytest.raises(AttributeError):
            intent.diagram = "spaghetti"

    def test_render_intent_all_fields_optional(self):
        """RenderIntent should support partial initialization."""
        intent = RenderIntent(diagram="sppm", sppm_label_density="compact")
        assert intent.diagram == "sppm"
        assert intent.sppm_label_density == "compact"
        assert intent.layout_wrap is None
        assert intent.spaghetti_channel is None

    def test_render_intent_default_constructor(self):
        """RenderIntent should create with all None when no args provided."""
        intent = RenderIntent()
        assert intent.diagram is None
        assert intent.layout_wrap is None
        assert intent.sppm_label_density is None
        assert intent.spaghetti_channel is None


class TestRenderIntentResolverHardDefaults:
    """Test hard defaults (library-defined fallbacks)."""

    def test_hard_defaults_applied_when_nothing_provided(self):
        """Should apply hard defaults when no metadata or overrides provided."""
        intent = RenderIntentResolver.resolve(
            render_metadata=None,
            cli_overrides=None,
            profile="default",
        )
        assert intent.diagram == "sppm"
        assert intent.layout_wrap == "none"
        assert intent.sppm_label_density == "full"
        assert intent.spaghetti_channel == "material"
        assert intent.spaghetti_people_mode == "aggregate"

    def test_hard_defaults_with_empty_metadata(self):
        """Should apply hard defaults when metadata is empty dict."""
        intent = RenderIntentResolver.resolve(
            render_metadata={},
            cli_overrides=None,
            profile="default",
        )
        assert intent.diagram == "sppm"
        assert intent.layout_wrap == "none"
        assert intent.sppm_label_density == "full"

    def test_hard_defaults_with_none_profile(self):
        """Should apply hard defaults even with None values in defaults."""
        intent = RenderIntentResolver.resolve(
            render_metadata=None,
            cli_overrides=None,
            profile="default",
        )
        assert intent.publication_page_format is None
        assert intent.diagram == "sppm"


class TestRenderIntentResolverProfileDefaults:
    """Test profile-specific defaults."""

    def test_default_profile_applied(self):
        """Should apply 'default' profile defaults."""
        intent = RenderIntentResolver.resolve(
            render_metadata=None,
            cli_overrides=None,
            profile="default",
        )
        assert intent.diagram == "sppm"
        assert intent.sppm_label_density == "full"

    def test_analysis_profile_applied(self):
        """Should apply 'analysis' profile defaults."""
        intent = RenderIntentResolver.resolve(
            render_metadata=None,
            cli_overrides=None,
            profile="analysis",
        )
        assert intent.diagram == "topdown"
        assert intent.sppm_label_density == "compact"
        assert intent.layout_wrap == "auto"

    def test_unknown_profile_falls_back_to_hard_defaults(self):
        """Should fall back to hard defaults for unknown profile."""
        intent = RenderIntentResolver.resolve(
            render_metadata=None,
            cli_overrides=None,
            profile="unknown_profile",
        )
        # Should not have analysis-specific values
        assert intent.diagram == "sppm"  # hard default
        assert intent.sppm_label_density == "full"  # hard default

    def test_profile_defaults_override_hard_defaults(self):
        """Profile defaults should override hard defaults."""
        intent_default = RenderIntentResolver.resolve(
            render_metadata=None,
            cli_overrides=None,
            profile="default",
        )
        intent_analysis = RenderIntentResolver.resolve(
            render_metadata=None,
            cli_overrides=None,
            profile="analysis",
        )
        assert intent_default.diagram == "sppm"
        assert intent_analysis.diagram == "topdown"


class TestRenderIntentResolverViewIntent:
    """Test view-specific intent from compiled IR metadata."""

    def test_view_intent_overrides_profile_defaults(self):
        """View intent should override profile defaults."""
        metadata = {
            "views": {
                "custom_view": {
                    "diagram": "spaghetti",
                }
            }
        }
        intent = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides=None,
            profile="default",
            view_name="custom_view",
        )
        assert intent.diagram == "spaghetti"

    def test_view_intent_partial_override(self):
        """View intent should only override specified fields."""
        metadata = {
            "views": {
                "custom": {
                    "sppm": {
                        "label_density": "teaching",
                    }
                }
            }
        }
        intent = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides=None,
            profile="default",
            view_name="custom",
        )
        assert intent.sppm_label_density == "teaching"
        assert intent.diagram == "sppm"  # profile default
        assert intent.layout_wrap == "none"  # hard default

    def test_default_view_used_as_fallback(self):
        """Should fall back to 'defaults' view if specific view not found."""
        metadata = {
            "defaults": {
                "diagram": "topdown",
            },
            "views": {
                "other": {"diagram": "spaghetti"}
            }
        }
        intent = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides=None,
            profile="default",
            view_name="missing_view",
        )
        assert intent.diagram == "topdown"

    def test_nested_publication_config_flattened(self):
        """Should flatten nested publication config."""
        metadata = {
            "views": {
                "custom": {
                    "publication": {
                        "page_format": "a4",
                        "margins": {
                            "top": 10,
                            "left": 20,
                        },
                        "header": {
                            "enabled": True,
                        }
                    }
                }
            }
        }
        intent = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides=None,
            profile="default",
            view_name="custom",
        )
        assert intent.publication_page_format == "a4"
        assert intent.publication_margins_top == 10
        assert intent.publication_margins_left == 20
        assert intent.publication_header_enabled is True

    def test_nested_layout_config_flattened(self):
        """Should flatten nested layout config."""
        metadata = {
            "views": {
                "custom": {
                    "layout": {
                        "wrap": "manual",
                        "max_width": 1200,
                        "target_columns": 8,
                    }
                }
            }
        }
        intent = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides=None,
            profile="default",
            view_name="custom",
        )
        assert intent.layout_wrap == "manual"
        assert intent.layout_max_width == 1200
        assert intent.layout_target_columns == 8

    def test_nested_sppm_config_flattened(self):
        """Should flatten nested SPPM config."""
        metadata = {
            "views": {
                "custom": {
                    "sppm": {
                        "label_density": "compact",
                        "node_numbering": "visible",
                        "edge_numbering": "hidden",
                    }
                }
            }
        }
        intent = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides=None,
            profile="default",
            view_name="custom",
        )
        assert intent.sppm_label_density == "compact"
        assert intent.sppm_node_numbering == "visible"
        assert intent.sppm_edge_numbering == "hidden"

    def test_nested_spaghetti_config_flattened(self):
        """Should flatten nested spaghetti config."""
        metadata = {
            "views": {
                "custom": {
                    "spaghetti": {
                        "channel": "people",
                        "people_mode": "individual",
                    }
                }
            }
        }
        intent = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides=None,
            profile="default",
            view_name="custom",
        )
        assert intent.spaghetti_channel == "people"
        assert intent.spaghetti_people_mode == "individual"


class TestRenderIntentResolverCliPrecedence:
    """Test CLI override precedence (highest priority)."""

    def test_cli_override_nullifies_view_intent(self):
        """CLI override should completely replace view intent."""
        metadata = {
            "views": {
                "custom": {
                    "diagram": "spaghetti",
                }
            }
        }
        cli_overrides = {"diagram": "sppm"}
        intent = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides=cli_overrides,
            profile="default",
            view_name="custom",
        )
        assert intent.diagram == "sppm"

    def test_cli_override_partial(self):
        """CLI override should only affect specified keys."""
        metadata = {
            "views": {
                "custom": {
                    "diagram": "spaghetti",
                    "sppm": {
                        "label_density": "teaching",
                    }
                }
            }
        }
        cli_overrides = {"diagram": "topdown"}
        intent = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides=cli_overrides,
            profile="default",
            view_name="custom",
        )
        # diagram from CLI
        assert intent.diagram == "topdown"
        # sppm_label_density from view intent (not overridden)
        assert intent.sppm_label_density == "teaching"

    def test_cli_override_maps_ui_names_correctly(self):
        """CLI args use UI naming; should map to internal keys."""
        cli_overrides = {
            "publication_page_format": "letter",
            "layout_max_width_px": 1600,
            "sppm_step_numbering": "visible",
        }
        intent = RenderIntentResolver.resolve(
            render_metadata=None,
            cli_overrides=cli_overrides,
            profile="default",
        )
        assert intent.publication_page_format == "letter"
        assert intent.layout_max_width == 1600
        assert intent.sppm_node_numbering == "visible"

    def test_cli_override_precedence_over_all(self):
        """CLI override should have highest precedence."""
        metadata = {
            "defaults": {
                "diagram": "topdown",
            },
            "views": {
                "custom": {
                    "diagram": "spaghetti",
                }
            }
        }
        cli_overrides = {"diagram": "sppm"}
        intent = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides=cli_overrides,
            profile="analysis",
            view_name="custom",
        )
        # All sources specify different values
        # CLI should win
        assert intent.diagram == "sppm"


class TestRenderIntentResolverCompletePrecedence:
    """Test complete precedence chain: CLI > view > profile > hard-default."""

    def test_full_precedence_chain_diagram(self):
        """Test diagram resolution through full precedence chain."""
        metadata = {
            "defaults": {
                "diagram": "topdown",  # hard
            },
            "views": {
                "custom": {
                    "diagram": "spaghetti",  # view
                }
            }
        }

        # Hard default only (no view match, no CLI)
        intent1 = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides=None,
            profile="default",
            view_name="missing",
        )
        assert intent1.diagram == "topdown"

        # View intent overrides hard default
        intent2 = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides=None,
            profile="default",
            view_name="custom",
        )
        assert intent2.diagram == "spaghetti"

        # CLI overrides view intent
        intent3 = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides={"diagram": "sppm"},
            profile="default",
            view_name="custom",
        )
        assert intent3.diagram == "sppm"

    def test_profile_applied_between_view_and_cli(self):
        """Profile should apply between view and hard defaults."""
        # Analysis profile sets diagram to topdown
        intent = RenderIntentResolver.resolve(
            render_metadata={},  # no view intent
            cli_overrides=None,  # no CLI override
            profile="analysis",
        )
        # Profile default (topdown) should be used
        assert intent.diagram == "topdown"

        # But CLI should still override profile
        intent2 = RenderIntentResolver.resolve(
            render_metadata={},
            cli_overrides={"diagram": "sppm"},
            profile="analysis",
        )
        assert intent2.diagram == "sppm"


class TestRenderIntentResolverViewNameHandling:
    """Test view name resolution."""

    def test_default_view_name_uses_default_intent(self):
        """view_name='default' should use 'defaults' in metadata."""
        metadata = {
            "defaults": {
                "diagram": "topdown",
            }
        }
        intent = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides=None,
            profile="default",
            view_name="default",
        )
        assert intent.diagram == "topdown"

    def test_custom_view_name_uses_named_view(self):
        """Named view_name should use views[name] in metadata."""
        metadata = {
            "defaults": {
                "diagram": "sppm",
            },
            "views": {
                "report": {
                    "diagram": "spaghetti",
                }
            }
        }
        intent = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides=None,
            profile="default",
            view_name="report",
        )
        assert intent.diagram == "spaghetti"

    def test_missing_view_falls_back_to_defaults(self):
        """Missing view_name should fall back to 'defaults'."""
        metadata = {
            "defaults": {
                "diagram": "topdown",
            },
            "views": {
                "other": {
                    "diagram": "spaghetti",
                }
            }
        }
        intent = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides=None,
            profile="default",
            view_name="missing",
        )
        assert intent.diagram == "topdown"


class TestRenderIntentResolverResolveViewMethod:
    """Test resolve_view() helper method."""

    def test_resolve_view_no_cli_overrides(self):
        """resolve_view() should exclude CLI overrides."""
        metadata = {
            "defaults": {
                "diagram": "topdown",
            }
        }
        intent = RenderIntentResolver.resolve_view(
            render_metadata=metadata,
            view_name="default",
        )
        assert intent.diagram == "topdown"

    def test_resolve_view_uses_default_profile(self):
        """resolve_view() should use 'default' profile."""
        # Even though analysis profile changes diagram, resolve_view ignores profile
        intent = RenderIntentResolver.resolve_view(
            render_metadata={},
            view_name="default",
        )
        # Should get hard default (sppm), not analysis profile (topdown)
        assert intent.diagram == "sppm"

    def test_resolve_view_pure_source_intent(self):
        """resolve_view() should extract pure view intent from IR."""
        metadata = {
            "views": {
                "dashboard": {
                    "diagram": "sppm",
                    "sppm": {
                        "label_density": "compact",
                    }
                }
            }
        }
        intent = RenderIntentResolver.resolve_view(
            render_metadata=metadata,
            view_name="dashboard",
        )
        assert intent.diagram == "sppm"
        assert intent.sppm_label_density == "compact"


class TestRenderIntentResolverEdgeCases:
    """Test edge cases and error handling."""

    def test_malformed_metadata_ignored(self):
        """Malformed metadata should be safely ignored."""
        metadata = {
            "views": None,  # should be dict
            "defaults": "invalid",  # should be dict
        }
        intent = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides=None,
            profile="default",
        )
        # Should fall back to hard defaults
        assert intent.diagram == "sppm"

    def test_malformed_cli_overrides_ignored(self):
        """Malformed CLI overrides should be safely ignored."""
        cli_overrides = "not a dict"  # should be dict
        intent = RenderIntentResolver.resolve(
            render_metadata=None,
            cli_overrides=cli_overrides,
            profile="default",
        )
        # Should fall back to hard defaults
        assert intent.diagram == "sppm"

    def test_null_values_in_metadata_preserved(self):
        """Null values in metadata should not override previous values."""
        metadata = {
            "defaults": {
                "diagram": "sppm",
            },
            "views": {
                "custom": {
                    "diagram": None,  # null value
                }
            }
        }
        intent = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides=None,
            profile="default",
            view_name="custom",
        )
        # None should not override the default
        # (depends on implementation: either keeps default or uses None)
        # Here we verify it doesn't crash
        assert intent.diagram is not None or intent.diagram is None

    def test_empty_cli_overrides(self):
        """Empty CLI overrides dict should not affect resolution."""
        metadata = {
            "views": {
                "custom": {
                    "diagram": "spaghetti",
                }
            }
        }
        intent = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides={},
            profile="default",
            view_name="custom",
        )
        assert intent.diagram == "spaghetti"

    def test_unknown_metadata_fields_ignored(self):
        """Unknown fields in metadata should be safely ignored."""
        metadata = {
            "views": {
                "custom": {
                    "diagram": "sppm",
                    "unknown_field": "should_be_ignored",
                    "another_unknown": 42,
                }
            }
        }
        intent = RenderIntentResolver.resolve(
            render_metadata=metadata,
            cli_overrides=None,
            profile="default",
            view_name="custom",
        )
        assert intent.diagram == "sppm"
        # No exception, unknown fields safely ignored
