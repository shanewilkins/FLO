---
id: f096c888
title: Schema-aligned IR JSON export
headline: Make compiled JSON conform to schema/flo_ir.json and become the stable export shape.
priority: high
status: closed
archived: false
issue_type: feature
milestone: v0-1-core-completion
labels: []
remote_ids: {}
created: '2026-05-05T17:16:35.110835+00:00'
updated: '2026-05-12T17:22:37+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on: []
blocks: []
actual_start_date: null
actual_end_date: '2026-05-12T17:22:37+00:00'
progress_percentage: null
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: '2026-05-12T17:22:37+00:00'
comments: []
github_issue: null
---

# Schema-aligned IR JSON export

Implement schema-shaped IR export so compiled JSON validates against `schema/flo_ir.json` and becomes the canonical serialization target.

## Why

The current compiler emits the in-memory IR dataclass shape, but the roadmap for v0.1 calls for a canonical JSON export that matches the published schema. Until those shapes align, schema validation remains partially broken and downstream tools lack a stable serialization contract.

## Acceptance Criteria

- `flo compile <file>` emits JSON that validates against `schema/flo_ir.json`.
- The export shape is treated as the canonical serialized representation of compiled IR.
- Serializer and deserializer coverage exercise the schema-aligned structure.
- CI schema validation passes against representative example flows.

## Notes

This issue should use the current `.roadmap` milestone scope for `v0-1-core-completion` as the planning source of truth.
