---
id: a3e631a8
title: Add reusable header footer document bands
headline: Create shared document-band primitives for titles, headers, footers, and
  metadata blocks.
priority: high
status: todo
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels: []
remote_ids: {}
created: '2026-05-05T17:17:36.230631+00:00'
updated: '2026-05-05T19:42:34.366047+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 07cb2436
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

# Add reusable header footer document bands

Create shared primitives for title bands, headers, footers, and document metadata regions that multiple renderers can adopt.

## Why

SPPM needs title and footer regions now, but those concerns are broader than SPPM alone. Shared document bands keep layout infrastructure reusable while allowing renderers to control the semantic content they place into those regions.

## Acceptance Criteria

- Shared document-band primitives exist for top and bottom regions.
- Renderers can place content into those bands without hardcoding SPPM-specific assumptions.
- The primitives cooperate with page bounds and future overflow behavior.
- Existing renderers remain functional when bands are unused.

## Notes

This issue is about layout plumbing, not the semantic content of any specific band.
