---
id: '10085780'
title: Improve CLI diagnostics and render UX
headline: Close the remaining v0.1 CLI usability gaps for render workflows and diagnostics.
priority: medium
status: todo
archived: false
issue_type: feature
milestone: v0-1-core-completion
labels: []
remote_ids: {}
created: '2026-05-05T17:17:30.247185+00:00'
updated: '2026-05-05T17:17:30.247188+00:00'
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

# Improve CLI diagnostics and render UX

Upgrade CLI diagnostics, render command ergonomics, and user-facing error messages to close remaining v0.1 UX gaps.

## Why

The core CLI exists, but the roadmap still calls for richer diagnostics and a more complete rendering UX. Improving the command surface now reduces friction across validation, compile, and render workflows.

## Acceptance Criteria

- Error output is actionable and points users to the failing file or step.
- Render commands expose the remaining v0.1 style options cleanly.
- CLI behavior is covered by focused integration tests.
- User-facing diagnostics stay consistent with the documented CLI error contract.

## Notes

Favor thin CLI wrappers over business logic in Click handlers, consistent with the current architecture.
