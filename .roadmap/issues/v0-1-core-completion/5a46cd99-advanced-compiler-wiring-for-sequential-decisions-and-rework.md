---
id: 5a46cd99
title: Advanced compiler wiring for sequential decisions and rework
headline: Complete the remaining compiler rules for sequencing, decisions, and rework.
priority: high
status: todo
archived: false
issue_type: feature
milestone: v0-1-core-completion
labels: []
remote_ids: {}
created: '2026-05-05T17:17:29.068024+00:00'
updated: '2026-05-05T17:17:29.068031+00:00'
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

# Advanced compiler wiring for sequential decisions and rework

Implement the remaining compiler rules for sequential edge inference, decision outcome wiring, and rework heuristics so compiled models round-trip cleanly into canonical IR.

## Why

The v0.1 roadmap still calls out advanced compilation rules as unfinished. Until those rules are explicit and tested, modeled flows remain under-specified and the canonical IR does not fully capture author intent.

## Acceptance Criteria

- Sequential edge inference is deterministic and documented.
- Decision outcomes are wired into canonical IR without ambiguous fallthrough behavior.
- Rework heuristics are implemented or replaced with explicit compilation rules.
- Representative examples and tests cover the remaining compilation branches.

## Notes

Use the current `v0-1-core-completion` milestone scope in `.roadmap` as the planning source of truth for this work.
