---
id: a1d9f4c6
title: Introduce RenderIntent domain model and view-aware resolver
headline: Create typed RenderIntent dataclass and implement source-view-first option resolution with strict precedence.
priority: critical
status: open
archived: false
issue_type: feature
milestone: render-intent-schema-and-multi-view-support
labels: [domain-model, critical-path]
remote_ids: {}
created: '2026-05-13T17:30:00+00:00'
updated: '2026-05-13T17:30:00+00:00'
assignee: null
estimated_hours: 8
due_date: null
depends_on: [4f8b5c2d]
blocks: [5e6b7d3a, 6a2c8f9b]
actual_start_date: null
actual_end_date: null
progress_percentage: 0
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: null
comments: []
github_issue: null
---

## Introduce RenderIntent domain model and view-aware resolver

Create typed `RenderIntent` domain model and implement view-aware resolver with strict CLI > view > profile > hard-default precedence.

## Why

Current option resolution conflates CLI, TOML config, and hard defaults into one precedence chain that cannot express multi-view intent. Cannot build clean separation of concerns (what the source intends vs. what the user overrides). Must introduce RenderIntent as a first-class domain model.

## Acceptance Criteria

- [ ] Create new module [src/flo/core/render_intent.py](../../../src/flo/core/render_intent.py) with `RenderIntent` dataclass (diagram, views, layout, publication, etc.)
- [ ] Implement `RenderIntentResolver` with strict precedence: CLI override > view intent > profile defaults > hard defaults
- [ ] Extract view-selection logic from compiled metadata into resolver
- [ ] Wire resolver into [src/flo/core/__init__.py](../../../src/flo/core/__init__.py) execution pipeline before RenderOptions.from_mapping()
- [ ] Write unit tests for all precedence cases (CLI override nullifies view, profile fallback, etc.)
- [ ] Verify existing full test suite still passes

## Implementation Notes

- `RenderIntent` should be immutable dataclass capturing one view's intent
- Resolver takes: (compiled IR.process.metadata.render, CLI overrides dict, profile name) → RenderIntent
- Keep resolver pure (no side effects); separate from execution pipeline
- Consider helper method for view-aware resolution: `RenderIntentResolver.resolve_view(view_name, ...)` → RenderIntent
- Document precedence explicitly in docstring

## References

- Audit finding #2 (Option Resolution is CLI+TOML, Not Source-View-First)
- [docs/design/render_intent_schema.md](../../../docs/design/render_intent_schema.md) - precedence spec
- [src/flo/core/__init__.py#L45](../../../src/flo/core/__init__.py#L45) - execution orchestrator
- [src/flo/render/options.py](../../../src/flo/render/options.py) - current RenderOptions (target for refactor)
