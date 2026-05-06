---
id: 7305f218
title: Extract a framework-agnostic CLI parse and dispatch contract
headline: ''
priority: medium
status: todo
archived: false
issue_type: other
milestone: codebase-cleanup
labels: []
remote_ids: {}
created: '2026-05-06T23:35:37.830572+00:00'
updated: '2026-05-06T23:35:37.830574+00:00'
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

CLI behavior is still shaped heavily by Click wiring and console entrypoint mechanics, which makes argument behavior harder to test in isolation.

## Why
A small framework-agnostic parse/dispatch seam would make the CLI easier to test and easier to evolve without monkeypatch-heavy tests.

## Acceptance Criteria
- CLI parsing or dispatch has a testable seam independent of Click decorator wiring.
- Console entry tests rely less on `sys.argv` patching and internal monkeypatching.
- User-visible CLI behavior remains unchanged.
- The refactor reduces duplication between Click commands and console entry code.
