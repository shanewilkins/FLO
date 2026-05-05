---
id: 6a61c515
title: Add step classification summaries
headline: Summarize step classifications and counts for analysis-oriented reporting.
priority: medium
status: todo
archived: false
issue_type: feature
milestone: v0-2-static-analytics
labels: []
remote_ids: {}
created: '2026-05-05T18:56:57.209859+00:00'
updated: '2026-05-05T18:56:57.209861+00:00'
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

# Add step classification summaries

Summarize step classifications and counts for analysis-oriented reporting.

## Why

Classification summaries make the analytics layer more interpretable by showing the composition of a process rather than only edge- or path-level metrics.

## Acceptance Criteria

- Analysis can summarize step classifications and counts from the model.
- Output is available in a form suitable for diagnostics or reporting.
- Tests cover representative mixes of step types.

## Notes

Keep the summary model reusable across future export or reporting formats.
