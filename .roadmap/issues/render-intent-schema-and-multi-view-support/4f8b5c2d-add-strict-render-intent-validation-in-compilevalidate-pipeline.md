---
id: 4f8b5c2d
title: Add strict render-intent validation in compile/validate pipeline
headline: Extend schema and validator to enforce render-intent structure and catch
  malformed process.metadata.render keys.
priority: critical
status: in-progress
archived: false
issue_type: feature
milestone: render-intent-schema-and-multi-view-support
labels:
- validation
- critical-path
remote_ids: {}
created: '2026-05-13T17:30:00+00:00'
updated: '2026-05-16T19:14:09.779972+00:00'
assignee: shanewilkins
estimated_hours: 5.0
due_date: null
depends_on:
- 3c7a2e1f
blocks:
- a1d9f4c6
actual_start_date: '2026-05-16T19:14:09.591584+00:00'
actual_end_date: null
progress_percentage: 0.0
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: null
comments: []
github_issue: null
---

## Add strict render-intent validation in compile/validate pipeline

Extend the IR schema and validation logic to enforce render-intent structure and reject malformed metadata keys before rendering.

## Why

Currently, malformed `.render` intent keys in process metadata flow directly to the renderer with no validation. Means typos, unknown diagram types, or invalid view names are only caught (if at all) at render time. Must add compile-time validation to enable source-first design.

## Acceptance Criteria

- [ ] Extend [schema/flo_ir.json](../../../schema/flo_ir.json) with typed render-intent subtree (diagram, views, layout hints, etc. per render_intent_schema.md)
- [ ] Add validator rule in [src/flo/compiler/ir/validate.py](../../../src/flo/compiler/ir/validate.py) to validate process.metadata.render against schema
- [ ] Write golden-file tests asserting validation errors for malformed intent (bad diagram type, invalid view name, missing required fields)
- [ ] Verify all existing valid test fixtures still pass validation
- [ ] Document render-intent schema in human-readable format adjacent to validation logic

## Implementation Notes

- Reference render-intent schema from [docs/design/render_intent_schema.md](../../../docs/design/render_intent_schema.md) for structure
- Add helper function `validate_render_intent(metadata: dict) -> ValidationError | None`
- Update `ensure_schema_aligned()` in validate.py to call new render-intent validator
- Consider validator message quality for common errors (unknown diagram type, duplicate view names)

## References

- Audit finding #1 (No Render Intent Validation)
- [docs/design/render_intent_schema.md](../../../docs/design/render_intent_schema.md) - design requirements
- [src/flo/compiler/ir/validate.py#L563](../../../src/flo/compiler/ir/validate.py#L563) - schema validation entry point
