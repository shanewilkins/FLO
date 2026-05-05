---
id: 717992b5
title: Add user-definable color themes
headline: Let users define themes in config instead of relying only on hardcoded theme tables.
priority: medium
status: todo
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels: []
remote_ids: {}
created: '2026-05-05T18:57:02.772083+00:00'
updated: '2026-05-05T18:57:02.772085+00:00'
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

# Add user-definable color themes

Load user-defined themes from config files instead of limiting theme selection to hardcoded defaults.

## Why

Theme customization is a recurring publishing need and should not require code edits. Even though this started from SPPM needs, the loading and validation path belongs in reusable renderer infrastructure.

## Acceptance Criteria

- Users can define custom themes in a config file.
- The renderer can load and validate custom theme definitions.
- CLI theme selection can target those custom themes.
- Fallback behavior remains clear when a theme is missing or invalid.

## Notes

Keep the theme loader reusable so other renderers can adopt it later.
