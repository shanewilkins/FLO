---
id: 10da2d9d
title: Add optional legend and caption support
headline: Allow SPPM maps to carry a legend or caption when notation needs explanation.
priority: high
status: closed
archived: false
issue_type: feature
milestone: sppm-semantic-completeness
labels: []
remote_ids: {}
created: '2026-05-05T17:17:33.940884+00:00'
updated: '2026-05-10T00:00:00+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- a3e631a8
blocks: []
actual_start_date: '2026-05-10T00:00:00+00:00'
actual_end_date: '2026-05-10T00:00:00+00:00'
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

# Add optional legend and caption support

Support optional legends and captions when non-default notation or explanatory callouts need to accompany an SPPM diagram.

## Why

Some published maps need a small legend or caption to explain notation choices, unusual symbols, or contextual assumptions. That support should be first-class instead of requiring manual post-layout edits.

## Acceptance Criteria

- SPPM output can include an optional legend, caption, or both.
- Omission preserves current rendering with no extra visual clutter.
- Legend and caption placement works with header and footer bands.
- The mechanism supports explanatory content for non-default notation.

## Notes

If legend or caption placement becomes obviously reusable beyond SPPM, the placement primitive can later migrate into shared renderer infrastructure.
