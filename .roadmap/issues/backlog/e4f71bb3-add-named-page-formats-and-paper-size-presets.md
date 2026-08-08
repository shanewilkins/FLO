---
id: e4f71bb3
title: Add named page formats and paper size presets
headline: ''
priority: high
status: closed
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels: []
remote_ids: {}
created: '2026-05-06T23:01:35.359234+00:00'
updated: '2026-05-10T00:00:00+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 07cb2436
blocks: []
actual_start_date: '2026-05-10T00:00:00+00:00'
actual_end_date: '2026-05-10T00:00:00+00:00'
progress_percentage: 100.0
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: '2026-05-10T00:00:00+00:00'
comments: []
github_issue: null
---

Support named publication page formats and paper-size presets in the shared publication planner.

Why

The shared publication model now carries page bounds and margins, but there is no tracked issue for resolving those bounds from named page formats such as Letter, A4, Legal, or Tabloid. Without explicit presets, publication sizing will remain ad hoc and profile defaults will be harder to reason about.

Acceptance Criteria

- Shared publication planning supports named page-size presets such as Letter and A4.
- Presets can define width, height, and default margins.
- Output profiles can select sensible default page formats without hardcoding renderer-specific geometry.
- Unknown or unsupported page-size names fail predictably.
- Documentation covers supported formats and extension rules.
