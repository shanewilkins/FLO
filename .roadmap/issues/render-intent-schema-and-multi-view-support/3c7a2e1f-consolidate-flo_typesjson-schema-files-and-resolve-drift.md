---
id: 3c7a2e1f
title: Consolidate flo_types.json schema files and resolve drift
headline: Merge duplicate schema files and ensure single source of truth for typed
  metadata validation.
priority: critical
status: closed
archived: false
issue_type: feature
milestone: render-intent-schema-and-multi-view-support
labels:
- schema
- critical-path
remote_ids: {}
created: '2026-05-13T17:30:00+00:00'
updated: '2026-05-16T19:14:04.019702+00:00'
assignee: null
estimated_hours: 3.0
due_date: null
depends_on: []
blocks:
- 4f8b5c2d
actual_start_date: null
actual_end_date: null
progress_percentage: 100.0
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: null
comments: []
github_issue: null
---

## Consolidate flo_types.json schema files and resolve drift

Merge duplicate schema files at [schema/flo_types.json](../../../schema/flo_types.json) and [src/flo/schema/flo_types.json](../../../src/flo/schema/flo_types.json), and establish single authoritative location for all typed metadata definitions.

## Why

Schema duplication creates non-deterministic validation behavior. The src copy currently includes fields (changeover_time, rework edge attributes) missing from the root copy, causing validator inconsistencies. Must consolidate before implementing strict render-intent validation.

## Acceptance Criteria

- [ ] Identify all field differences between root and src copies
- [ ] Merge into single authoritative location (recommend [schema/flo_types.json](../../../schema/flo_types.json) as root canonical source)
- [ ] Remove duplicate file and update all imports in codebase
- [ ] Verify all existing tests pass with consolidated schema
- [ ] Document schema location convention in contributing guide

## Implementation Notes

- Start by running: `diff -u schema/flo_types.json src/flo/schema/flo_types.json` to enumerate drift
- Check all imports of flo_types.json across compiler, adapters, and test fixtures
- Update [src/flo/schema/__init__.py](../../../src/flo/schema/__init__.py) to import from root location
- Ensure Pydantic model validation still works across all validator entry points

## References

- Audit finding #4 (Schema Duplication with Live Drift)
- [docs/design/render_intent_schema.md](../../../docs/design/render_intent_schema.md) - design doc
