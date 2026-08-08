---
id: 653b0e4c
title: Add analytics footer band
headline: Add a bottom summary band for analytics and explanatory totals in SPPM output.
priority: critical
status: closed
archived: false
issue_type: feature
milestone: sppm-semantic-completeness
labels: []
remote_ids: {}
created: '2026-05-05T17:17:32.676748+00:00'
updated: '2026-05-06T23:21:05.922347+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- a3e631a8
blocks: []
actual_start_date: '2026-05-06T23:14:47.214771+00:00'
actual_end_date: '2026-05-06T23:21:05.810543+00:00'
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

# Add analytics footer band

Render an optional analytics or summary band at the bottom of SPPM outputs for totals, key metrics, and explanatory context.

## Why

SPPM maps often need a compact summary region for totals, headline metrics, or short interpretive notes. That is part of making the output publication-ready without relying on external layout tools.

## Acceptance Criteria

- SPPM output can include an optional footer band for totals or analytics.
- Footer content is driven by model metadata or render-time inputs.
- The footer integrates cleanly with the rest of the map and does not obscure flow content.
- The feature is optional and omission preserves existing rendering behavior.

## Notes

Keep analytic content flexible enough to support both handcrafted summary text and future computed metrics.
