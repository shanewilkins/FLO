---
id: f620fe69
title: Introduce shared typed metadata contracts for renderer-facing fields
headline: ''
priority: medium
status: todo
archived: false
issue_type: other
milestone: codebase-cleanup
labels: []
remote_ids: {}
created: '2026-05-06T23:35:37.017723+00:00'
updated: '2026-05-06T23:35:37.017725+00:00'
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

Renderer-facing metadata such as process headers, subprocess detail-map references, and footer/header extension fields currently rely on scattered string-key conventions.

## Why
This is workable in pre-release code, but it increases the risk of typo-driven drift and inconsistent behavior as more renderer features depend on metadata.

## Acceptance Criteria
- Shared metadata keys used across render/validation are centralized behind typed constants, helpers, or small domain models.
- Header/footer/process metadata contracts are easier to discover from one place.
- At least one current multi-key fallback path is simplified through the new contract.
- Tests protect against silent key drift.
