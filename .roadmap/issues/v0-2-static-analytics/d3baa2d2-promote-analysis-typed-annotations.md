---
id: d3baa2d2
title: Promote analysis typed annotations
headline: Support analysis-oriented typed annotations such as SLA targets and value class.
priority: medium
status: todo
archived: false
issue_type: feature
milestone: v0-2-static-analytics
labels: []
remote_ids: {}
created: '2026-05-05T18:56:57.704327+00:00'
updated: '2026-05-05T18:56:57.704329+00:00'
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

# Promote analysis typed annotations

Support analysis-oriented annotations such as `sla_target_seconds` and `value_class` in the modeled outputs.

## Why

The v0.2 analytics outline calls out optional typed annotations that enrich static analysis. Capturing them explicitly keeps the analysis layer grounded in typed metadata rather than ad hoc fields.

## Acceptance Criteria

- Analysis-oriented typed annotations are supported in the relevant model or export layer.
- Validation and typing rules are clear for supported annotations.
- Tests cover parsing and consumption of those annotations where applicable.

## Notes

Prefer typed metadata and schema-backed fields over renderer-specific special cases.
