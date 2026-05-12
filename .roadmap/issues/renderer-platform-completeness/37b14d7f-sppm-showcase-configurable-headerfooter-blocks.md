---
id: 37b14d7f
title: 'SPPM showcase: configurable header/footer blocks'
headline: Add explicit header and footer blocks for SPPM publication output, with
  clean CLI control over visib
priority: high
status: closed
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels:
- sppm,renderer,cli
remote_ids: {}
created: '2026-05-11T17:22:28.119390+00:00'
updated: '2026-05-12T13:19:55.409718+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 63da7b5d
blocks: []
actual_start_date: '2026-05-12T13:14:14.852135+00:00'
actual_end_date: null
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

Add explicit header and footer blocks for SPPM publication output, with clean CLI control over visibility.\n\nScope\n- Render a header block (title/subtitle/context) and footer block (metrics/notes) for showcase outputs.\n- Add CLI flags to suppress each independently: --no-header and --no-footer.\n- Preserve backward-compatible defaults for existing flows.\n\nAcceptance Criteria\n- Header and footer appear by default in SPPM showcase output.\n- --no-header hides only the header; --no-footer hides only the footer.\n- Integration tests verify flag behavior and output stability.\n- Option wiring follows shared CLI/schema contracts (see dependency).
