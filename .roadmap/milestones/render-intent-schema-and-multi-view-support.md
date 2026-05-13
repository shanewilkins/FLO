---
name: render-intent-schema-and-multi-view-support
headline: Refactor render and publication intent from CLI+TOML into source metadata with strict validation, multi-view support, and bundle orchestration.
description: |-
  Implement source-driven render intent with typed metadata, strict validation, 
  multi-view rendering capability (one .flo → multiple diagram types), and a bundle 
  orchestration layer. Addresses critical architectural issues blocking human-readable 
  render schema and multi-artifact generation.
due_date: '2026-05-23T00:00:00'
status: open
archived: false
github_milestone: null
created: '2026-05-13T17:30:00+00:00'
updated: '2026-05-13T17:30:00+00:00'
project_id: null
calculated_progress: null
last_progress_update: null
completion_velocity: null
risk_level: medium
actual_start_date: null
actual_end_date: null
comments: []
---

# Render Intent Schema & Multi-View Support

Refactor render and publication intent from CLI+TOML configuration into source metadata with strict validation, multi-view rendering support, and bundle orchestration.

## Context

Current architecture splits render intent across three incoherent sources:
- CLI flags (Click and argparse in [src/flo/core/cli.py](../../../src/flo/core/cli.py) / [src/flo/core/cli_args.py](../../../src/flo/core/cli_args.py))
- TOML [diagrams.toml](../../../diagrams.toml) global and preset defaults 
- Hardcoded RenderOptions defaults in [src/flo/render/options.py](../../../src/flo/render/options.py)

This makes it impossible to:
- Express multiple render perspectives (e.g., SPPM + spaghetti from one source file)
- Validate render intent as part of compile pipeline
- Deprecate legacy configuration sources cleanly
- Maintain human-readable schema constraints

## Outcome

A strict, source-driven render intent model with:
- Typed `.render` metadata in process definitions expressing diagram type, publication format, layout hints
- Named views for multi-artifact generation (SPPM, spaghetti, topdown, etc. from one compile)
- Validated intent with clear precedence: CLI override > view intent > profiles > hard defaults
- Bundle orchestration executor emitting ordered artifacts
- Staged deprecation of TOML and legacy CLI options

## Phased Approach

- **Phase 1**: Schema consolidation (issue #3 below) + strict render-intent validation (issue #2)
- **Phase 2**: RenderIntent domain model and view-aware resolver (issue #1)  
- **Phase 3**: RenderOptions refactor and SPPM decoupling (issue #4)
- **Phase 4**: Multi-view bundle orchestration executor (issue #5) + CLI integration
- **Phase 5** (future): Deprecate TOML, unify CLI, converge metadata aliases
