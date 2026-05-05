---
id: ce07a4e0
title: Add subprocess notation and detail-map references
headline: Support subprocess markers and detail-map references in native SPPM output.
priority: high
status: todo
archived: false
issue_type: feature
milestone: sppm-semantic-completeness
labels: []
remote_ids: {}
created: '2026-05-05T17:17:31.412873+00:00'
updated: '2026-05-05T17:17:31.412875+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on: []
blocks: []
actual_start_date: null
actual_end_date: null
progress_percentage: null
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: null
comments: []
github_issue: null
---

# Add subprocess notation and detail-map references

Extend SPPM to render subprocess markers and detail-map references so nested process views can be represented directly in the notation.

## Why

Subprocess notation is one of the clearest remaining semantic gaps in SPPM support. Without it, FLO can render local process detail but cannot express the notation needed to point readers to a deeper map.

## Acceptance Criteria

- FLO metadata can mark a step as a subprocess or attach a detail-map reference.
- SPPM output renders a distinct subprocess marker or border treatment.
- Detail-map references appear in labels or callouts without manual post-editing.
- Validation catches obviously broken or circular detail-map references where feasible.

## Notes

Keep the semantic marker in the model layer; hyperlinking or cross-document behavior can be handled separately if needed.
