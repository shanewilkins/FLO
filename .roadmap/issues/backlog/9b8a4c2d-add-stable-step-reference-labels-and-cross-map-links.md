---
id: 9b8a4c2d
title: Add stable step reference labels and cross-map links
headline: Surface visible step references derived from node ids so SPPM pages and
  child maps can cross-reference reliably.
priority: critical
status: closed
archived: false
issue_type: feature
milestone: sppm-semantic-completeness
labels: []
remote_ids: {}
created: '2026-05-06T00:00:00+00:00'
updated: '2026-05-06T21:20:03.593767+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- ce07a4e0
blocks:
- 47c38a4e
actual_start_date: '2026-05-06T20:40:37.052597+00:00'
actual_end_date: '2026-05-06T21:20:03.509210+00:00'
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

## Add stable step reference labels and cross-map links

Expose visible stable step references derived from `node_id` so parent maps, child maps, continuation markers, and diagnostics can all refer to the same published steps unambiguously.

## Why

Long-form static publication breaks down quickly if readers cannot identify a step consistently across pages and child maps. Human-readable names are not stable enough on their own.

## Acceptance Criteria

- Published SPPM nodes show a stable visible reference token derived from `node_id`.
- Continuation anchors and child-map references can include those tokens.
- References remain stable across re-renders for the same model and options.
- The labels improve navigation without overwhelming the primary step name.

## Notes

This is a publication and notation issue, not just a testing aid.
